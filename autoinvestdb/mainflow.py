from .service_initialize import Initializer
from .service_update_us_symbols import USSymbolUpdater
from .service_update_us_historical_data import USHistoricalDataUpdater
import threading


def RUN():

    obj = Initializer()
    runloop_with_report(obj)

    obj = USSymbolUpdater()
    runloop_with_report(obj)

    obj = USHistoricalDataUpdater()
    runloop_with_report(obj)


def runloop_with_report(obj):
    t = threading.Thread(target=obj.run)
    t.start()
    x = ""
    while obj.activate == True:
        if not x == obj.report:
            print(obj.report)
            x = obj.report
    t.join()