import pandas as pd
import plotly.express as px
import calendar

from dash import Dash, html, dcc, dash_table, Input, Output
import dash_bootstrap_components as dbc








df = pd.read_csv("data.csv")

df = df[['CustomerID','Gender','Location','Product_Category','Quantity','Avg_Price',
         'Transaction_Date','Month','Discount_pct']]

df['CustomerID'] = df['CustomerID'].fillna(0).astype(int)

df['Transaction_Date'] = pd.to_datetime(df['Transaction_Date'])

df['Total_price'] = df['Quantity'] * df['Avg_Price'] * (1 - df['Discount_pct']/100)

df["Week"] = df["Transaction_Date"].dt.isocalendar().week








def calculer_ca(data):
    return round(data["Total_price"].sum(),2)

def nombre_ventes(data):
    return int(data["Quantity"].sum())

def top_categories(data):

    return (
        data.groupby("Product_Category")["Quantity"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )



def evolution_ca(data):

    weekly = (
        data.groupby("Week")["Total_price"]
        .sum()
        .reset_index()
    )

    fig = px.line(
        weekly,
        x="Week",
        y="Total_price",
        markers=True,
        title="Evolution du chiffre d'affaire par semaine"
    )

    fig.update_layout(template="plotly_white")

    return fig



def graph_top_ventes(data):

    top = top_categories(data)

    fig = px.bar(
        top,
        y="Product_Category",
        x="Quantity",
        orientation="h",
        color="Quantity",
        title="Frequence des 10 meilleures ventes"
    )

    fig.update_layout(template="plotly_white")

    return fig







app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])







app.layout = dbc.Container([

    html.H2("ECAP Store Dashboard", style={"marginBottom":30}),

    dbc.Row([

        dbc.Col([
            dcc.Dropdown(
                options=[{"label":i,"value":i} for i in df["Location"].unique()],
                id="zone_filter",
                placeholder="Choisissez une zone"
            )
        ], width=4),

        dbc.Col([
            dcc.Dropdown(
                options=[{"label":calendar.month_name[i],"value":i} for i in range(1,13)],
                id="month_filter",
                placeholder="Choisissez un mois"
            )
        ], width=4)

    ]),

    html.Br(),

    dbc.Row([

        dbc.Col([
            html.H5("Chiffre d'affaire"),
            html.H2(id="ca")
        ], width=3),

        dbc.Col([
            html.H5("Nombre de ventes"),
            html.H2(id="ventes")
        ], width=3)

    ]),

    html.Br(),

    dbc.Row([

        dbc.Col(
            dcc.Graph(id="graph_ca"),
            width=6
        ),

        dbc.Col(
            dcc.Graph(id="graph_top"),
            width=6
        )

    ]),

    html.Br(),

    html.H4("Table des 100 dernières ventes"),

    dash_table.DataTable(
        id="table",
        page_size=10,
        style_table={"overflowX":"auto"},
        style_header={"backgroundColor":"lightgrey","fontWeight":"bold"}
    )

])





@app.callback(

    Output("ca","children"),
    Output("ventes","children"),
    Output("graph_ca","figure"),
    Output("graph_top","figure"),
    Output("table","data"),
    Output("table","columns"),

    Input("zone_filter","value"),
    Input("month_filter","value")

)

def update_dashboard(zone, month):

    data = df.copy()

    if zone:
        data = data[data["Location"]==zone]

    if month:
        data = data[data["Month"]==month]

    ca = calculer_ca(data)
    ventes = nombre_ventes(data)

    fig1 = evolution_ca(data)
    fig2 = graph_top_ventes(data)

    table = data.sort_values("Transaction_Date",ascending=False).head(100)

    return (
        f"{ca:,.0f} $",
        ventes,
        fig1,
        fig2,
        table.to_dict("records"),
        [{"name":i,"id":i} for i in table.columns]
    )



import os

port = int(os.environ.get("PORT", 10000))

app.run(host="0.0.0.0", port=port)

