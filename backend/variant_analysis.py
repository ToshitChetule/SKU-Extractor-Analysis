
# ...existing code...
import pandas as pd
import os
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment
# ...existing code...

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

        # summary = (
        #     df_attr.groupby(attribute)
        #     .agg(
        #         Total_Annual_Revenue=("Revenue", "sum"),
        #         Unique_Customers=("SKU ID", "nunique")
        #     )
        #     .reset_index()
        # )

        summary = ( df_attr.groupby(attribute) .agg( { "Revenue": "sum", "SKU ID": "nunique" } ) .rename( columns={ "Revenue": "Total Annual Revenue", "SKU ID": "# of Unique Customers" } ) .reset_index() )

        total_rev = summary["Total Annual Revenue"].sum()
        summary["Percentage of Total Revenue"] = (
            summary["Total Annual Revenue"] / total_rev * 100
        ).round(1)
        summary["Attribute"] = attribute
        summary = summary.rename(columns={attribute: "Values"})
        summary = summary[
            ["Attribute", "Values", "Total Annual Revenue", "Percentage of Total Revenue", "# of Unique Customers"]
        ].sort_values(["Attribute", "Total Annual Revenue"], ascending=[True, False])
        consolidated.append(summary)

    if not consolidated:
        raise ValueError("No valid attribute columns found in file.")

    final_table = pd.concat(consolidated, ignore_index=True)

    # Convert percentage column from "12.3" to 0.123 so Excel can show it as 12.3%
    if "Percentage of Total Revenue" in final_table.columns:
        final_table["Percentage of Total Revenue"] = final_table["Percentage of Total Revenue"] / 100.0

    # write to excel then autofit and format
    # ...existing code...
    # write to excel then autofit and format
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        final_table.to_excel(writer, index=False, sheet_name="Sheet1")
        # writer.save()  # removed: OpenpyxlWriter has no save() method; context manager writes file
# ...existing code...
    

    # Autofit columns/rows and apply number formats
    _autofit_and_format_excel(output_file, sheet_name="Sheet1")

    return output_file  # ✅ return path for download

def _autofit_and_format_excel(filepath, sheet_name="Sheet1"):
    """
    Adjust column widths and row heights to fit content, and apply number formats:
    - "Total Annual Revenue" => currency ($#,##0.00)
    - "Percentage of Total Revenue" => percentage with one decimal (0.0%)
    """
    wb = load_workbook(filepath)
    if sheet_name not in wb.sheetnames:
        wb.save(filepath)
        return
    ws = wb[sheet_name]

    # determine header names and column indexes
    headers = [cell.value for cell in ws[1]]

    # Autofit column widths based on max length of cell text in each column
    for col_cells in ws.columns:
        col_idx = col_cells[0].column
        col_letter = get_column_letter(col_idx)
        max_length = 0
        for cell in col_cells:
            val = cell.value
            if val is None:
                length = 0
            else:
                # account for numbers with formatting by converting to str
                length = len(str(val))
            if length > max_length:
                max_length = length
        # small adjustment for padding
        ws.column_dimensions[col_letter].width = max(8, max_length + 2)

    # Autofit row heights by counting line breaks
    for row in ws.iter_rows():
        max_lines = 1
        for cell in row:
            if cell.value and isinstance(cell.value, str):
                lines = cell.value.count("\n") + 1
                if lines > max_lines:
                    max_lines = lines
        if max_lines > 1:
            ws.row_dimensions[row[0].row].height = max_lines * 15  # approximate line height

    # Apply wrap_text and vertical alignment to all cells
    for row in ws.iter_rows():
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    # Apply number formats
    try:
        rev_col_idx = headers.index("Total Annual Revenue") + 1
    except ValueError:
        rev_col_idx = None
    try:
        pct_col_idx = headers.index("Percentage of Total Revenue") + 1
    except ValueError:
        pct_col_idx = None

    if rev_col_idx:
        for row in ws.iter_rows(min_row=2, min_col=rev_col_idx, max_col=rev_col_idx):
            for cell in row:
                # set currency format
                cell.number_format = '$#,##0.00'

    if pct_col_idx:
        for row in ws.iter_rows(min_row=2, min_col=pct_col_idx, max_col=pct_col_idx):
            for cell in row:
                # values already converted to decimal fraction; show one decimal percent
                cell.number_format = '0.0%'

    wb.save(filepath)
# ...existing code...