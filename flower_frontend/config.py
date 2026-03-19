# 应用配置文件

# 测试模式配置
# False: 正式模式，完整执行数据库初始化、连接、CRUD逻辑
# True: 测试模式，用于排查Flask基础启动问题，可临时关闭数据库依赖
TEST_MODE = False

# 模型使用配置
# True: 使用真实模型
# False: 不加载模型，使用模拟模型
USE_MODEL = True