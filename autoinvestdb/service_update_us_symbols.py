from . import mysqlite
from . import iexcloudapi
import tkinter as tk
from tkinter import ttk


class USSymbolUpdater:

    def __init__(self):
        self.report = ""
        self.activate = True
    
    def run(self):
        try:
            self.get_symbols_from_db()
            self.get_symbols_from_iex()
            self.disable_all_symbols()
            self.update_symbols_from_iex_to_db()
        except:
            pass
        self.activate = False

    def get_symbols_from_db(self):
        self.report = "USSymbolUpdater: getting symbols from database..."
        db = mysqlite.DB("./investment.db")
        tb = db.TB("symbols")
        self.dbsymbols = tb.query("*", 'WHERE `market`="us"')
        db.close()

    def get_symbols_from_iex(self):
        self.report = "USSymbolUpdater: getting symbols from iex cloud..."
        db = mysqlite.DB("./investment.db")
        tb = db.TB("configs")
        self.configs = tb.query()
        if not "iex_token" in self.configs:
            self.configs["iex_token"] = {"value": ""}
        while True:
            try:
                token = self.configs["iex_token"]["value"]
                self.iexsymbols = iexcloudapi.getSymbols(token)
                break
            except:
                self.ask_user_token()
                tb.update(self.configs)
                db.commit()
        db.close()

    def disable_all_symbols(self):
        self.report = "USSymbolUpdater: disabling symbols in database..."
        for symbol in self.dbsymbols:
            if self.dbsymbols[symbol]["auto"] == True:
                self.dbsymbols[symbol]["enable"] = False

    def update_symbols_from_iex_to_db(self):
        n = 0
        for symbol in self.iexsymbols:
            n += 1
            self.report = "USSymbolUpdater: updating symbols\t{}/{}".format(
                n, len(self.iexsymbols))
            symbol = symbol.replace(".", "-").upper()
            if not symbol in self.dbsymbols:
                self.dbsymbols[symbol] = {
                    "market": "us",
                    "auto": True,
                    "enable": True
                }
            elif self.dbsymbols[symbol]["auto"] == True:
                self.dbsymbols[symbol]["enable"] = True
        self.report = "saving changes..."
        db = mysqlite.DB("./investment.db")
        tb = db.TB("symbols")
        tb.update(self.dbsymbols)
        db.commit()
        db.close()

    def ask_user_token(self):
        self.report = "USSymbolUpdater: waiting iex token from user..."
        win = tk.Tk()
        win.geometry("500x70")
        win.title("Please provide IEX token")
        lbl = ttk.Label(win, text="Please provide IEX token:")
        lbl.pack(fill="both")
        entry = ttk.Entry(win)
        entry.pack(fill="both")

        def getToken():
            self.configs["iex_token"]["value"] = entry.get()
            win.destroy()
        btn = ttk.Button(win, text="submit", command=getToken)
        btn.pack()
        win.mainloop()
