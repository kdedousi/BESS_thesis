import pandas as pd
import statsmodels.api as sm

def res_coefficients_imb_surplus(file_path):
    df = pd.read_excel(file_path, sheet_name="Imb_surpl_hourly").apply(pd.to_numeric, errors='coerce').dropna()

    X = sm.add_constant(df[['Renewable_energy (MWh)', 'Renewable_Share (%)', 'Demand (MWh)', 'Coal_Prices (€/MWh)']])
    y = df["Electricity_Price_Imb_Sur (€/MWh)"]

    model = sm.OLS(y, X).fit()

    return model.params.get("Renewable_Share (%)", None)

coeff_imb_surpl = res_coefficients_imb_surplus("bess_price_data.xlsx")
print(f"α_imb_surplus (per % RES): {coeff_imb_surpl:.4f} €/MWh")
