import os
from datetime import timedelta

DB_URI = os.getenv("DB_URI", "mysql+aiomysql://root:123456@127.0.0.1:3306/student_learn?charset=utf8mb4")

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# ??????????
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://spark-api-open.xf-yun.com/agent/v1/")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "spark-x")

# ???? DashScope??????- ? openai_service.py ???
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "student_learn_jwt_secret_key_2026")
JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=15)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

# ???????????
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
MAIL_FROM = os.getenv("MAIL_FROM", "")
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.qq.com")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "???????")
MAIL_STARTTLS = os.getenv("MAIL_STARTTLS", "True").lower() == "true"
MAIL_SSL_TLS = os.getenv("MAIL_SSL_TLS", "False").lower() == "true"
