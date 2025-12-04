
import os
import sys
import torch
from pathlib import Path
import pathlib
import platform

# Windows系统下的路径兼容性处理
if platform.system() == 'Windows':
    _original_pure_posix_path = pathlib.PurePosixPath
    _original_posix_path = pathlib.PosixPath
    pathlib.PurePosixPath = pathlib.PureWindowsPath
    pathlib.PosixPath = pathlib.WindowsPath

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

# 从模块化文件导入FlowerVision类
from tool.flower_vision import FlowerVision

def main():
    """
    主函数，演示FlowerVision类的使用方式
    """
    import argparse
    
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='花卉识别程序 - 使用YOLOv5模型识别图片中的花卉')
    parser.add_argument('image_path', help='待识别的图片路径')
    parser.add_argument('--weights', default='testflowers.pt', help='模型权重文件路径（默认: testflowers.pt）')
    parser.add_argument('--device', default='cuda:0' if torch.cuda.is_available() else 'cpu', 
                        help='计算设备选择（默认: 优先GPU，否则CPU）')
    parser.add_argument('--conf-thres', type=float, default=0.25, help='置信度阈值（默认: 0.25）')
    parser.add_argument('--iou-thres', type=float, default=0.45, help='IoU阈值（默认: 0.45）')
    parser.add_argument('--verbose', action='store_true', help='显示详细的处理信息')
    args = parser.parse_args()
    
    # 实例化FlowerVision对象
    print(f"\n初始化花卉识别器...")
    print(f"- 设备: {args.device}")
    
    try:
        # 创建花卉识别器实例
        flower_detector = FlowerVision(device=args.device, verbose=args.verbose)
        
        # 加载模型权重
        print(f"\n正在加载模型: {args.weights}...")
        flower_detector.load_model(args.weights)
        
        # 显示模型信息
        if flower_detector.names:
            print(f"识别器支持 {len(flower_detector.names)} 种花卉类别")
        
        # 执行花卉识别
        print(f"\n正在识别图片: {args.image_path}...")
        results = flower_detector.recognize(
            args.image_path, 
            conf_thres=args.conf_thres, 
            iou_thres=args.iou_thres
        )
        
        # 格式化显示识别结果
        if results:
            print(f"\n✅ 识别成功！检测到 {len(results)} 个花卉实例:")
            # 按置信度降序排序结果
            results_sorted = sorted(results, key=lambda x: x['confidence'], reverse=True)
            
            for i, result in enumerate(results_sorted, 1):
                flower_name = result['flower']
                confidence = result['confidence']
                bbox = result['bbox']
                
                # 格式化输出
                print(f"  {i}. [{confidence:.2%}] {flower_name}")
                print(f"     位置: x1={bbox[0]}, y1={bbox[1]}, x2={bbox[2]}, y2={bbox[3]}")
                print(f"     尺寸: {bbox[2]-bbox[0]}×{bbox[3]-bbox[1]}")
        else:
            print(f"\n⚠️  未检测到任何花卉")
            
        print(f"\n✅ 处理完成")
        return 0
        
    except FileNotFoundError as e:
        print(f"\n❌ 文件错误: {str(e)}")
        return 1
    except RuntimeError as e:
        print(f"\n❌ 运行时错误: {str(e)}")
        return 1
    except ValueError as e:
        print(f"\n❌ 输入错误: {str(e)}")
        return 1
    except Exception as e:
        print(f"\n❌ 未预期的错误: {str(e)}")
        import traceback
        if args.verbose:
            traceback.print_exc()
        return 1


# 提供一个简单的使用示例函数，作为外部调用参考
def demo_usage(weights_path="testflowers.pt", image_path="example.jpg"):
    """
    演示如何在其他Python代码中使用FlowerVision类
    
    Args:
        weights_path (str): 模型权重文件路径
        image_path (str): 要识别的图片路径
        
    Returns:
        list: 识别结果列表，与recognize方法返回格式相同
    """
    # 创建识别器实例
    detector = FlowerVision(verbose=True)
    
    try:
        # 加载模型
        detector.load_model(weights_path)
        
        # 识别花卉
        results = detector.recognize(image_path)
        return results
    except Exception as e:
        print(f"识别失败: {str(e)}")
        return []


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)