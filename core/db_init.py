from sqlalchemy import create_engine
from sqlalchemy import URL

DATABASE_NAME="prompt_manger"
DATABASE_PASSWORD="postgres"
DATABASE_USERNAME="postgres"
DATABASE_PORT="5432"
DATABASE_HOST="localhost"
DATABASE_DRIVER_NAME="postgresql"


class DbIntialization:
    def __init__(self):
        self.DATABASE_NAME = "prompt_manger"
        self.DATABASE_PASSWORD = "postgres"
        self.DATABASE_USERNAME = "postgres"
        self.DATABASE_PORT = 5432
        self.DATABASE_HOST = "localhost"
        self.DATABASE_DRIVER_NAME = "postgresql"
    def do_create_table(self):
        pass

    def do_create_url(self):
        url_object = URL.create(drivername=self.DATABASE_DRIVER_NAME,
            username=self.DATABASE_USERNAME,
            password=self.DATABASE_PASSWORD,
            host=self.DATABASE_HOST,
            port=self.DATABASE_PORT,
            database=self.DATABASE_NAME,
        )
        return url_object
    def initialize_engin(self):
        url_object = self.do_create_url()
        engine = create_engine(url_object)
        return engine
    def _do_postgres_process(self):
        pass
    def _do_sqlite_process(self):
        pass
    def _do_oracle_process(self):
        pass