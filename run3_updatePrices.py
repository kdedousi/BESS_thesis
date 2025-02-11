import pandas as pd
import numpy as np

def update_prices(df, charging_DA, discharging_DA, charging_imb, discharging_imb, price_per_mwh_bess):

    charging_DA = np.array(charging_DA)
    discharging_DA = np.array(discharging_DA)
    charging_imb = np.array(charging_imb)
    discharging_imb = np.array(discharging_imb)

    df["Extrapolated_DAM_Price"] += price_per_mwh_bess * (discharging_DA - charging_DA)
    df["Extrapolated_Imbalance_Price"] += price_per_mwh_bess * (discharging_imb - charging_imb)

