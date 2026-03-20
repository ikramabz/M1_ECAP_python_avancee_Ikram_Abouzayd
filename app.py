# DASHBOARD DE VENTES - ECAP STORE ikram 

import pandas as pd
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc
import os

# =========================
# IMPORT DATA
# =========================
DATA_PATH = os.getenv("DATA_PATH", "data.csv")

df = pd.read_csv(DATA_PATH)

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
        "Discount_pct",
    ]
]

# Nettoyage
df["CustomerID"] = df["CustomerID"].fillna(0).astype(int)
df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
df["Avg_Price"] = pd.to_numeric(df["Avg_Price"], errors="coerce")
df["Discount_pct"] = pd.to_numeric(df["Discount_pct"], errors="coerce")

df["Transaction_Date"] = pd.to_datetime(df["Transaction_Date"], errors="coerce")

df = df.dropna(subset=["Transaction_Date", "Quantity", "Avg_Price"])

df["Total_price"] = df["Quantity"] * df["Avg_Price"] * (
    1 - df["Discount_pct"] / 100
)

# =========================
# FONCTIONS
# =========================
def calculer_chiffre_affaire(data):
    return data["Total_price"].sum()


def frequence_meilleure_vente(data, top=10, ascending=False):
    return data["Product_Category"].value_counts(ascending=ascending).head(top)


def indicateur_du_mois(data, current_month=12):
    prev_month = 12 if current_month == 1 else current_month - 1

    current = data[data["Transaction_Date"].dt.month == current_month]
    previous = data[data["Transaction_Date"].dt.month == prev_month]

    return {
        "ca_current": calculer_chiffre_affaire(current),
        "ca_previous": calculer_chiffre_affaire(previous),
        "sales_current": len(current),
        "sales_previous": len(previous),
    }


# =========================
# APP DASH
# =========================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = html.Div([

    # HEADER
    html.Div([

        html.Div([
            html.H2("ECAP Store Dashboard", style={"color": "white"}),
            html.P("Analyse des ventes", style={"color": "white"})
        ]),

        dcc.Dropdown(
            id="location_filter",
            options=[
                {"label": i, "value": i}
                for i in sorted(df["Location"].dropna().unique())
            ],
            multi=True,
            placeholder="Filtrer par zone",
            style={"width": "250px"}
        )

    ], style={
        "backgroundColor": "#4e73df",
        "padding": "15px",
        "display": "flex",
        "justifyContent": "space-between"
    }),

    # BODY
    html.Div([

        # LEFT
        html.Div([

            html.Div([

                html.Div([
                    html.H4("Décembre"),
                    html.H1(id="kpi_ca"),
                    html.Div(id="kpi_ca_var")
                ], style={"width": "45%", "textAlign": "center"}),

                html.Div([
                    html.H4("Décembre"),
                    html.H1(id="kpi_sales"),
                    html.Div(id="kpi_sales_var")
                ], style={"width": "45%", "textAlign": "center"})

            ], style={"display": "flex", "justifyContent": "space-around"}),

            dcc.Graph(id="bar_chart")

        ], style={"width": "45%", "padding": "10px"}),

        # RIGHT
        html.Div([

            dcc.Graph(id="line_chart"),

            dash_table.DataTable(
                id="sales_table",
                page_size=10,
                filter_action="native",
                sort_action="native"
            )

        ], style={"width": "55%", "padding": "10px"})

    ], style={"display": "flex"})

])

# =========================
# CALLBACK
# =========================
@app.callback(
    [
        Output("kpi_ca", "children"),
        Output("kpi_ca_var", "children"),
        Output("kpi_sales", "children"),
        Output("kpi_sales_var", "children"),
        Output("line_chart", "figure"),
        Output("bar_chart", "figure"),
        Output("sales_table", "data"),
        Output("sales_table", "columns")
    ],
    Input("location_filter", "value")
)
def update_dashboard(location):

    # FILTRAGE
    dff = df.copy()
    if location:
        dff = dff[dff["Location"].isin(location)]

    # KPI (avec fonction)
    indicateurs = indicateur_du_mois(dff)

    ca_dec = indicateurs["ca_current"]
    ca_nov = indicateurs["ca_previous"]

    sales_dec = indicateurs["sales_current"]
    sales_nov = indicateurs["sales_previous"]

    var_ca = ca_dec - ca_nov
    var_sales = sales_dec - sales_nov

    # affichage KPI
    kpi_ca = f"{ca_dec/1000:.0f}k"
    kpi_sales = f"{sales_dec}"

    kpi_ca_var = html.Span(
        f"▲ +{var_ca/1000:.0f}k" if var_ca >= 0 else f"▼ -{abs(var_ca)/1000:.0f}k",
        style={"color": "green" if var_ca >= 0 else "red"}
    )

    kpi_sales_var = html.Span(
        f"▲ +{var_sales}" if var_sales >= 0 else f"▼ -{abs(var_sales)}",
        style={"color": "green" if var_sales >= 0 else "red"}
    )

    # =========================
    # LINE CHART
    # =========================
    weekly = (
        dff.groupby(pd.Grouper(key="Transaction_Date", freq="W"))["Total_price"]
        .sum()
        .reset_index()
    )

    line = px.line(
        weekly,
        x="Transaction_Date",
        y="Total_price",
        title="Evolution du chiffre d'affaire par semaine",
        labels={
            "Transaction_Date": "Semaine",
            "Total_price": "Chiffre d'affaires"
        }
    )

    # =========================
    # BAR CHART
    # =========================
    dff_dec = dff[dff["Transaction_Date"].dt.month == 12]

    top_categories = frequence_meilleure_vente(dff_dec)

    dff_dec = dff_dec[dff_dec["Product_Category"].isin(top_categories.index)]

    df_grouped = (
        dff_dec.groupby(["Product_Category", "Gender"])
        .size()
        .unstack(fill_value=0)
    )

    # tri
    df_grouped["total"] = df_grouped.sum(axis=1)
    df_grouped = df_grouped.sort_values("total", ascending=False).head(10)
    df_grouped = df_grouped.drop(columns="total")

    df_plot = df_grouped.reset_index().melt(id_vars="Product_Category")

    bar = px.bar(
        df_plot,
        x="value",
        y="Product_Category",
        color="Gender",
        orientation="h",
        barmode="group",
        title="Top 10 des catégories - Nombre de commandes (Décembre)",
        labels={
            "value": "Nombre de commandes",
            "Product_Category": "Catégorie",
            "Gender": "Genre"
        },
        color_discrete_map={"F": "#FFB6C1", "M": "#ADD8E6"},
        category_orders={
            "Product_Category": df_grouped.index.tolist()
        }
    )

    # =========================
    # TABLE
    # =========================
    table = dff.sort_values("Transaction_Date", ascending=False).head(100).copy()

    table["Transaction_Date"] = table["Transaction_Date"].dt.strftime("%d/%m/%Y")
    table["Avg_Price"] = table["Avg_Price"].round(2)
    table["Total_price"] = table["Total_price"].round(2)

    columns = [
        {"name": "Date", "id": "Transaction_Date"},
        {"name": "Sexe", "id": "Gender"},
        {"name": "Ville", "id": "Location"},
        {"name": "Catégorie produit", "id": "Product_Category"},
        {"name": "Quantité", "id": "Quantity"},
        {"name": "Prix moyen (€)", "id": "Avg_Price"},
        {"name": "Remise (%)", "id": "Discount_pct"},
        {"name": "Prix total (€)", "id": "Total_price"}
    ]

    # RETURN
    return (
        kpi_ca,
        kpi_ca_var,
        kpi_sales,
        kpi_sales_var,
        line,
        bar,
        table.to_dict("records"),
        columns
    )
# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8043, debug=True)