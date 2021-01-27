from . import yfapi
from . import mysqlite
from datetime import datetime
import threading


def Update_US_Historical_Data():
    global symbols
    symbols = get_symbols_need_update()
    tblist = get_table_list()
    while len(symbols) > 0:
        symbol = symbols.pop()
        print("Updating symbol historical data...\tremaining: {}".format(
            len(symbols)))
        if not symbol + "_price" in tblist:
            create_symbol_tables(symbol)
        update_symbol_data(symbol)


def get_table_list() -> list:
    db = mysqlite.DB("./investment.db")
    tbs = db.listTB()
    db.close()
    return tbs


def get_symbols_need_update() -> list:
    db = mysqlite.DB("./investment.db")
    tb = db.TB("symbols")
    data = tb.query("*", 'WHERE `market`="us" AND `enable`=true')
    symbols = []
    for symbol in data:
        symbols.append(symbol)
    db.close()
    return symbols


def create_symbol_tables(symbol: str):
    db = mysqlite.DB("./investment.db")
    # price
    tbname = symbol + "_price"
    tb = db.createTB(tbname, "date", "INT")
    tb.addCol("open", "FLOAT")
    tb.addCol("high", "FLOAT")
    tb.addCol("low", "FLOAT")
    tb.addCol("close", "FLOAT")
    tb.addCol("adjclose", "FLOAT")
    tb.addCol("volume", "BIGINT")
    # dividend
    tbname = symbol + "_divid"
    tb = db.createTB(tbname, "date", "DATE")
    tb.addCol("dividend", "FLOAT")
    # stocksplit
    tbname = symbol + "_split"
    tb = db.createTB(tbname, "date", "DATE")
    tb.addCol("stocksplit", "FLOAT")
    db.commit()
    db.close()


def update_symbol_data(symbol: str):
    db = mysqlite.DB("./investment.db")

    lastyear = datetime.now().year - 1
    lastyear_timestamp = datetime.timestamp(datetime(lastyear, 1, 1))

    # price
    tbname = symbol + "_price"
    tb = db.TB(tbname)
    dbdata = tb.query("date", "WHERE `date` > {}".format(lastyear_timestamp))
    if len(dbdata) == 0:
        yfdata = yfapi.query(symbol, 1000, disableInfo=True)
        laststamp = -9999999999
    else:
        yfdata = yfapi.query(symbol, 3, disableInfo=True)
        laststamp = max(list(dbdata.keys()))
    updates = {}
    for stamp in yfdata["price"]:
        if stamp > laststamp:
            updates[stamp] = yfdata["price"][stamp]
    tb.update(updates)

    # dividend
    tbname = symbol + "_divid"
    tb = db.TB(tbname)
    tb.update(yfdata["dividend"])

    # stocksplit
    tbname = symbol + "_split"
    tb = db.TB(tbname)
    dbdata = tb.query("date")
    if len(dbdata) == 0:
        dbmaxstamp = -9999999999
    else:
        dbmaxstamp = max(dbdata.keys())
    yfdata = yfdata["stocksplit"]
    if len(yfdata) == 0:
        yfmaxstamp = -9999999999
    else:
        yfmaxstamp = max(yfdata.keys())
    if yfmaxstamp > dbmaxstamp:
        tb.update(yfdata)
        tbname = symbol + "_price"
        tb = db.TB(tbname)
        dbdata = tb.query("date")
        yfdata = yfapi.query(symbol, 1000, disableInfo=True)
        for stamp in dbdata:
            dbdata[stamp] = yfdata["price"][stamp]
        tb.update(dbdata)

    db.commit()
    db.close()
