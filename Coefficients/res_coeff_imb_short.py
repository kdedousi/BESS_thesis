import pandas as pd
import statsmodels.api as sm

def res_coefficients_imb_short(file_path):
    df = pd.read_excel(file_path, sheet_name="Imb_short_hourly").apply(pd.to_numeric, errors='coerce').dropna()

    X = sm.add_constant(df[['Renewable_energy (MWh)', 'Renewable_Share (%)', 'Demand (MWh)', 'Coal_Prices (€/MWh)']])
    y = df["Electricity_Price_Imb_Short (€/MWh)"]

    model = sm.OLS(y, X).fit()

    return model.params.get("Renewable_Share (%)", None)

coeff_imb_short = res_coefficients_imb_short("bess_price_data.xlsx")
print(f"α_imb_shortage (per % RES): {coeff_imb_short:.4f} €/MWh")