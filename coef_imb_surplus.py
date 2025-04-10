import pandas as pd
import statsmodels.api as sm

def bess_coefficients_imb_surplus(file_path):
    df = pd.read_excel(file_path, sheet_name="Imb_surpl_hourly").apply(pd.to_numeric, errors='coerce').dropna()

    X = sm.add_constant(df[['Renewable_Share (%)', 'Renewable_energy (MWh)', 'Demand (MWh)', 'Gas_Prices (€/MWh)', 'Coal_Prices (€/MWh)']])
    y = df["Electricity_Price_Imb_Sur (€/MWh)"]

    model = sm.OLS(y, X).fit()

    return model.params.get("Demand (MWh)", None)

coeff_imb_surpl = bess_coefficients_imb_surplus("bess_price_data.xlsx")
print(f"Imbalance surplus Coefficient: {coeff_imb_surpl:.4f}")
