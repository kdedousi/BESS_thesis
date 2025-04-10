import pandas as pd

def load_initial_prices(RES_current, RES_future, total_demand_current, total_demand_future, res_DAM, res_imb_short, res_imb_sur, res_aFRR_up_reserve, res_aFRR_down_reserve):
    # Load historical energy prices
    data_dam = pd.read_excel("py_2024_DAM_prices_hourly.xlsx", sheet_name="Sheet1")
    data_imbalance_surplus = pd.read_excel("py_2024_imbalance_prices_hourly_surplus.xlsx", sheet_name="Sheet1")
    data_imbalance_shortage = pd.read_excel("py_2024_imbalance_prices_hourly_shortage.xlsx", sheet_name="Sheet2")
    data_aFRR_up_reserve = pd.read_excel("aFRR_hourly_prices_Up.xlsx", sheet_name="Sheet1")  # Load aFRR Up reserve prices
    data_aFRR_down_reserve = pd.read_excel("aFRR_hourly_prices_Down.xlsx", sheet_name="Sheet1")  # Load aFRR Down reserve prices

    delta_res = (RES_future/total_demand_future - RES_current/total_demand_current) * 100

    data_dam["Price_future"] = data_dam["Price"] + res_DAM * delta_res
    data_imbalance_surplus["Price_future"] = data_imbalance_surplus["Price"] + res_imb_sur * delta_res
    data_imbalance_shortage["Price_future"] = data_imbalance_shortage["Price"] + res_imb_short * delta_res
    data_aFRR_up_reserve["Price_future"] = data_aFRR_up_reserve["Hourly price Reserve (€/MW)"] + res_aFRR_up_reserve * delta_res
    data_aFRR_down_reserve["Price_future"] = data_aFRR_down_reserve["Hourly price Reserve (€/MW)"] + res_aFRR_down_reserve * delta_res

    # Combine results into one DataFrame
    data_combined = pd.DataFrame({
        "Date": data_dam["Date"],
        "Historical_DAM_Price": data_dam["Price"],
        "Extrapolated_DAM_Price": data_dam["Price_future"],
        "Historical_Imbalance_Surplus_Price": data_imbalance_surplus["Price"],
        "Extrapolated_Imbalance_Surplus_Price": data_imbalance_surplus["Price_future"],
        "Historical_Imbalance_Shortage_Price": data_imbalance_shortage["Price"],
        "Extrapolated_Imbalance_Shortage_Price": data_imbalance_shortage["Price_future"],
        "Historical_aFRR_Up_Price_reserve": data_aFRR_up_reserve["Hourly price Reserve (€/MW)"],
        "Extrapolated_aFRR_Up_Price_reserve": data_aFRR_up_reserve["Price_future"],
        "Historical_aFRR_Down_Price_reserve": data_aFRR_down_reserve["Hourly price Reserve (€/MW)"],
        "Extrapolated_aFRR_Down_Price_reserve": data_aFRR_down_reserve["Price_future"]
    })
    
    return data_combined
