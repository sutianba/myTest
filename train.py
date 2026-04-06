# Ultralytics 🚀 AGPL-3.0 许可证 - https://ultralytics.com/license
"""
在自定义数据集上训练YOLOv5模型。模型和数据集会自动从最新的YOLOv5发布版本下载。.

使用方法 - 单GPU训练：
    $ python train.py --data coco128.yaml --weights yolov5s.pt --img 640  # 从预训练模型开始（推荐）
    $ python train.py --data coco128.yaml --weights '' --cfg yolov5s.yaml --img 640  # 从零开始训练

使用方法 - 多GPU DDP训练：
    $ python -m torch.distributed.run --nproc_per_node 4 --master_port 1 train.py --data coco128.yaml --weights yolov5s.pt --img 640 --device 0,1,2,3

模型：     https://github.com/ultralytics/yolov5/tree/master/models
数据集：   https://github.com/ultralytics/yolov5/tree/master/data
教程：     https://docs.ultralytics.com/yolov5/tutorials/train_custom_data
"""

import argparse
import math
import os
import random
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path

try:
    import comet_ml  # 如果已安装，必须在torch之前导入
except ImportError:
    comet_ml = None

import numpy as np
import torch
import torch.distributed as dist
import torch.nn as nn
import yaml
from torch.optim import lr_scheduler
from tqdm import tqdm

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5根目录
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # 将ROOT添加到PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # 相对路径

from ultralytics.utils.patches import torch_load

import val as validate  # 用于epoch结束时的mAP计算
from models.experimental import attempt_load
from models.yolo import Model
from utils.autoanchor import check_anchors
from utils.autobatch import check_train_batch_size
from utils.callbacks import Callbacks
from utils.dataloaders import create_dataloader
from utils.downloads import attempt_download, is_url
from utils.general import (
    LOGGER,
    TQDM_BAR_FORMAT,
    check_amp,
    check_dataset,
    check_file,
    check_git_info,
    check_git_status,
    check_img_size,
    check_requirements,
    check_suffix,
    check_yaml,
    colorstr,
    get_latest_run,
    increment_path,
    init_seeds,
    intersect_dicts,
    labels_to_class_weights,
    labels_to_image_weights,
    methods,
    one_cycle,
    print_args,
    print_mutation,
    strip_optimizer,
    yaml_save,
)
from utils.loggers import LOGGERS, Loggers
from utils.loggers.comet.comet_utils import check_comet_resume
from utils.loss import ComputeLoss
from utils.plots import plot_evolve
from utils.torch_utils import (
    EarlyStopping,
    ModelEMA,
    de_parallel,
    select_device,
    smart_DDP,
    smart_optimizer,
    smart_resume,
    torch_distributed_zero_first,
)

LOCAL_RANK = int(os.getenv("LOCAL_RANK", -1))  # https://pytorch.org/docs/stable/elastic/run.html
RANK = int(os.getenv("RANK", -1))
WORLD_SIZE = int(os.getenv("WORLD_SIZE", 1))
GIT_INFO = check_git_info()


def train(hyp, opt, device, callbacks):
    """在自定义数据集上使用指定的超参数、选项和设备训练YOLOv5模型，管理数据集、 模型架构、损失计算和优化器步骤。.

    参数：
        hyp (str | dict)：超参数YAML文件的路径或超参数字典。
        opt (argparse.Namespace)：包含训练选项的解析后的命令行参数。
        device (torch.device)：训练发生的设备，例如'cuda'或'cpu'。
        callbacks (Callbacks)：各种训练事件的回调函数。

    返回值：
        None

    示例：
        单GPU训练：
        ```bash
        $ python train.py --data coco128.yaml --weights yolov5s.pt --img 640  # 从预训练模型开始（推荐）
        $ python train.py --data coco128.yaml --weights '' --cfg yolov5s.yaml --img 640  # 从零开始训练
        ```

        多GPU DDP训练：
        ```bash
        $ python -m torch.distributed.run --nproc_per_node 4 --master_port 1 train.py --data coco128.yaml --weights
        yolov5s.pt --img 640 --device 0,1,2,3
        ```

        更多使用详情，请参考：
        - 模型：https://github.com/ultralytics/yolov5/tree/master/models
        - 数据集：https://github.com/ultralytics/yolov5/tree/master/data
        - 教程：https://docs.ultralytics.com/yolov5/tutorials/train_custom_data

    注意：
        模型和数据集会自动从最新的YOLOv5发布版本下载。
    """
    save_dir, epochs, batch_size, weights, single_cls, evolve, data, cfg, resume, noval, _nosave, workers, freeze = (
        Path(opt.save_dir),
        opt.epochs,
        opt.batch_size,
        opt.weights,
        opt.single_cls,
        opt.evolve,
        opt.data,
        opt.cfg,
        opt.resume,
        opt.noval,
        opt.nosave,
        opt.workers,
        opt.freeze,
    )
    callbacks.run("on_pretrain_routine_start")

    # 目录
    w = save_dir / "weights"  # 权重目录
    (w.parent if evolve else w).mkdir(parents=True, exist_ok=True)  # 创建目录
    last, best = w / "last.pt", w / "best.pt"

    # 超参数
    if isinstance(hyp, str):
        with open(hyp, errors="ignore") as f:
            hyp = yaml.safe_load(f)  # 加载超参数字典
    LOGGER.info(colorstr("超参数: ") + ", ".join(f"{k}={v}" for k, v in hyp.items()))
    opt.hyp = hyp.copy()  # 用于将超参数保存到检查点

    # 保存运行设置
    if not evolve:
        yaml_save(save_dir / "hyp.yaml", hyp)
        yaml_save(save_dir / "opt.yaml", vars(opt))

    # 日志记录器
    data_dict = None
    if RANK in {-1, 0}:
        include_loggers = list(LOGGERS)
        if getattr(opt, "ndjson_console", False):
            include_loggers.append("ndjson_console")
        if getattr(opt, "ndjson_file", False):
            include_loggers.append("ndjson_file")

        loggers = Loggers(
            save_dir=save_dir,
            weights=weights,
            opt=opt,
            hyp=hyp,
            logger=LOGGER,
            include=tuple(include_loggers),
        )

        # 注册操作
        for k in methods(loggers):
            callbacks.register_action(k, callback=getattr(loggers, k))

        # 处理自定义数据集制品链接
        data_dict = loggers.remote_dataset
        if resume:  # 如果从远程制品恢复运行
            weights, epochs, hyp, batch_size = opt.weights, opt.epochs, opt.hyp, opt.batch_size

    # 配置
    plots = not evolve and not opt.noplots  # 创建图表
    cuda = device.type != "cpu"
    init_seeds(opt.seed + 1 + RANK, deterministic=True)
    with torch_distributed_zero_first(LOCAL_RANK):
        data_dict = data_dict or check_dataset(data)  # 检查是否为None
    train_path, val_path = data_dict["train"], data_dict["val"]
    nc = 1 if single_cls else int(data_dict["nc"])  # 类别数量
    names = {0: "item"} if single_cls and len(data_dict["names"]) != 1 else data_dict["names"]  # 类别名称
    is_coco = isinstance(val_path, str) and val_path.endswith("coco/val2017.txt")  # COCO数据集

    # 模型
    check_suffix(weights, ".pt")  # 检查权重后缀
    if pretrained:
        with torch_distributed_zero_first(LOCAL_RANK):
            weights = attempt_download(weights)  # 如果本地未找到则下载
        ckpt = torch_load(weights, map_location="cpu")  # 加载检查点到CPU以避免CUDA内存泄漏
        model = Model(cfg or ckpt["model"].yaml, ch=3, nc=nc, anchors=hyp.get("anchors")).to(device)  # 创建模型
        exclude = ["anchor"] if (cfg or hyp.get("anchors")) and not resume else []  # 排除的键
        csd = ckpt["model"].float().state_dict()  # 检查点状态字典，FP32格式
        csd = intersect_dicts(csd, model.state_dict(), exclude=exclude)  # 交集
        model.load_state_dict(csd, strict=False)  # 加载
        LOGGER.info(f"从 {weights} 转移了 {len(csd)}/{len(model.state_dict())} 个项目")  # 报告
    else:
        model = Model(cfg, ch=3, nc=nc, anchors=hyp.get("anchors")).to(device)  # create
    amp = check_amp(model)  # 检查自动混合精度

    # 冻结
    freeze = [f"model.{x}." for x in (freeze if len(freeze) > 1 else range(freeze[0]))]  # 要冻结的层
    for k, v in model.named_parameters():
        v.requires_grad = True  # 训练所有层
        # v.register_hook(lambda x: torch.nan_to_num(x))  # NaN转0（注释掉以避免训练结果不稳定）
        if any(x in k for x in freeze):
            LOGGER.info(f"冻结 {k}")
            v.requires_grad = False

    # 图像大小
    gs = max(int(model.stride.max()), 32)  # 网格大小（最大步长）
    imgsz = check_img_size(opt.imgsz, gs, floor=gs * 2)  # 验证imgsz是gs的倍数

    # 批次大小
    if RANK == -1 and batch_size == -1:  # 仅单GPU，估计最佳批次大小
        batch_size = check_train_batch_size(model, imgsz, amp)
        loggers.on_params_update({"batch_size": batch_size})

    # 优化器
    nbs = 64  # 名义批次大小
    accumulate = max(round(nbs / batch_size), 1)  # 优化前累积损失
    hyp["weight_decay"] *= batch_size * accumulate / nbs  # 缩放权重衰减
    optimizer = smart_optimizer(model, opt.optimizer, hyp["lr0"], hyp["momentum"], hyp["weight_decay"])

    # 学习率调度器
    if opt.cos_lr:
        lf = one_cycle(1, hyp["lrf"], epochs)  # 余弦 1->hyp['lrf']
    else:

        def lf(x):
            """线性学习率调度函数，根据 epoch 比例计算衰减。."""
            return (1 - x / epochs) * (1.0 - hyp["lrf"]) + hyp["lrf"]  # 线性

    scheduler = lr_scheduler.LambdaLR(optimizer, lr_lambda=lf)  # plot_lr_scheduler(optimizer, scheduler, epochs)

    # EMA
    ema = ModelEMA(model) if RANK in {-1, 0} else None

    # 恢复训练
    best_fitness, start_epoch = 0.0, 0
    if pretrained:
        if resume:
            best_fitness, start_epoch, epochs = smart_resume(ckpt, optimizer, ema, weights, epochs, resume)
        del ckpt, csd

    # DP 模式
    if cuda and RANK == -1 and torch.cuda.device_count() > 1:
        LOGGER.warning(
            "警告 ⚠️ 不建议使用 DP，请使用 torch.distributed.run 以获得最佳 DDP 多 GPU 结果。\n"
            "请参阅多 GPU 教程：https://docs.ultralytics.com/yolov5/tutorials/multi_gpu_training 开始。"
        )
        model = torch.nn.DataParallel(model)

    # SyncBatchNorm
    if opt.sync_bn and cuda and RANK != -1:
        model = torch.nn.SyncBatchNorm.convert_sync_batchnorm(model).to(device)
        LOGGER.info("使用 SyncBatchNorm()")

    # 训练数据加载器
    train_loader, dataset = create_dataloader(
        train_path,
        imgsz,
        batch_size // WORLD_SIZE,
        gs,
        single_cls,
        hyp=hyp,
        augment=True,
        cache=None if opt.cache == "val" else opt.cache,
        rect=opt.rect,
        rank=LOCAL_RANK,
        workers=workers,
        image_weights=opt.image_weights,
        quad=opt.quad,
        prefix=colorstr("train: "),
        shuffle=True,
        seed=opt.seed,
    )
    labels = np.concatenate(dataset.labels, 0)
    mlc = int(labels[:, 0].max())  # 最大标签类别
    assert mlc < nc, f"标签类别 {mlc} 超过 {data} 中的 nc={nc}。可能的类别标签为 0-{nc - 1}"

    # 进程 0
    if RANK in {-1, 0}:
        val_loader = create_dataloader(
            val_path,
            imgsz,
            batch_size // WORLD_SIZE * 2,
            gs,
            single_cls,
            hyp=hyp,
            cache=None if noval else opt.cache,
            rect=True,
            rank=-1,
            workers=workers * 2,
            pad=0.5,
            prefix=colorstr("val: "),
        )[0]

        if not resume:
            if not opt.noautoanchor:
                check_anchors(dataset, model=model, thr=hyp["anchor_t"], imgsz=imgsz)  # 运行 AutoAnchor
            model.half().float()  # 预降低锚点精度

        callbacks.run("on_pretrain_routine_end", labels, names)

    # DDP 模式
    if cuda and RANK != -1:
        model = smart_DDP(model)

    # 模型属性
    nl = de_parallel(model).model[-1].nl  # 检测层数量（用于缩放超参数）
    hyp["box"] *= 3 / nl  # 缩放到层
    hyp["cls"] *= nc / 80 * 3 / nl  # 缩放到类别和层
    hyp["obj"] *= (imgsz / 640) ** 2 * 3 / nl  # 缩放到图像大小和层
    hyp["label_smoothing"] = opt.label_smoothing
    model.nc = nc  # 将类别数量附加到模型
    model.hyp = hyp  # 将超参数附加到模型
    model.class_weights = labels_to_class_weights(dataset.labels, nc).to(device) * nc  # 附加类别权重
    model.names = names

    # 开始训练
    t0 = time.time()
    nb = len(train_loader)  # 批次数量
    nw = max(round(hyp["warmup_epochs"] * nb), 100)  # 预热迭代次数，最大（3 个 epoch，100 次迭代）
    # nw = min(nw, (epochs - start_epoch) / 2 * nb)  # 将预热限制在训练的一半以内
    maps = np.zeros(nc)  # 每个类别的 mAP
    results = (0, 0, 0, 0, 0, 0, 0)  # P, R, mAP@.5, mAP@.5-.95, val_loss(box, obj, cls)
    scheduler.last_epoch = start_epoch - 1  # 不要移动
    torch.cuda.amp.GradScaler(enabled=amp)
    _stopper, _stop = EarlyStopping(patience=opt.patience), False
    compute_loss = ComputeLoss(model)  # 初始化损失类
    callbacks.run("on_train_start")
    LOGGER.info(
        f"图像大小 {imgsz} 训练，{imgsz} 验证\n"
        f"使用 {train_loader.num_workers * WORLD_SIZE} 个数据加载器工作线程\n"
        f"记录结果到 {colorstr('bold', save_dir)}\n"
        f"开始训练 {epochs} 个 epoch..."
    )
    for epoch in range(start_epoch, epochs):  # epoch ------------------------------------------------------------------
        callbacks.run("on_train_epoch_start")
        model.train()

        # 更新图像权重（可选，仅单 GPU）
        if opt.image_weights:
            cw = model.class_weights.cpu().numpy() * (1 - maps) ** 2 / nc  # 类别权重
            iw = labels_to_image_weights(dataset.labels, nc=nc, class_weights=cw)  # 图像权重
            dataset.indices = random.choices(range(dataset.n), weights=iw, k=dataset.n)  # 随机加权索引

        # 更新马赛克边框（可选）
        # b = int(random.uniform(0.25 * imgsz, 0.75 * imgsz + gs) // gs * gs)
        # dataset.mosaic_border = [b - imgsz, -b]  # 高度，宽度边框

        mloss = torch.zeros(3, device=device)  # 平均损失
        if RANK != -1:
            train_loader.sampler.set_epoch(epoch)
        pbar = enumerate(train_loader)
        LOGGER.info(("\n" + "%11s" * 7) % ("Epoch", "GPU_mem", "box_loss", "obj_loss", "cls_loss", "Instances", "Size"))
        if RANK in {-1, 0}:
            pbar = tqdm(pbar, total=nb, bar_format=TQDM_BAR_FORMAT)  # 进度条
        optimizer.zero_grad()
        for i, (imgs, targets, paths, _) in pbar:  # batch -------------------------------------------------------------
            callbacks.run("on_train_batch_start")
            ni = i + nb * epoch  # 自训练开始以来的集成批次数量
            imgs = imgs.to(device, non_blocking=True).float() / 255  # uint8 转 float32，0-255 转 0.0-1.0

            # 预热
            if ni <= nw:
                xi = [0, nw]  # x 插值
                # compute_loss.gr = np.interp(ni, xi, [0.0, 1.0])  # iou 损失比例 (obj_loss = 1.0 或 iou)
                accumulate = max(1, np.interp(ni, xi, [1, nbs / batch_size]).round())
                for j, x in enumerate(optimizer.param_groups):
                    # 偏置学习率从 0.1 降至 lr0，其他学习率从 0.0 升至 lr0
                    x["lr"] = np.interp(ni, xi, [hyp["warmup_bias_lr"] if j == 0 else 0.0, x["initial_lr"] * lf(epoch)])
                    if "momentum" in x:
                        x["momentum"] = np.interp(ni, xi, [hyp["warmup_momentum"], hyp["momentum"]])

            # 多尺度
            if opt.multi_scale:
                sz = random.randrange(int(imgsz * 0.5), int(imgsz * 1.5) + gs) // gs * gs  # 大小
                sf = sz / max(imgs.shape[2:])  # 缩放因子
                if sf != 1:
                    [math.ceil(x * sf / gs) * gs for x in imgs.shape[2:]]  # 新形状（拉伸到 gs 倍数）
                    imgs = nn.functional

        # 结束 epoch ----------------------------------------------------------------------------------------------------
    # 结束训练 -----------------------------------------------------------------------------------------------------
    if RANK in {-1, 0}:
        LOGGER.info(f"\n{epoch - start_epoch + 1} 个 epoch 已完成，耗时 {(time.time() - t0) / 3600:.3f} 小时。")
        for f in last, best:
            if f.exists():
                strip_optimizer(f)  # 去除优化器
                if f is best:
                    LOGGER.info(f"\n正在验证 {f}...")
                    results, _, _ = validate.run(
                        data_dict,
                        batch_size=batch_size // WORLD_SIZE * 2,
                        imgsz=imgsz,
                        model=attempt_load(f, device).half(),
                        iou_thres=0.65 if is_coco else 0.60,  # pycocotools 在 iou 0.65 时表现最佳
                        single_cls=single_cls,
                        dataloader=val_loader,
                        save_dir=save_dir,
                        save_json=is_coco,
                        verbose=True,
                        plots=plots,
                        callbacks=callbacks,
                        compute_loss=compute_loss,
                    )  # 验证最佳模型并绘图
                    if is_coco:
                        callbacks.run("on_fit_epoch_end", list(mloss) + list(results) + lr, epoch, best_fitness, fi)

        callbacks.run("on_train_end", last, best, epoch, results)
    torch.cuda.empty_cache()
    return results


def parse_opt(known=False):
    """解析YOLOv5训练、验证和测试的命令行参数。.

    参数：
        known (bool, 可选)：如果为True，仅解析已知参数，忽略未知参数。默认值为False。

    返回：
        (argparse.Namespace)：解析后的命令行参数，包含YOLOv5执行的选项。

    示例：
        ```python
        from ultralytics.yolo import parse_opt
        opt = parse_opt()
        print(opt)
        ```

    链接：
        - 模型：https://github.com/ultralytics/yolov5/tree/master/models
        - 数据集：https://github.com/ultralytics/yolov5/tree/master/data
        - 教程：https://docs.ultralytics.com/yolov5/tutorials/train_custom_data
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", type=str, default=ROOT / "yolov5s.pt", help="initial weights path")
    parser.add_argument("--cfg", type=str, default="", help="model.yaml path")
    parser.add_argument("--data", type=str, default=ROOT / "data/coco128.yaml", help="dataset.yaml path")
    parser.add_argument("--hyp", type=str, default=ROOT / "data/hyps/hyp.scratch-low.yaml", help="hyperparameters path")
    parser.add_argument("--epochs", type=int, default=100, help="total training epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="total batch size for all GPUs, -1 for autobatch")
    parser.add_argument("--imgsz", "--img", "--img-size", type=int, default=640, help="train, val image size (pixels)")
    parser.add_argument("--rect", action="store_true", help="rectangular training")
    parser.add_argument("--resume", nargs="?", const=True, default=False, help="resume most recent training")
    parser.add_argument("--nosave", action="store_true", help="only save final checkpoint")
    parser.add_argument("--noval", action="store_true", help="only validate final epoch")
    parser.add_argument("--noautoanchor", action="store_true", help="disable AutoAnchor")
    parser.add_argument("--noplots", action="store_true", help="save no plot files")
    parser.add_argument("--evolve", type=int, nargs="?", const=300, help="evolve hyperparameters for x generations")
    parser.add_argument(
        "--evolve_population", type=str, default=ROOT / "data/hyps", help="location for loading population"
    )
    parser.add_argument("--resume_evolve", type=str, default=None, help="resume evolve from last generation")
    parser.add_argument("--bucket", type=str, default="", help="gsutil bucket")
    parser.add_argument("--cache", type=str, nargs="?", const="ram", help="image --cache ram/disk")
    parser.add_argument("--image-weights", action="store_true", help="use weighted image selection for training")
    parser.add_argument("--device", default="", help="cuda device, i.e. 0 or 0,1,2,3 or cpu")
    parser.add_argument("--multi-scale", action="store_true", help="vary img-size +/- 50%%")
    parser.add_argument("--single-cls", action="store_true", help="train multi-class data as single-class")
    parser.add_argument("--optimizer", type=str, choices=["SGD", "Adam", "AdamW"], default="SGD", help="optimizer")
    parser.add_argument("--sync-bn", action="store_true", help="use SyncBatchNorm, only available in DDP mode")
    parser.add_argument("--workers", type=int, default=8, help="max dataloader workers (per RANK in DDP mode)")
    parser.add_argument("--project", default=ROOT / "runs/train", help="save to project/name")
    parser.add_argument("--name", default="exp", help="save to project/name")
    parser.add_argument("--exist-ok", action="store_true", help="existing project/name ok, do not increment")
    parser.add_argument("--quad", action="store_true", help="quad dataloader")
    parser.add_argument("--cos-lr", action="store_true", help="cosine LR scheduler")
    parser.add_argument("--label-smoothing", type=float, default=0.0, help="Label smoothing epsilon")
    parser.add_argument("--patience", type=int, default=100, help="EarlyStopping patience (epochs without improvement)")
    parser.add_argument("--freeze", nargs="+", type=int, default=[0], help="Freeze layers: backbone=10, first3=0 1 2")
    parser.add_argument("--save-period", type=int, default=-1, help="Save checkpoint every x epochs (disabled if < 1)")
    parser.add_argument("--seed", type=int, default=0, help="Global training seed")
    parser.add_argument("--local_rank", type=int, default=-1, help="Automatic DDP Multi-GPU argument, do not modify")

    # Logger arguments
    parser.add_argument("--entity", default=None, help="Entity")
    parser.add_argument("--upload_dataset", nargs="?", const=True, default=False, help='Upload data, "val" option')
    parser.add_argument("--bbox_interval", type=int, default=-1, help="Set bounding-box image logging interval")
    parser.add_argument("--artifact_alias", type=str, default="latest", help="Version of dataset artifact to use")

    # NDJSON logging
    parser.add_argument("--ndjson-console", action="store_true", help="Log ndjson to console")
    parser.add_argument("--ndjson-file", action="store_true", help="Log ndjson to file")

    return parser.parse_known_args()[0] if known else parser.parse_args()


def main(opt, callbacks=Callbacks()):
    """使用指定选项和可选回调函数运行训练或超参数进化的主入口点。.

    参数：
        opt (argparse.Namespace)：为YOLOv5训练和进化解析的命令行参数。
        callbacks (ultralytics.utils.callbacks.Callbacks, 可选)：用于训练各阶段的回调函数。
            默认为 Callbacks()。

    返回：
        None

    说明：
        详细用法请参考：
        https://github.com/ultralytics/yolov5/tree/master/models
    """
    if RANK in {-1, 0}:
        print_args(vars(opt))
        check_git_status()
        check_requirements(ROOT / "requirements.txt")

    # Resume (from specified or most recent last.pt)
    if opt.resume and not check_comet_resume(opt) and not opt.evolve:
        last = Path(check_file(opt.resume) if isinstance(opt.resume, str) else get_latest_run())
        opt_yaml = last.parent.parent / "opt.yaml"  # train options yaml
        opt_data = opt.data  # original dataset
        if opt_yaml.is_file():
            with open(opt_yaml, errors="ignore") as f:
                d = yaml.safe_load(f)
        else:
            d = torch_load(last, map_location="cpu")["opt"]
        opt = argparse.Namespace(**d)  # replace
        opt.cfg, opt.weights, opt.resume = "", str(last), True  # reinstate
        if is_url(opt_data):
            opt.data = check_file(opt_data)  # avoid HUB resume auth timeout
    else:
        opt.data, opt.cfg, opt.hyp, opt.weights, opt.project = (
            check_file(opt.data),
            check_yaml(opt.cfg),
            check_yaml(opt.hyp),
            str(opt.weights),
            str(opt.project),
        )  # checks
        assert len(opt.cfg) or len(opt.weights), "either --cfg or --weights must be specified"
        if opt.evolve:
            if opt.project == str(ROOT / "runs/train"):  # if default project name, rename to runs/evolve
                opt.project = str(ROOT / "runs/evolve")
            opt.exist_ok, opt.resume = opt.resume, False  # pass resume to exist_ok and disable resume
        if opt.name == "cfg":
            opt.name = Path(opt.cfg).stem  # use model.yaml as name
        opt.save_dir = str(increment_path(Path(opt.project) / opt.name, exist_ok=opt.exist_ok))

    # DDP mode
    device = select_device(opt.device, batch_size=opt.batch_size)
    if LOCAL_RANK != -1:
        msg = "is not compatible with YOLOv5 Multi-GPU DDP training"
        assert not opt.image_weights, f"--image-weights {msg}"
        assert not opt.evolve, f"--evolve {msg}"
        assert opt.batch_size != -1, f"AutoBatch with --batch-size -1 {msg}, please pass a valid --batch-size"
        assert opt.batch_size % WORLD_SIZE == 0, f"--batch-size {opt.batch_size} must be multiple of WORLD_SIZE"
        assert torch.cuda.device_count() > LOCAL_RANK, "insufficient CUDA devices for DDP command"
        torch.cuda.set_device(LOCAL_RANK)
        device = torch.device("cuda", LOCAL_RANK)
        dist.init_process_group(
            backend="nccl" if dist.is_nccl_available() else "gloo", timeout=timedelta(seconds=10800)
        )

    # Train
    if not opt.evolve:
        train(opt.hyp, opt, device, callbacks)

    # 进化超参数（可选）
    else:
        # 超参数进化元数据（包含此超参数是否可进化True-False，下限，上限）
        meta = {
            "lr0": (False, 1e-5, 1e-1),  # 初始学习率 (SGD=1E-2, Adam=1E-3)
            "lrf": (False, 0.01, 1.0),  # 最终OneCycleLR学习率 (lr0 * lrf)
            "momentum": (False, 0.6, 0.98),  # SGD动量/Adam beta1
            "weight_decay": (False, 0.0, 0.001),  # 优化器权重衰减
            "warmup_epochs": (False, 0.0, 5.0),  # 预热轮数（允许小数）
            "warmup_momentum": (False, 0.0, 0.95),  # 预热初始动量
            "warmup_bias_lr": (False, 0.0, 0.2),  # 预热初始偏置学习率
            "box": (False, 0.02, 0.2),  # 边界框损失权重
            "cls": (False, 0.2, 4.0),  # 分类损失权重
            "cls_pw": (False, 0.5, 2.0),  # 分类BCELoss正样本权重
            "obj": (False, 0.2, 4.0),  # 目标损失权重（随像素缩放）
            "obj_pw": (False, 0.5, 2.0),  # 目标BCELoss正样本权重
            "iou_t": (False, 0.1, 0.7),  # IoU训练阈值
            "anchor_t": (False, 2.0, 8.0),  # 锚框倍数阈值
            "anchors": (False, 2.0, 10.0),  # 每个输出网格的锚框数量（0表示忽略）
            "fl_gamma": (False, 0.0, 2.0),  # 焦点损失gamma参数（efficientDet默认gamma=1.5）
            "hsv_h": (True, 0.0, 0.1),  # 图像HSV-色调增强（比例）
            "hsv_s": (True, 0.0, 0.9),  # 图像HSV-饱和度增强（比例）
            "hsv_v": (True, 0.0, 0.9),  # 图像HSV-明度增强（比例）
            "degrees": (True, 0.0, 45.0),  # 图像旋转角度（±度）
            "translate": (True, 0.0, 0.9),  # 图像平移（±比例）
            "scale": (True, 0.0, 0.9),  # 图像缩放（±增益）
            "shear": (True, 0.0, 10.0),  # 图像剪切（±度）
            "perspective": (True, 0.0, 0.001),  # 图像透视变换（±比例），范围0-0.001
            "flipud": (True, 0.0, 1.0),  # 图像上下翻转（概率）
            "fliplr": (True, 0.0, 1.0),  # 图像左右翻转（概率）
            "mosaic": (True, 0.0, 1.0),  # 图像马赛克增强（概率）
            "mixup": (True, 0.0, 1.0),  # 图像混合增强（概率）
            "copy_paste": (True, 0.0, 1.0),  # 分割图复制粘贴增强（概率）
        }

        # 遗传算法配置
        pop_size = 50
        mutation_rate_min = 0.01
        mutation_rate_max = 0.5
        crossover_rate_min = 0.5
        crossover_rate_max = 1
        min_elite_size = 2
        max_elite_size = 5
        tournament_size_min = 2
        tournament_size_max = 10

        with open(opt.hyp, errors="ignore") as f:
            hyp = yaml.safe_load(f)  # 加载超参数字典
            if "anchors" not in hyp:  # anchors 在 hyp.yaml 中被注释
                hyp["anchors"] = 3
        if opt.noautoanchor:
            del hyp["anchors"], meta["anchors"]
        opt.noval, opt.nosave, save_dir = True, True, Path(opt.save_dir)  # 仅验证/保存最后一个 epoch
        # ei = [isinstance(x, (int, float)) for x in hyp.values()]  # 可进化的索引
        evolve_yaml, evolve_csv = save_dir / "hyp_evolve.yaml", save_dir / "evolve.csv"
        if opt.bucket:
            # 下载 evolve.csv（如果存在）
            subprocess.run(
                [
                    "gsutil",
                    "cp",
                    f"gs://{opt.bucket}/evolve.csv",
                    str(evolve_csv),
                ]
            )

        # 删除 meta 字典中第一个值为 False 的项
        del_ = [item for item, value_ in meta.items() if value_[0] is False]
        hyp_GA = hyp.copy()  # 复制 hyp 字典
        for item in del_:
            del meta[item]  # 从 meta 字典中删除该项
            del hyp_GA[item]  # 从 hyp_GA 字典中删除该项

        # 设置 lower_limit 和 upper_limit 数组以保存搜索空间边界
        lower_limit = np.array([meta[k][1] for k in hyp_GA.keys()])
        upper_limit = np.array([meta[k][2] for k in hyp_GA.keys()])

        # 创建 gene_ranges 列表以保存种群中每个基因的值范围
        gene_ranges = [(lower_limit[i], upper_limit[i]) for i in range(len(upper_limit))]

        # 使用 initial_values 或随机值初始化种群
        initial_values = []

        # 如果从之前的检查点恢复进化
        if opt.resume_evolve is not None:
            assert os.path.isfile(ROOT / opt.resume_evolve), "进化种群路径错误！"
            with open(ROOT / opt.resume_evolve, errors="ignore") as f:
                evolve_population = yaml.safe_load(f)
                for value in evolve_population.values():
                    value = np.array([value[k] for k in hyp_GA.keys()])
                    initial_values.append(list(value))

        # 如果没有从之前的检查点恢复，则从 opt.evolve_population 中的 .yaml 文件生成初始值
        else:
            yaml_files = [f for f in os.listdir(opt.evolve_population) if f.endswith(".yaml")]
            for file_name in yaml_files:
                with open(os.path.join(opt.evolve_population, file_name)) as yaml_file:
                    value = yaml.safe_load(yaml_file)
                    value = np.array([value[k] for k in hyp_GA.keys()])
                    initial_values.append(list(value))

        # 为种群的其余部分生成搜索空间内的随机值
        if initial_values is None:
            population = [generate_individual(gene_ranges, len(hyp_GA)) for _ in range(pop_size)]
        elif pop_size > 1:
            population = [generate_individual(gene_ranges, len(hyp_GA)) for _ in range(pop_size - len(initial_values))]
            for initial_value in initial_values:
                population = [initial_value, *population]

        # 运行固定代数的遗传算法
        list_keys = list(hyp_GA.keys())
        for generation in range(opt.evolve):
            if generation >= 1:
                save_dict = {}
                for i in range(len(population)):
                    little_dict = {list_keys[j]: float(population[i][j]) for j in range(len(population[i]))}
                    save_dict[f"gen{generation!s}number{i!s}"] = little_dict

                with open(save_dir / "evolve_population.yaml", "w") as outfile:
                    yaml.dump(save_dict, outfile, default_flow_style=False)

            # 自适应精英规模
            elite_size = min_elite_size + int((max_elite_size - min_elite_size) * (generation / opt.evolve))
            # 评估种群中每个个体的适应度
            fitness_scores = []
            for individual in population:
                for key, value in zip(hyp_GA.keys(), individual):
                    hyp_GA[key] = value
                hyp.update(hyp_GA)
                results = train(hyp.copy(), opt, device, callbacks)
                callbacks = Callbacks()
                # 写入变异结果
                keys = (
                    "metrics/precision",
                    "metrics/recall",
                    "metrics/mAP_0.5",
                    "metrics/mAP_0.5:0.95",
                    "val/box_loss",
                    "val/obj_loss",
                    "val/cls_loss",
                )
                print_mutation(keys, results, hyp.copy(), save_dir, opt.bucket)
                fitness_scores.append(results[2])

            # 使用自适应锦标赛选择选择最适应的个体进行繁殖
            selected_indices = []
            for _ in range(pop_size - elite_size):
                # 自适应锦标赛规模
                tournament_size = max(
                    max(2, tournament_size_min),
                    int(min(tournament_size_max, pop_size) - (generation / (opt.evolve / 10))),
                )
                # 执行锦标赛选择以选择最佳个体
                tournament_indices = random.sample(range(pop_size), tournament_size)
                tournament_fitness = [fitness_scores[j] for j in tournament_indices]
                winner_index = tournament_indices[tournament_fitness.index(max(tournament_fitness))]
                selected_indices.append(winner_index)

            # 将精英个体添加到选定的索引中
            elite_indices = [i for i in range(pop_size) if fitness_scores[i] in sorted(fitness_scores)[-elite_size:]]
            selected_indices.extend(elite_indices)
            # 通过交叉和变异创建下一代
            next_generation = []
            for _ in range(pop_size):
                parent1_index = selected_indices[random.randint(0, pop_size - 1)]
                parent2_index = selected_indices[random.randint(0, pop_size - 1)]
                # 自适应交叉率
                crossover_rate = max(
                    crossover_rate_min, min(crossover_rate_max, crossover_rate_max - (generation / opt.evolve))
                )
                if random.uniform(0, 1) < crossover_rate:
                    crossover_point = random.randint(1, len(hyp_GA) - 1)
                    child = population[parent1_index][:crossover_point] + population[parent2_index][crossover_point:]
                else:
                    child = population[parent1_index]
                # 自适应变异率
                mutation_rate = max(
                    mutation_rate_min, min(mutation_rate_max, mutation_rate_max - (generation / opt.evolve))
                )
                for j in range(len(hyp_GA)):
                    if random.uniform(0, 1) < mutation_rate:
                        child[j] += random.uniform(-0.1, 0.1)
                        child[j] = min(max(child[j], gene_ranges[j][0]), gene_ranges[j][1])
                next_generation.append(child)
            # 用新一代替换旧种群
            population = next_generation
        # 打印找到的最佳解
        best_index = fitness_scores.index(max(fitness_scores))
        best_individual = population[best_index]
        print("找到的最佳解：", best_individual)
        # 绘制结果
        plot_evolve(evolve_csv)
        LOGGER.info(
            f"超参数进化完成 {opt.evolve} 代\n"
            f"结果保存到 {colorstr('bold', save_dir)}\n"
            f"使用示例：$ python train.py --hyp {evolve_yaml}"
        )


def generate_individual(input_ranges, individual_length):
    """在指定范围内生成具有随机超参数的个体。.

    参数：
        input_ranges (list[tuple[float, float]]): 元组列表，每个元组包含对应基因（超参数）的上下界。
        individual_length (int): 个体中基因（超参数）的数量。

    返回：
        list[float]: 表示生成的个体的列表，其基因值在指定范围内随机生成。

    示例：
        ```python
        input_ranges = [(0.01, 0.1), (0.1, 1.0), (0.9, 2.0)]
        individual_length = 3
        individual = generate_individual(input_ranges, individual_length)
        print(individual)  # 输出: [0.035, 0.678, 1.456]（示例输出）
        ```

    说明：
        返回的个体长度等于 `individual_length`，每个基因值均为 `input_ranges` 中对应范围内的浮点数。
    """
    individual = []
    for i in range(individual_length):
        lower_bound, upper_bound = input_ranges[i]
        individual.append(random.uniform(lower_bound, upper_bound))
    return individual


def run(**kwargs):
    """使用指定选项执行YOLOv5训练，可通过关键字参数进行可选覆盖。.

    参数：
        weights (str, 可选): 初始权重路径。默认为 ROOT / 'yolov5s.pt'。
        cfg (str, 可选): 模型YAML配置文件路径。默认为空字符串。
        data (str, 可选): 数据集YAML配置文件路径。默认为 ROOT / 'data/coco128.yaml'。
        hyp (str, 可选): 超参数YAML配置文件路径。默认为 ROOT / 'data/hyps/hyp.scratch-low.yaml'。
        epochs (int, 可选): 总训练轮数。默认为 100。
        batch_size (int, 可选): 所有GPU的总批次大小。设为-1可自动确定批次大小。默认为 16。
        imgsz (int, 可选): 训练和验证的图像尺寸（像素）。默认为 640。
        rect (bool, 可选): 是否使用矩形训练。默认为 False。
        resume (bool | str, 可选): 是否从最近训练恢复，可指定路径。默认为 False。
        nosave (bool, 可选): 仅保存最终检查点。默认为 False。
        noval (bool, 可选): 仅在最后一轮进行验证。默认为 False。
        noautoanchor (bool, 可选): 禁用自动锚框。默认为 False。
        noplots (bool, 可选): 不保存绘图文件。默认为 False。
        evolve (int, 可选): 对超参数进行指定代数的进化。若提供但无值则使用 300。
        evolve_population (str, 可选): 进化过程中加载种群的目录。默认为 ROOT / 'data/hyps'。
        resume_evolve (str, 可选): 从最后一代恢复超参数进化。默认为 None。
        bucket (str, 可选): 用于保存检查点的 gsutil 存储桶。默认为空字符串。
        cache (str, 可选): 在 'ram' 或 'disk' 中缓存图像数据。默认为 None。
        image_weights (bool, 可选): 训练时使用加权图像选择。默认为 False。
        device (str, 可选): CUDA 设备标识，例如 '0'、'0,1,2,3' 或 'cpu'。默认为空字符串。
        multi_scale (bool, 可选): 使用多尺度训练，图像尺寸变化 ±50%。默认为 False。
        single_cls (bool, 可选): 将多类数据作为单类训练。默认为 False。
        optimizer (str, 可选): 优化器类型，可选 ['SGD', 'Adam', 'AdamW']。默认为 'SGD'。
        sync_bn (bool, 可选): 使用同步批归一化，仅在 DDP 模式下可用。默认为 False。
        workers (int, 可选): DDP 模式下每个 rank 的最大数据加载器工作进程数。默认为 8。
        project (str, 可选): 保存训练运行的目录。默认为 ROOT / 'runs/train'。
        name (str, 可选): 保存训练运行的名称。默认为 'exp'。
        exist_ok (bool, 可选): 允许已存在的 project/name 而不递增。默认为 False。
        quad (bool, 可选): 使用 quad 数据加载器。默认为 False。
        cos_lr (bool, 可选): 使用余弦学习率调度器。默认为 False。
        label_smoothing (float, 可选): 标签平滑的 epsilon 值。默认为 0.0。
        patience (int, 可选): 早停耐心值，以无改善的轮数计量。默认为 100。
        freeze (list, 可选): 要冻结的层，例如 backbone=10，前3层 = [0, 1, 2]。默认为 [0]。
        save_period (int, 可选): 保存检查点的频率（轮数）。小于1则禁用。默认为 -1。
        seed (int, 可选): 全局训练随机种子。默认为 0。
        local_rank (int, 可选): 自动 DDP 多GPU参数，请勿修改。默认为 -1。

    返回：
        None: 该函数根据提供的选项启动YOLOv5训练或超参数进化。

    示例：
        ```python
        import train
        train.run(data='coco128.yaml', imgsz=320, weights='yolov5m.pt')
        ```

    说明：
        - 模型：https://github.com/ultralytics/yolov5/tree/master/models
        - 数据集：https://github.com/ultralytics/yolov5/tree/master/data
        - 教程：https://docs.ultralytics.com/yolov5/tutorials/train_custom_data
    """
    opt = parse_opt(True)
    for k, v in kwargs.items():
        setattr(opt, k, v)
    main(opt)
    return opt


if __name__ == "__main__":
    opt = parse_opt()
    main(opt)
