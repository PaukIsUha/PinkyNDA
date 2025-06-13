import os


class ConfigPostgre:
    username: str = os.getenv("POSTGRE_USERNAME", None)
    password: str = os.getenv("POSTGRE_PASSWORD", None)
    host: str = os.getenv("POSTGRE_HOST", None)
    port: str = os.getenv("POSTGRE_PORT", None)
    db_name: str = os.getenv("POSTGRE_DB_NAME", None)

    def __call__(self):
        return f"postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.db_name}"


CONFIG_POSTGRE = ConfigPostgre()


class ConfigRedis:
    host: str = os.getenv("REDIS_HOST", None)
    port: str = os.getenv("REDIS_PORT", None)
    num_buffer: str = os.getenv("REDIS_NUM_BUFFER", "0")
    buffer_key: str = os.getenv("REDIS_BUFFER_KEY", "spylog_buffer")

    def __call__(self):
        return f"redis://{self.host}:{self.port}/{self.num_buffer}"


CONFIG_REDIS = ConfigRedis()


class ConfigBot:
    token: str = os.getenv("BOT_TOKEN")


CONFIG_BOT = ConfigBot()
