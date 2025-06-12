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
