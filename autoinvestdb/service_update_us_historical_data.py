from . import yfapi
from . import mysqlite
import threading


class USHistoricalDataUpdater:

    def __init__(self):
        self.report = ""
        self.activate = True

    def run(self):
        self.get_symbols_need_update()
        self.get_table_list_in_db()
        def update_robert():
            while len(self.symbols) > 0:
                symbol = self.symbols.pop()
                self.report = "USHistoricalDataUpdater: updating symbol historical data...\tremaining: {}".format(
                    len(self.symbols))
                if not symbol + "_price" in self.pricetbs:
                    self.create_new_price_table(symbol)
                if not symbol + "_divid" in self.dividtbs:
                    self.create_new_dividend_table(symbol)
                if not symbol + "_split" in self.splittbs:
                    self.create_new_stocksplit_table(symbol)
                yfdata = self.get_yfdata_from_yfapi(symbol)
                self.update_price_table(symbol, yfdata)
                self.update_divid_table(symbol, yfdata)
                self.update_split_table(symbol, yfdata)
        threads = []
        for _ in range(5):
            threads.append(threading.Thread(target=update_robert))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.activate = False

    def get_symbols_need_update(self):
        db = mysqlite.DB("./investment.db")
        self.report = "USHistoricalDataUpdater: getting symbols need update..."
        tb = db.TB("symbols")
        data = tb.query("*", 'WHERE `market`="us" AND `enable`=true')
        self.symbols = []
        for symbol in data:
            self.symbols.append(symbol)
        db.close()

    def get_table_list_in_db(self):
        db = mysqlite.DB("./investment.db")
        self.report = "USHistoricalDataUpdater: getting table list..."
        self.pricetbs = db.listTB("_price")
        self.dividtbs = db.listTB("_divid")
        self.splittbs = db.listTB("_split")
        db.close()

    def get_yfdata_from_yfapi(self, symbol):
        yfdata = yfapi.query(symbol, 1000, disableInfo=True)
        return yfdata

    def update_price_table(self, symbol: str, yfdata: dict):
        db = mysqlite.DB("./investment.db")
        tb = db.TB(symbol+"_price")
        dbdata = tb.query("date")
        dbdates = list(dbdata.keys())
        yfdates = list(yfdata["price"].keys())
        if len(dbdata) == 0:
            start = 0
        elif dbdates[-1] == yfdates[-1]:
            return  # no need to update
        else:
            lastdate = dbdates[-1]
            start = yfdates.index(lastdate) + 1
        for i in range(start, len(yfdates)):
            date = yfdates[i]
            dbdata[date] = {}
            for item in yfdata["price"][date]:
                dbdata[date][item] = yfdata["price"][date][item]
        tb.update(dbdata)
        db.commit()
        db.close()

    def update_divid_table(self, symbol: str, yfdata: dict):
        db = mysqlite.DB("./investment.db")
        tb = db.TB(symbol+"_divid")
        yfdata = yfdata["dividend"]
        tb.update(yfdata)
        db.commit()
        db.close()

    def update_split_table(self, symbol: str, yfdata: dict):
        db = mysqlite.DB("./investment.db")
        tb = db.TB(symbol+"_split")
        yfdata = yfdata["stocksplit"]
        tb.update(yfdata)
        db.commit()
        db.close()

    def create_new_price_table(self, symbol: str):
        db = mysqlite.DB("./investment.db")
        tbname = symbol + "_price"
        tb = db.createTB(tbname, "date", "DATE")
        tb.addCol("open", "FLOAT")
        tb.addCol("high", "FLOAT")
        tb.addCol("low", "FLOAT")
        tb.addCol("close", "FLOAT")
        tb.addCol("adjclose", "FLOAT")
        tb.addCol("volume", "BIGINT")
        db.commit()
        db.close()

    def create_new_dividend_table(self, symbol: str):
        db = mysqlite.DB("./investment.db")
        tbname = symbol + "_divid"
        tb = db.createTB(tbname, "date", "DATE")
        tb.addCol("dividend", "FLOAT")
        db.commit()
        db.close()

    def create_new_stocksplit_table(self, symbol: str):
        db = mysqlite.DB("./investment.db")
        tbname = symbol + "_split"
        tb = db.createTB(tbname, "date", "DATE")
        tb.addCol("stocksplit", "FLOAT")
        db.commit()
        db.close()
