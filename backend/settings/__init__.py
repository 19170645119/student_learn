DB_URI = "mysql+aiomysql://root:123456@127.0.0.1:3306/student_learn?charset=utf8mb4"

REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379
REDIS_DB = 0

# 阿里云百炼（通义千问）API
LLM_BASE_URL = "https://spark-api-open.xf-yun.com/agent/v1/"
LLM_API_KEY = "JPUXahEwpaHsnuewOsOf:hBzagoSHYLdYwpOoWXXa"
LLM_MODEL = "spark-x"

from datetime import timedelta

JWT_SECRET_KEY = "student_learn_jwt_secret_key_2026"
JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=15)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

# 邮件配置（演示模式，已禁用发送）
MAIL_USERNAME="3231591517@qq.com"
MAIL_PASSWORD="vyapcdbqjzhncjfc"
MAIL_FROM="3231591517@qq.com"
MAIL_PORT = 587
MAIL_SERVER = "smtp.qq.com"
MAIL_FROM_NAME = "个性化学习平台"
MAIL_STARTTLS = True
MAIL_SSL_TLS = False


