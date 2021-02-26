from . import yfapi
from . import iexcloudapi
from . import trendtable
from . import investdb_keepers
import tkinter as tk
from tkinter import ttk
from tkinter import font
import os


class USStockUpdater:

    def __init__(self, db_folder_path: str):
        self.info_keeper = investdb_keepers.SymbolInfoKeeper(db_folder_path)
        self.price_keeper = investdb_keepers.HistoricalPriceKeeper(
            db_folder_path)
        self.divid_keeper = investdb_keepers.DividendKeeper(db_folder_path)
        self.split_keeper = investdb_keepers.StockSplitKeeper(db_folder_path)
        self.trend_keeper = investdb_keepers.TrendTableKeeper(db_folder_path)

    def update_symbols(self):
        # get symbol from IEX Cloud
        while True:
            self.__print_report("getting symbols from IEX Cloud...")
            token = self.__get_iex_token()
            try:
                symbols = iexcloudapi.getSymbols(token)
                break
            except:
                self.__print_report("waiting iex token from user...")
                self.__ask_user_for_iex_token()
        # disable all symbols in us market
        data = self.info_keeper.query()
        n = 0
        for symbol in data.get_key_list():
            n += 1
            self.__print_report(
                "disabling symbols...\t{}/{}".format(n, len(data.get_key_list())))
            data.write(symbol, "enable", False)
        # enable symbols
        n = 0
        for symbol in symbols:
            n += 1
            self.__print_report(
                "enabling symbols...\t{}/{}".format(n, len(symbols)))
            data.write(symbol, "enable", True)
            data.write(symbol, "type", "stock")
            data.write(symbol, "market", "us")
        self.info_keeper.update(data.to_dict())

    def update_info(self):
        data = self.info_keeper.query()
        symbols = data.get_key_list()
        n = 0
        for symbol in symbols:
            n += 1
            self.__print_report(
                "updating symbol information...\t{}/{}\t{}".format(n, len(symbols), symbol))
            api = yfapi.YFAPI(symbol)
            data.write(symbol, "short_name", api.shortName())
            data.write(symbol, "long_name", api.longName())
            data.write(symbol, "sector", api.sector())
            data.write(symbol, "industry", api.industry())
            data.write(symbol, "shares_outstanding", api.sharesOutstanding())
            data.write(symbol, "market_cap", api.marketCap())
            data.write(symbol, "fin_currency", api.financialCurrency())
        self.info_keeper.update(data.to_dict())

    def update_historical_data(self):
        """
        This method updates historical price, dividend and stock split.
        Because of those three data are requesting from a same request,
        so updating them in same method can reducing requests.
        """
        # get symbols
        symbols_data = self.info_keeper.query()
        symbols = []
        for symbol in symbols_data.get_key_list():
            if symbols_data.read(symbol, "market") == "us" and symbols_data.read(symbol, "enable") == True:
                symbols.append(symbol)
        n = 0
        for symbol in symbols:
            n += 1
            self.__print_report(
                "updating historical data...\t{}/{}\t{}".format(n, len(symbols), symbol))
            retry = 0
            while True:
                try:
                    api = yfapi.YFAPI(symbol)
                    break
                except:
                    retry += 1
                    if retry == 3:
                        continue
            # historical price
            price_data = api.price()
            self.price_keeper.update(symbol, price_data)
            # dividend
            divid_data = api.dividend()
            self.divid_keeper.update(symbol, divid_data)
            # stock split
            stock_split = api.stocksplit()
            self.split_keeper.update(symbol, stock_split)

    def update_trendtable(self, skipUpdated: bool = True):
        """
        Update trend table of prices data.
        """
        price_info = self.price_keeper.query_master()
        trendtable_info = self.trend_keeper.query_master()
        symbols = price_info.get_key_list()
        n = 0
        for symbol in symbols:
            n += 1
            self.__print_report(
                "updating trend table data...\t{}/{}\t{}".format(n, len(symbols), symbol))
            if symbol in trendtable_info.get_key_list():
                last_update = trendtable_info.read(symbol, "last_update")
                if last_update == 0:
                    last_update = -9999999999999
            price = self.price_keeper.query(symbol, start_timestamp=last_update-6307200)
            dates = price.get_key_list()
            adjcloses = price.get_col_data("adjclose")
            updates = {}
            for i in range(len(dates)):
                date = dates[i]
                if date < last_update or i < 378:
                    continue
                li = adjcloses[i-378+1:i+1]
                result = trendtable.cal_trend_serious(li, 3)
                updates[date] = {}
                for t in result:
                    updates[date]["tb"+str(t)] = result[t]
            self.trend_keeper.update(symbol, updates)

    def __get_iex_token(self) -> str:
        token_path = "./iex_token.txt"
        if not os.path.exists(token_path):
            with open(token_path, 'w') as f:
                f.write("")
        with open(token_path, 'r') as f:
            token = f.read()
        return token

    def __ask_user_for_iex_token(self):
        token_path = "./iex_token.txt"
        win = tk.Tk()
        win.title("iex token")
        defaultFontObj = font.nametofont("TkDefaultFont")
        defaultFontObj.config(size=14)
        lbl = ttk.Label(win, text="Please provide IEX Cloud token:")
        lbl.pack()
        token_var = tk.StringVar()
        entry = ttk.Entry(win, textvariable=token_var, font=(14))
        entry.pack()
        btn = ttk.Button(win, text="submit", command=win.destroy)
        btn.pack()
        win.mainloop()
        with open(token_path, 'w') as f:
            f.write(token_var.get())

    def __print_report(self, text: str):
        print("US Stock Updater: {}".format(text))
