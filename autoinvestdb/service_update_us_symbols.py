from . import mysqlite
from . import iexcloudapi
import tkinter as tk
from tkinter import ttk


def Update_US_Symbols():

    print("updating us symbols...")

    # get symbols from db
    db = mysqlite.DB("./investment.db")
    tb = db.TB("symbols")
    dbsymbols = tb.query("*", 'WHERE `market`="us"')

    # disable all symbols that is auto management
    for symbol in dbsymbols:
        if dbsymbols[symbol]["auto"] == True:
            dbsymbols[symbol]["enable"] = False

    # get symbols from iex
    configs = db.TB("configs").query()
    if not "iex_token" in configs:
        configs["iex_token"] = {"value": ""}
    while True:
        try:
            token = configs["iex_token"]["value"]
            iexsymbols = iexcloudapi.getSymbols(token)
            break
        except:
            configs = ask_user_token(configs)
            db.TB("configs").update(configs)
    for symbol in iexsymbols:
        symbol = symbol.replace(".", "-").upper()
        if not symbol in dbsymbols:
            dbsymbols[symbol] = {
                "market": "us",
                "auto": True,
                "enable": True
            }
        elif dbsymbols[symbol]["auto"] == True:
            dbsymbols[symbol]["enable"] = True

    # save
    tb.update(dbsymbols)
    db.commit()
    db.close()


def ask_user_token(configs):
    win = tk.Tk()
    win.geometry("500x70")
    win.title("Please provide IEX token")
    lbl = ttk.Label(win, text="Please provide IEX token:")
    lbl.pack(fill="both")
    entry = ttk.Entry(win)
    entry.pack(fill="both")

    def getToken():
        configs["iex_token"]["value"] = entry.get()
        win.destroy()
    btn = ttk.Button(win, text="submit", command=getToken)
    btn.pack()
    win.mainloop()

    return configs
