# variant_analysis.py
import pandas as pd
import os

def run_variant_analysis(input_file, output_dir="outputs"):
    """
    Runs variant attribute analysis for uploaded Excel file.
    Saves the consolidated output to an Excel file in output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"processed_{os.path.basename(input_file)}")

    # Columns that should NOT be analyzed as attributes
    non_attribute_columns = ['SKU ID', 'SKU Descriptions', 'Revenue']

    # Load and clean data
    df = pd.read_excel(input_file)
    df.columns = df.columns.str.strip()

    # Determine attribute columns
    attribute_columns = [col for col in df.columns if col not in non_attribute_columns]

    consolidated = []

    for attribute in attribute_columns:
        df_attr = df[df[attribute].notna()]
        if df_attr.empty:
            continue

        summary = (
            df_attr.groupby(attribute)
            .agg(
                Total_Annual_Revenue=("Revenue", "sum"),
                Unique_Customers=("SKU ID", "nunique")
            )
            .reset_index()
        )

        total_rev = summary["Total_Annual_Revenue"].sum()
        summary["Percent_of_Total_Revenue"] = (
            summary["Total_Annual_Revenue"] / total_rev * 100
        ).round(1)
        summary["Attribute"] = attribute
        summary = summary.rename(columns={attribute: "Values"})
        summary = summary[
            ["Attribute", "Values", "Total_Annual_Revenue", "Percent_of_Total_Revenue", "Unique_Customers"]
        ].sort_values(["Attribute", "Total_Annual_Revenue"], ascending=[True, False])
        consolidated.append(summary)

    if not consolidated:
        raise ValueError("No valid attribute columns found in file.")

    final_table = pd.concat(consolidated, ignore_index=True)
    final_table.to_excel(output_file, index=False)

    return output_file  # ✅ return path for download
