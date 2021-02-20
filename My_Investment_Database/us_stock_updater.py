from . import yfapi
from . import iexcloudapi
from . import symbolinfo_dbkeeper
from . import histprice_dbkeeper
from . import dividend_dbkeeper
from . import stocksplit_dbkeeper
from . import trendtable_dbkeeper
import tkinter as tk
from tkinter import ttk
from tkinter import font
import os


class USStockUpdater:

    def __init__(self, db_folder_path: str):
        self.info_keeper = symbolinfo_dbkeeper.DBKeeper(db_folder_path)
        self.price_keeper = histprice_dbkeeper.DBKeeper(db_folder_path)
        self.divid_keeper = dividend_dbkeeper.DBKeeper(db_folder_path)
        self.split_keeper = dividend_dbkeeper.DBKeeper(db_folder_path)
        self.trend_keeper = trendtable_dbkeeper.DBKeeper(db_folder_path)

    def update_symbols(self):
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
        data = self.info_keeper.query('WHERE market = "us" AND type = "stock"')
        n = 0
        for symbol in data:
            n += 1
            self.__print_report(
                "disabling symbols...\t{}/{}".format(n, len(data)))
            data[symbol]["enable"] = False
        # enable symbols
        n = 0
        for symbol in symbols:
            n += 1
            self.__print_report(
                "enabling symbols...\t{}/{}".format(n, len(symbols)))
            if symbol in data:
                data[symbol]["enable"] = True
                data[symbol]["type"] = "stock"
                data[symbol]["market"] = "us"
            else:
                data[symbol] = {"enable": True,
                                "type": "stock", "market": "us"}
        self.info_keeper.update(data)

    def update_info(self):
        data = self.info_keeper.query(
            'WHERE market = "us" AND enable = True AND type = "stock"')
        symbols = list(data.keys())
        n = 0
        for symbol in symbols:
            n += 1
            self.__print_report(
                "updating symbol information...\t{}/{}\t{}".format(n, len(symbols), symbol))
            api = yfapi.YFAPI(symbol)
            data[symbol]["short_name"] = api.shortName()
            data[symbol]["long_name"] = api.longName()
            data[symbol]["sector"] = api.sector()
            data[symbol]["industry"] = api.industry()
            data[symbol]["shares_outstanding"] = api.sharesOutstanding()
            data[symbol]["market_cap"] = api.marketCap()
            data[symbol]["fin_currency"] = api.financialCurrency()
        self.info_keeper.update(data)

    def update_historical_data(self, skipUpdated: bool = True):
        """
        This method updates historical price, dividend and stock split.
        Because of those three data are requesting from a same request,
        so updating them in same method can reducing requests.
        """
        # get symbols
        symbols_data = self.info_keeper.query(
            'WHERE market = "us" AND enable = True AND short_name IS NOT NULL AND sector IS NOT NULL AND industry IS NOT NULL'
        )
        symbols = list(symbols_data.keys())
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
        master_info = self.price_keeper.query_full_master_info()
        symbols = list(master_info.keys())
        n = 0
        for symbol in symbols:
            n += 1
            self.__print_report(
                "updating trend table data...\t{}/{}\t{}".format(n, len(symbols), symbol))
            price = self.price_keeper.query_price(symbol)
            self.trend_keeper.update(symbol, price)

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
