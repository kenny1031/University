import pandas as pd
from typing import Dict
import numpy as np
import os

# UPDATE if moved Spreadsheet to other directories
FILE_PATH = "../data/raw/Portfolio Optimisation - EF.xlsm"
SHEET = "Monthly Raw Data"

def load_data(
    file: str = FILE_PATH,
    sheet: str = SHEET,
    save_csv: bool = False,
    output_dir: str = "../data/cleaned"
) -> Dict[str, pd.DataFrame]:
    try:
        df = pd.read_excel(file, sheet_name=sheet, header=None)
    except FileNotFoundError as e:
        print(e)

    datasets = {}

    # Extract Monthly Total Returns from asset classes
    returns_table = df.iloc[4:302, 1:11]
    returns_table.columns = df.iloc[3, 1:11]
    datasets["monthly_returns"] = returns_table

    # Extract Summary statistics and accumulation value plots
    summary_table = df.iloc[4:12, 13:23]
    summary_table.columns = df.iloc[3, 13:23]
    datasets["summary_statistics"] = summary_table

    # Extract Accumulated value of initial $100 investment
    accum_table = df.iloc[4:302, 25:35]
    accum_table.columns = df.iloc[3, 25:35]
    datasets["accumulated_value"] = accum_table

    # Asset class metadata
    metadata_table = df.iloc[6:15, 38:44]
    metadata_table.columns = df.iloc[5, 38:44]
    datasets["asset_class_metadata"] = metadata_table

    # Cost and fees
    cost_fees = pd.read_excel(file, sheet_name="Cost and Fees", header=None)
    cost_fees = cost_fees.iloc[7:16, :4]
    cost_fees.columns = ["ID#", "Asset Class", "Investment fees", "Tax rate"]
    cost_fees = cost_fees.set_index("ID#")
    datasets["cost_fees"] = cost_fees

    # Compute adjusted returns
    returns = datasets["monthly_returns"].set_index("DATE").astype(float)
    cost_fees = cost_fees.set_index("Asset Class").astype(float)

    adj_returns = returns.copy()
    for i in range(adj_returns.shape[1]):
        col = adj_returns.columns[i]
        adj_returns[col] = (adj_returns[col] - cost_fees.iloc[i, 0]) * (1 - cost_fees.iloc[i, 1])
    datasets["adjusted_returns"] = adj_returns

    print("Loaded tables:")
    for name, df_ in datasets.items():
        if save_csv:
            save_path = os.path.join(output_dir, name + ".csv")
            df_.to_csv(save_path, index=False)
            print(f"Saved {save_path}")
        print(f"{name:25} shape={df_.shape}")
    return datasets


def load_rf(returns: pd.DataFrame, output_dir: str='../data/cleaned', save_csv=False) -> pd.DataFrame:
    # Simulate 25 years of monthly data
    np.random.seed(42)
    months = pd.date_range(start="2000-11-29", periods=25 * 12, freq="ME")

    # Simulate around a mean annualised rate of 3%, with small noise
    annual_rf = np.random.normal(loc=0.03, scale=0.005, size=len(months))
    monthly_rf = (1 + annual_rf) ** (1 / 12) - 1

    rf_df = pd.DataFrame({"DATE": months, "RF": monthly_rf})
    rf_df['DATE'] = pd.to_datetime(rf_df['DATE'])
    rf_df['YearMonth'] = rf_df['DATE'].dt.strftime('%Y%m').astype(int)
    rf_df = rf_df.drop(columns=['DATE']).dropna()

    returns['DATE'] = pd.to_datetime(returns['DATE'])
    returns['YearMonth'] = returns['DATE'].dt.strftime('%Y%m').astype(int)
    returns = returns.dropna()

    merged = pd.merge(returns, rf_df, on='YearMonth', how='inner')
    returns = returns.drop(columns=['YearMonth'])
    rf = merged[["DATE", "RF"]].set_index("DATE")

    if save_csv:
        rf.to_csv(os.path.join(output_dir, "RF.csv"), index=False)
        print(f"Saved RF shape={rf.shape}")

    return rf

if __name__ == "__main__":
    datasets = load_data(save_csv=True)
    load_rf(datasets["monthly_returns"], save_csv=True)