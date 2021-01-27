from . import mysqlite
import os


def Initialize():

    print("Initializing...")

    # database
    db = mysqlite.DB("./investment.db")

    # configs
    if not "configs" in db.listTB("configs"):
        tb = db.createTB("configs", "item", "CHAR(50)")
        tb.addCol("value", "CHAR(200)")

    # symbols
    if not "symbols" in db.listTB("symbols"):
        tb = db.createTB("symbols", "symbol", "CHAR(20)")
        tb.addCol("market", "CHAR(5)")
        tb.addCol("auto", "BOOLEAN")
        tb.addCol("enable", "BOOLEAN")

    db.commit()
    db.close()