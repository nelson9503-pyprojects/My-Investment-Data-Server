from . import mysqlite
import os


class Initializer:

    def __init__(self):
        self.report = ""
        self.activate = True

    def run(self):
        try:
            self.check_database_exists()
            self.check_configs_table_exists()
            self.check_symbols_table_exists()
        except:
            pass
        self.activate = False

    def check_database_exists(self):
        self.report = "Initializer: initializing database..."
        if not os.path.exists("./investment.db"):
            db = mysqlite.DB("./investment.db")
        db.close()

    def check_configs_table_exists(self):
        self.report = "Initializer: initializing configs table..."
        db = mysqlite.DB("./investment.db")
        if not "configs" in db.listTB("configs"):
            tb = db.createTB("configs", "item", "CHAR(50)")
            tb.addCol("value", "CHAR(200)")
            db.commit()
        db.close()

    def check_symbols_table_exists(self):
        self.report = "Initializer: initializing symbols table..."
        db = mysqlite.DB("./investment.db")
        if not "symbols" in db.listTB("symbols"):
            tb = db.createTB("symbols", "symbol", "CHAR(20)")
            tb.addCol("market", "CHAR(5)")
            tb.addCol("auto", "BOOLEAN")
            tb.addCol("enable", "BOOLEAN")
            db.commit()
        db.close()
