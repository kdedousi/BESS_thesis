import pandas as pd

def load_initial_prices(RES_current, RES_future, price_per_mwh_res):
    # Load historical energy prices
    data_dam = pd.read_excel("py_2024_DAM_prices_hourly.xlsx", sheet_name="Sheet1")
    data_imbalance = pd.read_excel("py_2024_imbalance_prices_hourly_surplus.xlsx", sheet_name="Sheet1")
    
    # Select the first 1000 rows
    data_dam = data_dam.iloc[:, :]
    data_imbalance = data_imbalance.iloc[:, :]

    delta_res = RES_future - RES_current
    data_dam["Price_future"] = data_dam["Price"] + price_per_mwh_res * delta_res
    data_imbalance["Price_future"] = data_imbalance["Price"] + price_per_mwh_res * delta_res
    
    # Combine results into one DataFrame
    data_combined = pd.DataFrame({
        "Date": data_dam["Date"],
        "Historical_DAM_Price": data_dam["Price"],
        "Extrapolated_DAM_Price": data_dam["Price_future"],
        "Historical_Imbalance_Price": data_imbalance["Price"],
        "Extrapolated_Imbalance_Price": data_imbalance["Price_future"]
    })
    
    return data_combined


