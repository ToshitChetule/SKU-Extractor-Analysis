
# ...existing code...
import pandas as pd
import os
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment
from openpyxl.chart import BarChart, Reference, PieChart
from openpyxl.chart import PieChart, Reference

from openpyxl.utils import get_column_letter
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
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        final_table.to_excel(writer, index=False, sheet_name="Sheet1")
        
    # Autofit columns/rows and apply number formats
    _autofit_and_format_excel(output_file, sheet_name="Sheet1")

    # Add visualization charts
    _add_visualizations_to_excel(output_file, sheet_name="Sheet1")

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

def _add_visualizations_to_excel(filepath, sheet_name="Sheet1"):
    """
    Adds visualization charts to a new sheet 'Visualizations' in the same Excel workbook.
    Creates:
    1. Top 10 Values by Revenue (Bar Chart)
    2. Revenue % Contribution by Attribute (Pie Chart)
    3. Stacked Column Chart (Attribute vs Values)
    """
    wb = load_workbook(filepath)
    if sheet_name not in wb.sheetnames:
        return

    ws = wb[sheet_name]

    # Create visualization sheet
    if "Visualizations" in wb.sheetnames:
        vis_ws = wb["Visualizations"]
        for row in vis_ws["A1:Z100"]:
            for cell in row:
                cell.value = None
    else:
        vis_ws = wb.create_sheet("Visualizations")

    # Collect data from Sheet1
    df = pd.DataFrame(ws.values)
    df.columns = df.iloc[0]
    df = df.drop(0)

    # Ensure numeric columns are floats
    for col in ["Total Annual Revenue", "Percentage of Total Revenue"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ✅ 1. BAR CHART – Top 10 values by revenue
    try:
        top10 = (
            df.groupby("Values")["Total Annual Revenue"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )
        vis_ws["A1"] = "Top 10 Values by Total Annual Revenue"
        for i, (val, rev) in enumerate(top10.items(), start=3):
            vis_ws[f"A{i}"] = val
            vis_ws[f"B{i}"] = rev

        bar_chart = BarChart()
        bar_chart.title = "Top 10 Values by Revenue"
        bar_chart.y_axis.title = "Total Annual Revenue"
        bar_chart.x_axis.title = "Values"

        data = Reference(vis_ws, min_col=2, min_row=3, max_row=12)
        cats = Reference(vis_ws, min_col=1, min_row=3, max_row=12)
        bar_chart.add_data(data, titles_from_data=False)
        bar_chart.set_categories(cats)
        bar_chart.width, bar_chart.height = 20, 10
        vis_ws.add_chart(bar_chart, "D2")
    except Exception as e:
        print("⚠️ Skipping Bar Chart:", e)

    # ✅ 2. PIE CHART – Revenue % contribution by attribute
    try:
        pie_data = (
            df.groupby("Attribute")["Total Annual Revenue"]
            .sum()
            .sort_values(ascending=False)
            .head(6)
        )

        vis_ws["A15"] = "Top Attributes by Revenue Share"
        for i, (attr, rev) in enumerate(pie_data.items(), start=17):
            vis_ws[f"A{i}"] = attr
            vis_ws[f"B{i}"] = rev

        pie_chart = PieChart()
        pie_chart.title = "Revenue Share by Attribute"
        labels = Reference(vis_ws, min_col=1, min_row=17, max_row=17 + len(pie_data) - 1)
        data = Reference(vis_ws, min_col=2, min_row=17, max_row=17 + len(pie_data) - 1)
        pie_chart.add_data(data, titles_from_data=False)
        pie_chart.set_categories(labels)
        pie_chart.width, pie_chart.height = 12, 8
        vis_ws.add_chart(pie_chart, "D15")
    except Exception as e:
        print("⚠️ Skipping Pie Chart:", e)

    # ✅ 3. STACKED COLUMN CHART – Attribute vs Values (aggregated)
    try:
        pivot = (
            df.groupby(["Attribute", "Values"])["Total Annual Revenue"]
            .sum()
            .reset_index()
        )
        pivot = pivot.sort_values(["Attribute", "Total Annual Revenue"], ascending=[True, False])
        pivot_top = pivot.groupby("Attribute").head(3)

        vis_ws["A30"] = "Attribute"
        vis_ws["B30"] = "Values"
        vis_ws["C30"] = "Revenue"
        for i, row in enumerate(pivot_top.itertuples(index=False), start=31):
            vis_ws[f"A{i}"] = row.Attribute
            vis_ws[f"B{i}"] = row.Values
            vis_ws[f"C{i}"] = row._3

        stacked_chart = BarChart()
        stacked_chart.type = "col"
        stacked_chart.grouping = "stacked"
        stacked_chart.title = "Revenue by Attribute (Top 3 Values)"
        stacked_chart.y_axis.title = "Revenue"
        stacked_chart.x_axis.title = "Attribute"

        data = Reference(vis_ws, min_col=3, min_row=30, max_row=30 + len(pivot_top))
        cats = Reference(vis_ws, min_col=1, min_row=31, max_row=30 + len(pivot_top))
        stacked_chart.add_data(data, titles_from_data=True)
        stacked_chart.set_categories(cats)
        stacked_chart.width, stacked_chart.height = 20, 10
        vis_ws.add_chart(stacked_chart, "D30")
    except Exception as e:
        print("⚠️ Skipping Stacked Chart:", e)

    wb.save(filepath)
    print("✅ Visualization sheet added successfully!")
