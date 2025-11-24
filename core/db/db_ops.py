from core.db.db_init import DbIntialization


class DbOperation(DbIntialization):
    def __init__(self):
        super().__init__()
    def create_table(self):
        engin = self.initialize_engine()
        