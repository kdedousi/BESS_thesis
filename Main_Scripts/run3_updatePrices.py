import numpy as np

def update_prices(df, charging_DA, discharging_DA, charging_imb, discharging_imb, charging_aFRR, discharging_aFRR, coef_DAM, coef_imb_short, coef_imb_sur, coef_aFRR_up_reserve, coef_aFRR_down_reserve, step):

    charging_DA = np.array(charging_DA)
    discharging_DA = np.array(discharging_DA)
    charging_imb = np.array(charging_imb)
    discharging_imb = np.array(discharging_imb)
    charging_aFRR = np.array(charging_aFRR)  # aFRR Down reserve (Battery Charges)
    discharging_aFRR = np.array(discharging_aFRR)  # aFRR Up reserve (Battery Discharges)

    # Update DAM and Imbalance Prices
    df["Extrapolated_DAM_Price"] += coef_DAM * (charging_DA - discharging_DA)             
    df["Extrapolated_Imbalance_Surplus_Price"] += coef_imb_sur * charging_imb            
    df["Extrapolated_Imbalance_Shortage_Price"] += coef_imb_short * discharging_imb           
    df["Extrapolated_aFRR_Up_Price_reserve"] += coef_aFRR_up_reserve * discharging_aFRR      
    df["Extrapolated_aFRR_Down_Price_reserve"] += coef_aFRR_down_reserve * charging_aFRR 