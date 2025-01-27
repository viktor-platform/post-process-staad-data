import viktor as vkt
import pandas as pd

def generate_dataframe(table_data):
    df = pd.DataFrame([dict(item) for item in table_data])
    df.rename(
        columns={
            "col_beam": "Beam",
            "col_analysis_property": "Analysis Property",
            "col_design_property": "Design Property",
            "col_actual_ratio": "Actual Ratio",
            "col_allowable_ratio": "Allowable Ratio",
            "col_normalized_ratio": "Normalized Ratio (Actual/Allowable)",
            "col_clause": "Clause",
            "col_load_case": "L/C",
            "col_ax": "Ax in²",
            "col_iz": "Iz in⁴",
            "col_iy": "Iy in⁴",
            "col_ix": "Ix in⁴",
        },
        inplace=True,
    )
    return df

def get_cross_sections(params, **kwargs):
    if params.step_1.table:
        df = generate_dataframe(params.step_1.table)
        secs = df["Design Property"].unique().tolist()
        secs.append("All")
        return secs
    return ["No data available! Please add table input."]

class Parametrization(vkt.Parametrization):
    step_1 = vkt.Step("Step 1 - Input Your Data!")
    step_1.intro = vkt.Text("""
# STAAD Design Ratio Analyzer
This app allows you to visualize a heat map from your STAAD.PRO model results.
You can filter and group them based on cross sections and visualize how they are distributed.""")
    step_1.table_input = vkt.Text("""
## 1.0 Create the Input Table!
Paste the design ratio data from your STAAD.PRO model!""")

    step_1.table = vkt.Table("### Beam Design Analysis")
    step_1.table.col_beam = vkt.TextField("Beam")
    step_1.table.col_analysis_property = vkt.TextField("Analysis Property")
    step_1.table.col_design_property = vkt.TextField("Design Property")
    step_1.table.col_actual_ratio = vkt.NumberField("Actual Ratio")
    step_1.table.col_allowable_ratio = vkt.NumberField("Allowable Ratio")
    step_1.table.col_normalized_ratio = vkt.NumberField("Normalized Ratio")
    step_1.table.col_clause = vkt.TextField("Clause")
    step_1.table.col_load_case = vkt.TextField("L/C")
    step_1.table.col_ax = vkt.TextField("Ax in²")
    step_1.table.col_iz = vkt.TextField("Iz in⁴")
    step_1.table.col_iy = vkt.TextField("Iy in⁴")
    step_1.table.col_ix = vkt.TextField("Ix in⁴")

    step_2 = vkt.Step("Step 2 - Post-Processing", views=["table_design_ratios"])
    step_2.process = vkt.Text("""
## 2.0 Filter and Group
Group or filter by a specific cross section.
Use the options below to customize your view.
If you want to list all cross-sections after selecting one, you can select the "All" option!
""")
    step_2.group = vkt.BooleanField("### Group by Cross-Section")
    step_2.ln_break = vkt.LineBreak()
    step_2.cross_section = vkt.OptionField(
        "### Filter by Cross-Section", options=get_cross_sections
    )

class Controller(vkt.Controller):
    parametrization = Parametrization()

    @vkt.TableView(label="Design Ratios by Cross Section")
    def table_design_ratios(self, params, **kwargs):
        if not params.step_1.table or len(params.step_1.table) == 0:
            return vkt.TableResult([["No data available! Please add table input."]])

        df = generate_dataframe(params.step_1.table)

        # Group or filter the data based on user selection
        if params.step_2.group:
            # For each cross section, get the row with the maximum normalized ratio
            df = df.loc[
                df.groupby("Design Property")[
                    "Normalized Ratio (Actual/Allowable)"
                ].idxmax()
            ].reset_index(drop=True)
        if params.step_2.cross_section and params.step_2.cross_section != "All":
            df = df[df["Design Property"] == params.step_2.cross_section]

        # Drop unnecessary columns
        df.drop(
            ["Ax in²", "Iz in⁴", "Iy in⁴", "Ix in⁴", "Analysis Property", "Clause"],
            axis=1,
            inplace=True,
        )

        # Sort the DataFrame by Normalized Ratio in descending order
        df.sort_values(
            by="Normalized Ratio (Actual/Allowable)", ascending=False, inplace=True
        )

        # Create table data with color-coded cells
        data = []
        for _, row in df.iterrows():
            ratio = row["Normalized Ratio (Actual/Allowable)"]
            color = self.get_cell_color(ratio)
            row_data = row.tolist()
            row_data[4] = vkt.TableCell(ratio, background_color=color)
            data.append(row_data)

        return vkt.TableResult(
            data, column_headers=df.columns.tolist(), enable_sorting_and_filtering=True
        )

    def get_cell_color(self, ratio):
        if ratio >= 1:
            return vkt.Color(210, 0, 0)  # Red
        elif ratio >= 0.85:
            return vkt.Color(255, 165, 0)  # Orange
        else:
            return vkt.Color(0, 210, 0)  # Green