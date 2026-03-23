# 应用配置文件

# 测试模式配置
# False: 正式模式，完整执行数据库初始化、连接、CRUD逻辑
# True: 测试模式，用于排查Flask基础启动问题，可临时关闭数据库依赖
TEST_MODE = False

# 模型使用配置
# True: 使用真实模型
# False: 不加载模型，使用模拟模型
USE_MODEL = True

# SMTP邮件配置
MAIL_SERVER = 'smtp.qq.com'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = '3501123586@qq.com'  # QQ邮箱
MAIL_PASSWORD = 'mlbaryqvgbmbchib'  # QQ邮箱授权码
MAIL_DEFAULT_SENDER = '3501123586@qq.com'  # QQ邮箱

# 验证码配置
VERIFICATION_CODE_EXPIRY = 300  # 验证码过期时间（秒）
VERIFICATION_CODE_LENGTH = 6  # 验证码长度
VERIFICATION_CODE_RATE_LIMIT = 60  # 发送验证码的频率限制（秒）