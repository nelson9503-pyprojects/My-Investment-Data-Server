from .service_initialize import Initialize
from .service_update_us_symbols import Update_US_Symbols
from .service_update_us_historical_data import Update_US_Historical_Data


def RUN():

    Initialize()
    Update_US_Symbols()
    Update_US_Historical_Data()