import pandas as pd
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc
import os


# =============================
# DATA PREPARATION
# =============================

df = pd.read_csv("data.csv")

df = df[
[
"CustomerID",
"Gender",
"Location",
"Product_Category",
"Quantity",
"Avg_Price",
"Transaction_Date",
"Month",
"Discount_pct"
]
]

df["CustomerID"] = df["CustomerID"].fillna(0).astype(int)

df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
df["Avg_Price"] = pd.to_numeric(df["Avg_Price"], errors="coerce")
df["Discount_pct"] = pd.to_numeric(df["Discount_pct"], errors="coerce")

df["Transaction_Date"] = pd.to_datetime(df["Transaction_Date"], errors="coerce")

df = df.dropna(subset=["Transaction_Date","Quantity","Avg_Price"])

df["Total_price"] = df["Quantity"] * df["Avg_Price"] * (1 - df["Discount_pct"]/100)


# =============================
# APP
# =============================

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# 🔥 IMPORTANT POUR DEPLOIEMENT
server = app.server


# =============================
# LAYOUT
# =============================

app.layout = html.Div([

# HEADER
html.Div([
    html.Div([
        html.H2("ECAP Store Dashboard", style={"color":"white"}),
        html.P("Analyse des ventes", style={"color":"#e8f1f5"})
    ]),

    dcc.Dropdown(
        id="location_filter",
        options=[{"label":i,"value":i} for i in sorted(df["Location"].unique())],
        multi=True,
        placeholder="Filtrer par zone",
        style={"width":"300px"}
    )

], style={
    "background":"linear-gradient(90deg,#4e73df,#224abe)",
    "padding":"20px",
    "display":"flex",
    "justifyContent":"space-between"
}),

# BODY
html.Div([

# LEFT
html.Div([

html.Div([

dbc.Card([
    dbc.CardBody([
        html.P("Chiffre d'affaire - Décembre"),
        html.H1(id="kpi_ca"),
        html.Div(id="kpi_ca_var")
    ])
], style={"width":"48%"}),

dbc.Card([
    dbc.CardBody([
        html.P("Nombre de ventes - Décembre"),
        html.H1(id="kpi_sales"),
        html.Div(id="kpi_sales_var")
    ])
], style={"width":"48%"})

], style={"display":"flex"}),

dcc.Graph(id="bar_chart")

], style={"width":"45%"}),

# RIGHT
html.Div([

dcc.Graph(id="line_chart"),

dash_table.DataTable(
    id="sales_table",
    page_size=10,
    filter_action="native",
    sort_action="native"
)

], style={"width":"55%"})

], style={"display":"flex"})

])


# =============================
# CALLBACK
# =============================

@app.callback(
[
Output("kpi_ca","children"),
Output("kpi_ca_var","children"),
Output("kpi_sales","children"),
Output("kpi_sales_var","children"),
Output("line_chart","figure"),
Output("bar_chart","figure"),
Output("sales_table","data"),
Output("sales_table","columns")
],
Input("location_filter","value")
)

def update_dashboard(location):

    dff = df.copy()

    if location:
        dff = dff[dff["Location"].isin(location)]

# KPI
    dec = dff[dff["Transaction_Date"].dt.month == 12]
    nov = dff[dff["Transaction_Date"].dt.month == 11]

    ca_dec = dec["Total_price"].sum()
    ca_nov = nov["Total_price"].sum()

    sales_dec = len(dec)
    sales_nov = len(nov)

    kpi_ca = f"{ca_dec/1000:.0f}k"
    kpi_sales = f"{sales_dec}"

    kpi_ca_var = html.Span(f"{ca_dec-ca_nov:.0f}", style={"color":"green"})
    kpi_sales_var = html.Span(f"{sales_dec-sales_nov}", style={"color":"green"})

# LINE
    weekly = dff.groupby(pd.Grouper(key="Transaction_Date", freq="W"))["Total_price"].sum().reset_index()

    line = px.line(weekly, x="Transaction_Date", y="Total_price")

    line.update_layout(template="plotly_white")

    line.update_xaxes(dtick="M3", tickformat="%b %Y")

# BAR (nombre commandes)
    dff_dec = dff[dff["Transaction_Date"].dt.month == 12]

    df_grouped = dff_dec.groupby(["Product_Category","Gender"]).size().unstack(fill_value=0)

    df_grouped["total"] = df_grouped.sum(axis=1)
    df_grouped = df_grouped.sort_values("total", ascending=False).head(10)
    df_grouped = df_grouped.drop(columns="total")

    bar = px.bar(
        df_grouped.reset_index().melt(id_vars="Product_Category"),
        x="value",
        y="Product_Category",
        color="Gender",
        orientation="h",
        color_discrete_map={"F":"#FFB6C1","M":"#ADD8E6"}
    )

# TABLE
    table = dff.head(100)

    columns=[{"name":i,"id":i} for i in table.columns]

    return kpi_ca, kpi_ca_var, kpi_sales, kpi_sales_var, line, bar, table.to_dict("records"), columns


# =============================
# RUN (IMPORTANT POUR CLOUD)
# =============================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8050)),
        debug=False
    )