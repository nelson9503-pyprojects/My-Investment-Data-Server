from data_server.us_stock_updater import USStockUpdater
from datetime import datetime
import time


us_updater = USStockUpdater("D:/My_Investment_Database/investdb")
alive_check = 0

while True:

    time_check = datetime.now()

    if time_check.hour == 6 and time_check.weekday() in [0, 1, 2, 3, 4, 5]:
        us_updater.update_symbols()
        us_updater.update_historical_data()
        us_updater.update_trendtable()
    elif time_check.hour == 6 and time_check.weekday() in [6]:
        us_updater.update_info()

    time.sleep(60)
    alive_check += 1
    if alive_check == 20:
        print("alive. time:{}".format(time_check))
        alive_check = 0
