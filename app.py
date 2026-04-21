import os
import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.express as px

# =========================
# 1) Chargement des données
# =========================
df = pd.read_csv("supermarket_sales.csv")

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df.dropna(subset=["Date"]).copy()
df["Week"] = df["Date"].dt.to_period("W").apply(lambda x: x.start_time)

required_columns = [
    "Invoice ID",
    "City",
    "Gender",
    "Product line",
    "Total",
    "Rating",
    "Date"
]

missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    raise ValueError(f"Colonnes manquantes dans le fichier CSV : {missing_columns}")

# =========================
# 2) Traductions / libellés
# =========================
gender_display = {
    "Male": "Homme",
    "Female": "Femme"
}

THEME = {
    "bg": "#F7F2E8",
    "paper": "#FFFDF9",
    "card": "#FFFCF6",
    "header": "#5C1F24",
    "header_2": "#7A2E35",
    "text": "#241A17",
    "muted": "#6B5E57",
    "border": "#E5D9C8",
    "gold": "#B78A3B",
    "jade": "#3E8B7A",
    "ruby": "#8C2F39",
    "blue": "#355C7D"
}

GENDER_COLORS = {
    "Homme": THEME["blue"],
    "Femme": THEME["jade"]
}

CITY_COLORS = {
    "Mandalay": THEME["gold"],
    "Naypyitaw": THEME["jade"],
    "Yangon": THEME["ruby"]
}

# =========================
# 3) Préparation des données
# =========================
# On crée une colonne affichable en français
df["Genre"] = df["Gender"].map(gender_display)

# =========================
# 4) Fonctions utiles
# =========================
def apply_filters(dataframe, selected_gender, selected_city):
    filtered_df = dataframe.copy()

    if selected_gender != "Tous":
        filtered_df = filtered_df[filtered_df["Genre"] == selected_gender]

    if selected_city != "Toutes":
        filtered_df = filtered_df[filtered_df["City"] == selected_city]

    return filtered_df


def format_number_fr(value, decimals=0):
    text = f"{value:,.{decimals}f}"
    return text.replace(",", " ").replace(".", ",")


def format_currency_fr(value):
    return f"{format_number_fr(value, 2)} USD"


def create_empty_figure(message):
    fig = px.scatter()
    fig.update_traces(visible=False)
    fig.update_layout(
        paper_bgcolor=THEME["paper"],
        plot_bgcolor=THEME["paper"],
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 18, "color": THEME["muted"]}
            }
        ],
        margin=dict(l=20, r=20, t=60, b=20)
    )
    return fig


def style_figure(fig):
    fig.update_layout(
        paper_bgcolor=THEME["paper"],
        plot_bgcolor=THEME["paper"],
        font=dict(
            family="Inter, Segoe UI, Arial, sans-serif",
            color=THEME["text"],
            size=14
        ),
        title_font=dict(
            family="Cormorant Garamond, Georgia, serif",
            size=26,
            color=THEME["header"]
        ),
        margin=dict(l=55, r=30, t=80, b=50),
        legend=dict(
            bgcolor="rgba(255,255,255,0)",
            borderwidth=0,
            font=dict(size=12),
            title_text="Genre"
        ),
        hoverlabel=dict(
            bgcolor="#FFF8EE",
            bordercolor=THEME["border"],
            font_size=13,
            font_family="Inter, Segoe UI, Arial, sans-serif",
            font_color=THEME["text"]
        )
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(107,94,87,0.12)",
        linecolor="rgba(107,94,87,0.25)",
        zeroline=False
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(107,94,87,0.12)",
        linecolor="rgba(107,94,87,0.25)",
        zeroline=False
    )

    return fig


def filter_summary_text(gender_value, city_value, n_rows):
    gender_text = "Tous" if gender_value == "Tous" else gender_value
    city_text = "Toutes" if city_value == "Toutes" else city_value
    return f"Genre : {gender_text}   •   Ville : {city_text}   •   {n_rows} lignes"


# =========================
# 5) App Dash
# =========================
font_url = (
    "https://fonts.googleapis.com/css2?"
    "family=Inter:wght@400;500;600;700&"
    "family=Cormorant+Garamond:wght@600;700&display=swap"
)

app = dash.Dash(__name__, external_stylesheets=[font_url])
server = app.server
app.title = "Ventes des supermarchés du Myanmar"

gender_options = [{"label": "Tous", "value": "Tous"}] + [
    {"label": g, "value": g}
    for g in sorted(df["Genre"].dropna().unique())
]

city_options = [{"label": "Toutes", "value": "Toutes"}] + [
    {"label": city, "value": city}
    for city in sorted(df["City"].dropna().unique())
]

# =========================
# 6) Layout
# =========================
app.layout = html.Div(
    className="page",
    children=[

        html.Div(
            className="hero",
            children=[
                html.Div(className="hero-accent-line"),

                html.Div(
                    className="hero-top",
                    children=[
                        html.Div(
                            className="hero-title-block",
                            children=[
                                html.Div("MYANMAR SUPERMARKET SALES", className="hero-tag"),
                                html.H1("Tableau de bord des ventes", className="hero-title"),
                                html.P(
                                    "Analyse interactive des ventes par ville et par genre.",
                                    className="hero-subtitle"
                                )
                            ]
                        )
                    ]
                ),

                html.Div(
                    className="filters-card",
                    children=[
                        html.Div(
                            className="filters-grid",
                            children=[
                                html.Div(
                                    className="filter-item",
                                    children=[
                                        html.Label("Ville", className="filter-label"),
                                        dcc.Dropdown(
                                            id="city-filter",
                                            options=city_options,
                                            value="Toutes",
                                            clearable=False
                                        )
                                    ]
                                ),
                                html.Div(
                                    className="filter-item",
                                    children=[
                                        html.Label("Genre", className="filter-label"),
                                        dcc.Dropdown(
                                            id="gender-filter",
                                            options=gender_options,
                                            value="Tous",
                                            clearable=False
                                        )
                                    ]
                                )
                            ]
                        ),
                        html.Div(id="filters-summary", className="filters-summary")
                    ]
                )
            ]
        ),

        html.Div(
            className="kpi-grid",
            children=[
                html.Div(
                    className="kpi-card",
                    children=[
                        html.Div("Montant total des achats", className="kpi-label"),
                        html.Div(id="kpi-total", className="kpi-value")
                    ]
                ),
                html.Div(
                    className="kpi-card",
                    children=[
                        html.Div("Nombre total d'achats", className="kpi-label"),
                        html.Div(id="kpi-orders", className="kpi-value")
                    ]
                )
            ]
        ),

        html.Div(
            className="charts-grid",
            children=[
                html.Div(
                    className="chart-card",
                    children=[
                        dcc.Graph(
                            id="histogram-chart",
                            config={"displayModeBar": False}
                        )
                    ]
                ),

                html.Div(
                    className="chart-card",
                    children=[
                        dcc.Graph(
                            id="bar-chart",
                            config={"displayModeBar": False}
                        )
                    ]
                ),

                html.Div(
                    className="chart-card wide-card",
                    children=[
                        dcc.Graph(
                            id="line-chart",
                            config={"displayModeBar": False}
                        )
                    ]
                )
            ]
        )
    ]
)

# =========================
# 7) Callback
# =========================
@app.callback(
    Output("filters-summary", "children"),
    Output("kpi-total", "children"),
    Output("kpi-orders", "children"),
    Output("histogram-chart", "figure"),
    Output("bar-chart", "figure"),
    Output("line-chart", "figure"),
    Input("gender-filter", "value"),
    Input("city-filter", "value")
)
def update_dashboard(selected_gender, selected_city):
    filtered_df = apply_filters(df, selected_gender, selected_city)

    if filtered_df.empty:
        empty_fig = create_empty_figure("Aucune donnée disponible pour ce filtre.")
        return (
            filter_summary_text(selected_gender, selected_city, 0),
            "0,00 USD",
            "0",
            empty_fig,
            empty_fig,
            empty_fig
        )

    total_sales = filtered_df["Total"].sum()
    total_orders = filtered_df["Invoice ID"].nunique()

    # Histogramme
    hist_color = None
    hist_color_map = None

    if selected_gender == "Tous" and selected_city == "Toutes":
        hist_color = "Genre"
        hist_color_map = GENDER_COLORS
    elif selected_gender == "Tous":
        hist_color = "Genre"
        hist_color_map = GENDER_COLORS
    elif selected_city == "Toutes":
        hist_color = "City"
        hist_color_map = CITY_COLORS

    fig_hist = px.histogram(
        filtered_df,
        x="Total",
        color=hist_color,
        nbins=18,
        opacity=0.88,
        color_discrete_map=hist_color_map,
        color_discrete_sequence=[THEME["blue"]],
        title="Répartition des montants"
    )
    fig_hist.update_layout(
        xaxis_title="Montant total des achats",
        yaxis_title="Fréquence",
        bargap=0.05,
        title_x=0.02
    )
    style_figure(fig_hist)

    if hist_color == "Genre":
        fig_hist.update_layout(legend_title_text="Genre")
    elif hist_color == "City":
        fig_hist.update_layout(legend_title_text="Ville")

    # Barres
    bar_data = (
        filtered_df.groupby(["City", "Genre"], as_index=False)["Invoice ID"]
        .nunique()
        .rename(columns={"Invoice ID": "Nombre d'achats"})
    )

    fig_bar = px.bar(
        bar_data,
        x="City",
        y="Nombre d'achats",
        color="Genre",
        barmode="group",
        color_discrete_map=GENDER_COLORS,
        title="Nombre d'achats par ville et par genre",
        text="Nombre d'achats"
    )
    fig_bar.update_traces(textposition="outside", cliponaxis=False)
    fig_bar.update_layout(
        xaxis_title="Ville",
        yaxis_title="Nombre d'achats",
        title_x=0.02,
        legend_title_text="Genre"
    )
    style_figure(fig_bar)

    # Courbe
    line_data = (
        filtered_df.groupby(["Week", "City"], as_index=False)["Total"]
        .sum()
        .sort_values("Week")
    )

    fig_line = px.line(
        line_data,
        x="Week",
        y="Total",
        color="City",
        markers=True,
        color_discrete_map=CITY_COLORS,
        title="Évolution hebdomadaire des ventes"
    )
    fig_line.update_traces(line=dict(width=3), marker=dict(size=7))
    fig_line.update_layout(
        xaxis_title="Semaine",
        yaxis_title="Montant total des achats",
        title_x=0.02,
        legend_title_text="Ville"
    )
    style_figure(fig_line)

    return (
        filter_summary_text(selected_gender, selected_city, len(filtered_df)),
        format_currency_fr(total_sales),
        format_number_fr(total_orders, 0),
        fig_hist,
        fig_bar,
        fig_line
    )

# =========================
# 8) Lancement
# =========================
if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8053))
    )