# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import pandas as pd
import dash
from dash.dependencies import Input, Output, State
import dash_table
import dash_html_components as html
from dash_table.Format import Format, Scheme
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import plotly.graph_objects as go
import sys
import datetime as dt
import pickle
import glob
import json
import dash_daq as daq
from plotly.subplots import make_subplots
import plotly.express as px
from itertools import cycle
import pyodbc
import numpy as np
import time
from collections import namedtuple

# colors
palette = cycle(px.colors.sequential.Rainbow)

import statsmodels.api as sm
from sklearn import metrics


sys.path.append(r"L:\SHARED\PALE\my_python_modules\my_functions")
from my_functions_old import My_date
from functions import (
    import_jbc_models,
    prices_and_curve,
    get_fwd_dates,
    ols_cu_price,
    get_scenaris,
    get_fwd_curve_from_db,
)
from supply_functions import (
    fleet_dev_per_ship,
    orderbook,
    individual_tankers,
    addition,
    demolition,
    scenario_age,
    scenario_constant,
    layout_plotly,
)
from prices_functions import (
    get_index_name,
    get_prices,
    get_unique_index_type,
    get_settlement_date,
    get_source,
    get_unit,
    layout,
    time_serie_to_year,
    seasonality,
    get_prices_and_days,
    layout_contract_analysis,
    seasonality_graph,
    scatter_graph,
    hexa_to_rgb,
    get_fwd_dates_price,
    get_fwd_curve_from_db_price,
    plotly_drawing
)

from regional_supply_functions_new import (
    get_padd,
    get_zones,
    get_ballast_laden,
    make_supply_demand_graph,
    sql_format,
    get_index_name,
    make_balance_graph,
    TonnageList,
    get_unique_index_type,
)


from prices_layout import prices_layout
from vlcc_tool_layout import vlcc_layout
from supply_layout import supply_layout
from arbs_layout import arbs_layout
from regional_supply_layout_new import regional_supply_layout
from eiger_fleet_layout import eiger_fleet_layout
from afra_usgc_layout import afra_usgc_layout
global conn
conn = pyodbc.connect(
   "Driver={SQL Server};"
    "Server=GVASQL19Lis;"
    "Database = Fundamentals;"
    "Trusted_Connection=yes")

today = My_date()
dates = get_fwd_dates().sort_values(by="date", ascending=False).date
max_date = max(dates)


app = dash.Dash(
    __name__, prevent_initial_callbacks=True, suppress_callback_exceptions=True
)
app.title = "Analytics"

# styling the sidebar
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "15rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

# padding for the page content
CONTENT_STYLE = {
    "margin-left": "16rem",
    "margin-right": "2rem",
    "padding": "1rem 1rem",
}

sidebar = html.Div(
    [
        html.Img(src=app.get_asset_url("logo.png"), width="98%"),
        html.Hr(),
        html.P("Freight Analytics", className="lead"),
        dbc.Nav(
            [
                dbc.NavLink("Prices", href="/prices", active="exact"),
                dbc.NavLink("Short-Term Regional Supply", href="/regional", active="exact"),
                #dbc.NavLink("Eiger Fleet Map", href="/eiger_fleet", active="exact"),
                dbc.NavLink("Crude S&D Scenario Tool", href="/crude_s&d", active="exact"),
                dbc.NavLink("Fleet", href="/supply", active="exact"),
                #dbc.NavLink("Arbs - in Dev", href="/Arbs", active="exact"),
                dbc.NavLink("USAF Fundamentals", href="/usgc_afra", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
        html.Hr(),
        html.P("Designed by PALE", style={"align": "center", "color": "lightgrey"}),
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(id="page-content", children=[], style=CONTENT_STYLE)


navbar = dbc.Navbar(
    [
        html.A(
            # Use row and col to control vertical alignment of logo / brand
            dbc.Row(
                [
                    dbc.Col(html.Img(src=app.get_asset_url("logo.png"), height="30px")),
                    dbc.Col(dbc.NavbarBrand("Navbar", className="ml-2")),
                ],
                align="center",
                no_gutters=True,
            ),
            href="https://plot.ly",
        ),
    ],
    color="dark",
    dark=True,
)

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/Arbs":
        return arbs_layout()

    elif pathname == "/crude_s&d":
        return vlcc_layout()

    elif pathname == "/supply":
        return supply_layout()
    elif pathname == "/prices":
        return prices_layout()
    elif pathname == "/regional":
        return regional_supply_layout()
    elif pathname == "/eiger_fleet":
        return eiger_fleet_layout()
    elif pathname == "/usgc_afra":
        return afra_usgc_layout()
    # If the user tries to reach a different page, return a 404 message
    elif pathname == "/":
        return dbc.Jumbotron(
            [html.H1("Shipping Analytics Web App", className="text-danger"), html.Hr()]
        )

    return dbc.Jumbotron(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ]
    )


#######################################################################################################
#                                   SENARIO TOOL                                                     #
######################################################################################################


@app.callback(
    Output("intermediate-value-jbc", "children"), Input("scenario-dropdown", "value")
)
def jsonn(name):
    df_base = get_scenaris()[name].copy()
    df_base.Date = pd.to_datetime(df_base.Date)
    df_base = df_base.round(4)
    return df_base.to_json(orient="split")


#############################
#   update table           #
###########################
@app.callback(
    Output("tab", "children"),
    Input("scenario-dropdown", "value"),
)
def table(name):
    df = get_scenaris()[name].copy()

    df.Date = pd.to_datetime(df.Date)

    df = df.sort_values(by="Date", ascending=False)

    df.Date = df.Date.apply(lambda x: x.strftime("%Y-%m-%d"))
    df = df.round(4)

    return dash_table.DataTable(
        id="d_s-table",
        columns=[
            {"name": ["", "Date"], "id": "Date", "type": "datetime", "editable": False}
        ]
        + [
            {
                "name": ["Demand - MMBL", i],
                "id": i,
                "type": "numeric",
                "format": Format(precision=4, scheme=Scheme.decimal),
            }
            for i in df.columns[1:8]
        ]
        + [
            {
                "name": ["Supply", i],
                "id": i,
                "type": "numeric",
                "format": Format(precision=4, scheme=Scheme.decimal),
            }
            for i in df.columns[8:12]
        ]
        + [
            {
                "name": ["", i],
                "id": i,
                "type": "numeric",
                "format": Format(precision=4, scheme=Scheme.decimal),
            }
            for i in df.columns[12:]
        ],
        data=df.to_dict("records"),
        style_cell_conditional=[
            {"if": {"column_id": "Date"}, "textAlign": "left", "width": "5%"},
        ],
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "rgb(248, 248, 248)"},
        ],
        style_header={
            "backgroundColor": "rgba(255,0,0, 0.5)",
            "fontWeight": "bold",
            "textAlign": "center",
        },
        editable=True,
        sort_action="native",
        sort_mode="single",
        # fixed_rows={'headers': True},
        page_size=14,
        merge_duplicate_headers=True,
    )


# sum on the demand supply df
@app.callback(
    Output("d_s-table", "data"),
    Input("d_s-table", "data_timestamp"),
    State("d_s-table", "data"),
)
def update_columns(timestamp, rows):

    for row in rows:
        try:
            row["ton_day"] = round(
                float(row["AG-Asia"])
                + float(row["AG-Europe"])
                + float(row["AG-US"])
                + float(row["Latam-Asia"])
                + float(row["WAF-Asia"])
                + float(row["Small_flows"]),
                4,
            )

        except:
            row["ton_day"] = "NA"

        try:
            row["Total"] = round(
                float(row["VLCC fleet"])
                - float(row["Storage"])
                - float(row["Sanctions"]),
                4,
            )
        except:
            row["Total"] = "NA"
        try:
            row["cu"] = round(float(row["ton_day"]) / float(row["Total"]), 4)
        except:
            row["cu"] = "NA"
    return rows


# graph diference line
@app.callback(
    Output("graph-cu", "figure"),
    Input("d_s-table", "data"),
    Input("d_s-table", "columns"),
    Input("month-diff-dropdown", "value"),
    Input("rolling-dropdown", "value"),
    Input("intermediate-value-jbc", "children"),
    Input("generic-year", "on"),
    Input("index-name-dropdown", "value"),
    Input("index-type-dropdown", "value"),
)
def display_output_cu(
    rows, columns, value, rolling, json_old, switch, index_name, index_type
):

    df = pd.read_json(json_old, orient="split").copy()
    df.Date = pd.to_datetime(df.Date)
    df.set_index(df.Date, inplace=True)
    df = df.sort_index(ascending=True)
    df = df.merge(
        prices_and_curve(
            index_name=index_name,
            index_type=index_type,
            date="last",
            offset_2020=switch,
        ),
        left_index=True,
        right_index=True,
    )

    df_cu = pd.DataFrame(rows, columns=[c["name"][1] for c in columns])
    df_cu.Date = pd.to_datetime(df_cu.Date)
    df_cu.set_index("Date", inplace=True)
    df_cu = df_cu.sort_index(ascending=True)
    df_cu = df_cu.merge(
        prices_and_curve(
            index_name=index_name,
            index_type=index_type,
            date="last",
            offset_2020=switch,
        ),
        left_index=True,
        right_index=True,
    )

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=df_cu.index,
            y=df_cu.cu,
            name="Adjusted-Model",
            line={"width": 1, "color": "green"},
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df[: today.string].Date,
            y=df[: today.string].cu,
            name="Litasco Model CU - Actual",
            line={"width": 2, "color": "red"},
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df[today.string :].index,
            y=df[today.string :].cu,
            name="Litasco CU Model-FWD",
            line={"width": 2, "color": "red"},
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df[index_name],
            name=index_name,
            line={"width": 2, "color": "black"},
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title={"text": "VLCC CU Model", "font": {"size": 14}},
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=30, r=10, b=30, t=30, pad=4),
    )

    # fig.add_trace(
    #   go.Scatter(
    #      x=plot_new.index,
    #     y=plot_new.TD3_eiger_forecast,
    #     name="Adjusted Model",
    #    line={"width": 2, "color": "green"},
    # )
    # )

    return fig


#######################
# Scatter plot        #
######################
@app.callback(
    Output("graph-scatter", "figure"),
    Input("d_s-table", "data"),
    Input("d_s-table", "columns"),
    Input("month-diff-dropdown", "value"),
    Input("rolling-dropdown", "value"),
    Input("fwd-curves-dropdown", "value"),
    Input("generic-year", "on"),
    Input("index-name-dropdown", "value"),
    Input("index-type-dropdown", "value"),
)
def display_output_sct(
    rows, columns, value, rolling, dates, switch, index_name, index_type
):
    dates_db = get_fwd_dates().sort_values(by="date", ascending=False).date
    max_date = max(dates_db)

    df_cu = pd.DataFrame(rows, columns=[c["name"][1] for c in columns])
    df_cu.Date = pd.to_datetime(df_cu.Date)
    df_cu.set_index("Date", inplace=True)
    df_cu = df_cu.sort_index(ascending=True)
    # df_cu.to_csv('why.csv')

    df_cu = df_cu.merge(
        prices_and_curve(
            index_name=index_name,
            index_type=index_type,
            date="last",
            offset_2020=switch,
        ),
        left_index=True,
        right_index=True,
    )

    temp1 = (
        +df_cu[["cu", index_name]]
        - df_cu[["cu", index_name]].shift(value).rolling(rolling).mean()
    )
    if rolling != 1:
        temp1 = (
            +df_cu[["cu", index_name]]
            - df_cu[["cu", index_name]].shift(value).rolling(rolling).mean()
        )
    # temp1.to_csv('why.csv')
    # plot = dic_models["kpler_flow_reg"].predict(sm.add_constant(temp1.cu))
    plot, r2 = ols_cu_price(temp1.copy(), index_name=index_name)
    plot.name = "index_name" + "-forecast"
    plot = temp1[["cu"]].merge(plot, left_index=True, right_index=True)

    labels = pd.date_range(
        start=temp1[today.string :].index[1],
        periods=len(temp1[today.string :].index),
        freq="M",
    )
    labels = [
        x.strftime("%b-%Y") + " M" + str(i + 1) for i, x in enumerate(labels.date)
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=temp1[: today.string].cu,
            y=temp1[: today.string][index_name],
            name=index_name + " Price Difference",
            mode="markers",
            marker={"symbol": "circle", "size": 8, "color": "black"},
            text=temp1[: today.string].index.date,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=temp1[today.string :].cu,
            y=temp1[today.string :][index_name],
            name=index_name + " Price Difference - Last",
            mode="markers",
            marker={"symbol": "circle-open", "size": 10, "color": "black"},
            text=labels,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=plot.cu,
            y=plot["index_name" + "-forecast"],
            text=temp1.index.date,
            name="Litasco Price Difference Model",
            mode="lines",
            line={"color": "red"},
        )
    )

    fig.update_layout(
        title={
            "text": index_name + " Price Difference Forecast vs CU(%) difference",
            "font": {"size": 14},
        },
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=-0.02, xanchor="right", x=1),
        margin=dict(l=30, r=10, b=50, t=30, pad=4),
    )

    if dates != max_date:
        for dte in [x for x in dates if x != max_date]:
            df_cu_bis = df_cu.drop(columns=index_name)
            df_cu_bis = df_cu_bis.merge(
                prices_and_curve(
                    index_name=index_name,
                    index_type=index_type,
                    date=dte,
                    offset_2020=switch,
                ),
                left_index=True,
                right_index=True,
            )
            df_cu_bis = df_cu_bis.sort_index(ascending=True)
            if rolling != 1:
                temp2 = (
                    +df_cu_bis[["cu", index_name]]
                    - df_cu_bis[["cu", index_name]].shift(value).rolling(rolling).mean()
                )
            else:
                temp2 = +df_cu_bis[["cu", index_name]] - df_cu_bis[
                    ["cu", index_name]
                ].shift(value)
            labels = get_fwd_curve_from_db(index_name, date=dte).sort_values(
                by="settlement_date"
            )
            labels.settlement_date = pd.to_datetime(labels.settlement_date)
            # labels = [x.strftime('%b-%Y')+' M'+str(i+1) for i, x in enumerate(labels.date)]
            labels = [
                x.strftime("%b-%Y") + " M" + str(i + 1)
                for i, x in enumerate(labels.settlement_date)
            ]

            fig.add_trace(
                go.Scatter(
                    x=temp2[today.string :].cu,
                    y=temp2[today.string :][index_name],
                    name=dte,
                    mode="markers",
                    marker={"symbol": "circle", "size": 8, "color": next(palette)},
                    text=labels,
                )
            )

    return fig


# R2
@app.callback(
    Output("r2", "children"),
    Input("d_s-table", "data"),
    Input("d_s-table", "columns"),
    Input("month-diff-dropdown", "value"),
    Input("rolling-dropdown", "value"),
    Input("generic-year", "on"),
    Input("index-name-dropdown", "value"),
    Input("index-type-dropdown", "value"),
)
def r2(rows, columns, value, rolling, switch, index_name, index_type):

    df_cu = pd.DataFrame(rows, columns=[c["name"][1] for c in columns])
    df_cu.Date = pd.to_datetime(df_cu.Date)
    df_cu.set_index("Date", inplace=True)
    df_cu = df_cu.sort_index(ascending=True)
    # df_cu.to_csv('why.csv')
    df_cu = df_cu.merge(
        prices_and_curve(
            index_name=index_name,
            index_type=index_type,
            date="last",
            offset_2020=switch,
        ),
        left_index=True,
        right_index=True,
    )
    df_cu = df_cu.sort_index(ascending=True)
    temp1 = +df_cu[["cu", index_name]] - df_cu[["cu", index_name]].shift(value)
    plot, r2 = ols_cu_price(temp1.copy(), index_name=index_name)
    if rolling != 1:
        temp1 = (
            +df_cu[["cu", index_name]]
            - df_cu[["cu", index_name]].shift(value).rolling(rolling).mean()
        )
        # temp1.to_csv('test.csv')
        rr = temp1.copy()
        plot, r2 = ols_cu_price(rr, index_name=index_name)

    # plot = dic_models["kpler_flow_reg"].predict(sm.add_constant(temp1.cu))

    return "R2: " + str(round(r2, 3))


# saved scenario
@app.callback(
    Output("hidden", "children"),
    Input("save-button", "submit_n_clicks"),
    Input("d_s-table", "data"),
    Input("d_s-table", "columns"),
)
def save_csv(submit_n_clicks, rows, columns):
    if submit_n_clicks:

        df_cu = pd.DataFrame(rows, columns=[c["name"][1] for c in columns])
        df_cu.to_csv(
            r"\\gvaps1\DATAROOT\data\SHARED\PALE\Dash\saved_scenario\last_scenario_csv.csv"
        )


#######################################################################################################
#                                   SUPPLY SHEET                                                      #
######################################################################################################

# change ships options
@app.callback(
    Output("ship-dropdown", "options"),
    Input("clean-dropdown", "value"),
    Input("hidden-div", "children"),
)
def ship_options(value, json_data):
    df = pd.read_json(json.loads(json_data[0])[value]["fleet_dev"][0])

    options = [
        {"label": x.replace("_mbbl", "").upper(), "value": x.replace("_mbbl", "")}
        for x in df.columns
        if x != "state"
    ]

    return options


# change ships value
@app.callback(
    Output("ship-dropdown", "value"),
    Input("clean-dropdown", "value"),
)
def ship_value(clean):

    if clean:
        return "total"


# change slider values


@app.callback(
    Output("my-slider", "children"),
    Input("clean-dropdown", "value"),
    Input("ship-dropdown", "value"),
    Input("mbbl-button", "value"),
    Input("hidden-div", "children"),
)
def slider_value(clean, ship, mbbl, json_data):

    ## fetch the right element of the tuple
    if mbbl == "mbbl":
        dummy = 0
    else:
        dummy = 1

    unit = mbbl
    ship_type = ship + "_" + unit

    df = pd.read_json(json.loads(json_data[0])[clean]["demolition"][dummy])
    if ship == "total":
        marks = {
            str(round(df[ship_type].mean(), 2)): "Mean",
            str(round(df[ship_type].quantile(0.5), 2)): "2-Q",
            str(round(df[ship_type].quantile(0.75), 2)): "3-Q",
        }
    else:
        marks = {
            str(round(df[ship_type].mean(), 2)): "Mean",
            str(round(df[ship_type].quantile(0.5), 2)): "2-Q",
            str(round(df[ship_type].quantile(0.75), 2)): "3-Q",
        }

    child = daq.Slider(
        id="constant-slider",
        min=0,
        max=df[ship_type].mean() * 3,
        value=round(df[ship_type].mean(), 2),
        handleLabel={"showCurrentValue": True, "label": "Value"},
        marks=marks,
        step=0.1,
        size=250,
    )
    return child


###################################
#         Demolition graph        #
###################################
@app.callback(
    Output("graph-demo", "figure"),
    Input("clean-dropdown", "value"),
    Input("ship-dropdown", "value"),
    Input("mbbl-button", "value"),
    Input("hidden-div", "children"),
)
def demo_graph(clean, ship, mbbl, json_data):

    ## fetch the right element of the tuple
    if mbbl == "mbbl":
        dummy = 0
    else:
        dummy = 1

    df = pd.read_json(json.loads(json_data[0])[clean]["demolition"][dummy])

    unit = mbbl
    unit_u = unit.upper()
    ship_type = ship + "_" + unit

    if clean == "crude":
        clean_allias = "Dirty"
    else:
        clean_allias = "Clean"

    fig_demo = go.Figure()

    fig_demo.add_trace(
        go.Scatter(
            x=df.index,
            y=df[ship_type],
            name="Demolition - " + unit_u,
            mode="lines",
            line={"width": 1, "color": "DodgerBlue"},
            # fill='toself'
        )
    )

    fig_demo.add_trace(
        go.Scatter(
            x=df.index,
            y=df[ship_type].rolling(window=24).quantile(0.25),
            name="25% - Quantile",
            line={
                "width": 1,
                "color": "grey",
            },
        )
    )
    fig_demo.add_trace(
        go.Scatter(
            x=df.index,
            y=df[ship_type].rolling(window=24).quantile(0.75),
            name="75% - Quantile",
            line={"width": 1, "color": "grey"},
            fill="tonexty",
        )
    )

    fig_demo.add_trace(
        go.Scatter(
            x=df.index,
            y=df[ship_type].rolling(window=24).quantile(0.5),
            name="24-Month rolling Median",
            line={"width": 2, "color": "black", "dash": "dot"},
        )
    )

    fig_demo.update_layout(
        template="ggplot2",
        title={
            "text": "<b>{} - {} Demolition in {}<b>".format(
                ship.upper(), clean_allias, unit_u
            ),
            "font": {"size": 14},
            "x": 0.5,
        },
        # template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="left", x=0),
        margin=dict(l=30, r=10, b=50, t=30, pad=4),
    )

    return fig_demo


#########################################
#            ADDTION graph              #
#########################################
@app.callback(
    Output("graph-add", "figure"),
    Input("clean-dropdown", "value"),
    Input("ship-dropdown", "value"),
    Input("mbbl-button", "value"),
    Input("hidden-div", "children"),
)
def addition_graph(clean, ship, mbbl, json_data):

    ## fetch the right element of the tuple
    if mbbl == "mbbl":
        dummy = 0
    else:
        dummy = 1

    df = pd.read_json(json.loads(json_data[0])[clean]["addition"][dummy])
    df.fillna(0, inplace=True)
    unit = mbbl
    unit_u = unit.upper()
    ship_type = ship + "_" + unit

    if clean == "crude":
        clean_allias = "Dirty"
    else:
        clean_allias = "Clean"

    fig_add = go.Figure()

    fig_add.add_trace(
        go.Scatter(
            x=df[df.state == "deliveries"].index,
            y=df[df.state == "deliveries"][ship_type],
            name="Deliveries - " + unit_u,
            mode="lines",
            line={"width": 1, "color": "DodgerBlue"},
            # fill='toself'
        )
    )

    fig_add.add_trace(
        go.Scatter(
            x=df[df.state == "orderbook"].index,
            y=df[df.state == "orderbook"][ship_type],
            name="orderbook - " + unit_u,
            mode="lines",
            line={"width": 2, "color": "firebrick"},
            # fill='toself'
        )
    )

    fig_add.add_trace(
        go.Scatter(
            x=df.index,
            y=df[ship_type].rolling(window=24).quantile(0.25),
            name="25% - Quantile",
            line={
                "width": 1,
                "color": "grey",
            },
        )
    )
    fig_add.add_trace(
        go.Scatter(
            x=df.index,
            y=df[ship_type].rolling(window=24).quantile(0.75),
            name="75% - Quantile",
            line={"width": 1, "color": "grey"},
            fill="tonexty",
        )
    )

    fig_add.add_trace(
        go.Scatter(
            x=df.index,
            y=df[ship_type].rolling(window=24).quantile(0.5),
            name="24-Month rolling Median",
            line={"width": 2, "color": "black", "dash": "dot"},
        )
    )

    fig_add.update_layout(
        template="ggplot2",
        title={
            "text": "<b>{} - {} Deliveries+Orderbook in {}<b>".format(
                ship.upper(), clean_allias, unit_u
            ),
            "font": {"size": 14},
            "x": 0.5,
        },
        # template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="left", x=0),
        margin=dict(l=30, r=10, b=50, t=30, pad=4),
    )

    return fig_add


# save sceanrio change in hidden div
@app.callback(
    Output("hidden-div-sce", "children"),
    Input("clean-dropdown", "value"),
    Input("mbbl-button", "value"),
    Input("age-dropdown", "value"),
    Input("hidden-div", "children"),
)
def hidden_scenario(clean, mbbl, age, json_data):

    ## fetch the right element of the tuple
    if mbbl == "mbbl":
        dummy = 0
    else:
        dummy = 1

    df = pd.read_json(json.loads(json_data[0])[clean]["individual_tankers"][dummy])

    dic_sce = scenario_age(df, age)
    return json.dumps({k: v.to_json() for k, v in dic_sce.items()})


##########################
#       Scenario         #
##########################


@app.callback(
    Output("graph-sce", "figure"),
    Input("clean-dropdown", "value"),
    Input("mbbl-button", "value"),
    Input("ship-dropdown", "value"),
    Input("hidden-div", "children"),
    Input("hidden-div-sce", "children"),
    Input("constant-slider", "value"),
)
def graph_sce(clean, mbbl, ship, json_data, sce_data, constant):

    if mbbl == "mbbl":
        dummy = 0
    else:
        dummy = 1

    unit = mbbl
    unit_u = unit.upper()
    ship_type = ship + "_" + unit
    if clean == "crude":
        clean_allias = "Dirty"
    else:
        clean_allias = "Clean"

    crude_fleet_mbbl = pd.read_json(json.loads(json_data[0])[clean]["fleet_dev"][dummy])
    orderbook_mbbl = pd.read_json(json.loads(json_data[0])[clean]["orderbook"][dummy])

    orderbook_mbbl.index = pd.DatetimeIndex(orderbook_mbbl.index)
    orderbook_mbbl.fillna(0, inplace=True)
    # crude_fleet_mbbl.index = pd.to_datetime(crude_fleet_mbbl.index)

    fig_sce = go.Figure()
    dic_sce = json.loads(sce_data)

    x = scenario_constant(crude_fleet_mbbl, orderbook_mbbl, constant)

    fig_sce.add_trace(
        go.Scatter(
            x=crude_fleet_mbbl.index,
            y=crude_fleet_mbbl[ship_type],
            name="Fleet Development - " + unit_u,
            mode="lines",
            line={"width": 2, "color": "DodgerBlue"},
            # fill='tozeroy'
        )
    )

    l = []
    for k, v in dic_sce.items():
        l.append(k)
        if len(l) > 1:
            f = "tonexty"
            # f = None
        else:
            f = None

        v = pd.read_json(v)

        s = v.copy()
        s.index = pd.DatetimeIndex(s.index)

        scenario = (orderbook_mbbl.resample("M").mean().cumsum() - s).dropna(
            subset=["total_" + unit]
        )

        scenario.iloc[0] = 0
        fig_sce.add_trace(
            go.Scatter(
                x=scenario.index,
                y=scenario[ship_type] + crude_fleet_mbbl[ship_type][-1],
                name="Scrapping scenario " + str(k) + "Y",
                line={"width": 3, "dash": "dot"},
                fill=f,
            )
        )

    fig_sce.add_trace(
        go.Scatter(
            x=x.index,
            y=x[ship_type],
            name="Constant scenario",
            mode="lines",
            line={"width": 3, "dash": "dot", "color": "red"},
            # fill='tozeroy'
        )
    )

    fig_sce.update_layout(
        template="ggplot2",
        title={
            "text": "<b>{} - {} Fleet Development in {}<b>".format(
                ship.upper(), clean_allias, unit_u
            ),
            "font": {"size": 14},
            "x": 0.5,
        },
        # template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=0.93, xanchor="left", x=0),
        margin=dict(l=30, r=10, b=30, t=30, pad=4),
    )

    return fig_sce


# saved aupply
@app.callback(
    Output("hidden-supply", "children"),
    Input("save-button", "submit_n_clicks"),
    Input("graph-sce", "figure"),
)
def save_csv_supply(submit_n_clicks, fig_sce):
    if submit_n_clicks:

        l = []
        for el in fig_sce["data"]:
            if el["name"].find("scenario") > 0:
                l.append(
                    pd.DataFrame(index=el["x"], data=el["y"], columns=[el["name"]])
                )
        save = pd.concat(l, join="inner", axis=1)
        save.to_csv(
            r"\\gvaps1\DATAROOT\data\SHARED\PALE\Dash\saved_supply\last_supply_scenario.csv"
        )


##############################
#     Yearly Graph Bar chart #
#############################
@app.callback(
    Output("graph-yearly", "figure"),
    Input("clean-dropdown", "value"),
    Input("mbbl-button", "value"),
    Input("hidden-div", "children"),
)
def yearly_graph(clean, mbbl, json_data):

    ## fetch the right element of the tuple
    if mbbl == "mbbl":
        dummy = 0
    else:
        dummy = 1

    df = pd.read_json(json.loads(json_data[0])[clean]["fleet_dev"][dummy])
    # df.to_csv('testdfdf.csv')
    df.index = pd.to_datetime(df.index)
    yearly_fleet = df.copy()

    yearly_fleet["year"] = yearly_fleet.index.year
    yearly_fleet = yearly_fleet.groupby("year").last()
    # yearly_fleet.to_csv('test.csv')
    palette = cycle(px.colors.qualitative.D3)

    if clean == "crude":
        if mbbl == "mbbl":
            data = [
                go.Bar(
                    name="VLCC",
                    x=yearly_fleet.index,
                    y=yearly_fleet.VLCC_mbbl,
                    marker_color=next(palette),
                ),
                go.Bar(
                    name="Suezmax",
                    x=yearly_fleet.index,
                    y=yearly_fleet.suezmax_mbbl,
                    marker_color=next(palette),
                ),
                go.Bar(
                    name="Aframax",
                    x=yearly_fleet.index,
                    y=yearly_fleet.aframax_mbbl,
                    marker_color=next(palette),
                ),
                go.Bar(
                    name="Panamax",
                    x=yearly_fleet.index,
                    y=yearly_fleet.panamax_mbbl,
                    marker_color=next(palette),
                ),
                # go.Bar(name='Total', x=yearly_fleet.index, y=yearly_fleet.total_no, marker_color=next(palette))
            ]
        else:
            data = [
                go.Bar(
                    name="VLCC",
                    x=yearly_fleet.index,
                    y=yearly_fleet.VLCC_no,
                    marker_color=next(palette),
                ),
                go.Bar(
                    name="Suezmax",
                    x=yearly_fleet.index,
                    y=yearly_fleet.suezmax_no,
                    marker_color=next(palette),
                ),
                go.Bar(
                    name="Aframax",
                    x=yearly_fleet.index,
                    y=yearly_fleet.aframax_no,
                    marker_color=next(palette),
                ),
                go.Bar(
                    name="Panamax",
                    x=yearly_fleet.index,
                    y=yearly_fleet.panamax_no,
                    marker_color=next(palette),
                ),
                # go.Bar(name='Total', x=yearly_fleet.index, y=yearly_fleet.total_no, marker_color=next(palette))
            ]
        fig_yearly_graph = go.Figure(data=data)
        fig_yearly_graph = layout_plotly(
            fig_yearly_graph, "Dirty Fleet Development", template="ggplot2"
        )

    else:

        if mbbl == "mbbl":
            data = [
                go.Bar(
                    name="Suezmax",
                    x=yearly_fleet.index,
                    y=yearly_fleet.suezmax_mbbl,
                    marker_color=next(palette),
                ),
                go.Bar(
                    name="Aframax",
                    x=yearly_fleet.index,
                    y=yearly_fleet.aframax_mbbl,
                    marker_color=next(palette),
                ),
                go.Bar(
                    name="Panamax",
                    x=yearly_fleet.index,
                    y=yearly_fleet.panamax_mbbl,
                    marker_color=next(palette),
                ),
                go.Bar(
                    name="MR",
                    x=yearly_fleet.index,
                    y=yearly_fleet.MR_mbbl,
                    marker_color=next(palette),
                ),
                go.Bar(
                    name="Handy",
                    x=yearly_fleet.index,
                    y=yearly_fleet.handy_mbbl,
                    marker_color=next(palette),
                ),
            ]
        else:
            data = [
                go.Bar(
                    name="Suezmax",
                    x=yearly_fleet.index,
                    y=yearly_fleet.suezmax_no,
                    marker_color=next(palette),
                ),
                go.Bar(
                    name="Aframax",
                    x=yearly_fleet.index,
                    y=yearly_fleet.aframax_no,
                    marker_color=next(palette),
                ),
                go.Bar(
                    name="Panamax",
                    x=yearly_fleet.index,
                    y=yearly_fleet.panamax_no,
                    marker_color=next(palette),
                ),
                go.Bar(
                    name="MR",
                    x=yearly_fleet.index,
                    y=yearly_fleet.MR_no,
                    marker_color=next(palette),
                ),
                go.Bar(
                    name="Handy",
                    x=yearly_fleet.index,
                    y=yearly_fleet.handy_no,
                    marker_color=next(palette),
                ),
            ]
        fig_yearly_graph = go.Figure(data=data)
        fig_yearly_graph = layout_plotly(
            fig_yearly_graph, "Clean Fleet Development", template="ggplot2"
        )

    return fig_yearly_graph


####################################################################################################################
#                                       PRICE SHEET                                                                 #
##################################################################################################################
##############################
#           Row 1 dropdown   #
#############################


# Index_type dropdown
@app.callback(
    Output("index-type-dropdown-1", "options"),
    Input("index-name-dropdown-1", "value"),
)
def index_type_1(value):

    with conn:
        index = [{"label": x, "value": x} for x in get_unique_index_type(conn, value)]
        month = [{"label": x, "value": x} for x in get_settlement_date(conn, value)]
        # if len(month)>5:
        #    Q = [{"label": x, "value": x} for x in ['Q1', 'Q2', 'Q3', 'Q4']]
        # else:
        #    Q=[]
    return index + month


# source dropdown
@app.callback(
    Output("source-dropdown-1", "options"),
    Input("index-type-dropdown-1", "value"),
    State("index-name-dropdown-1", "value"),
)
def source_1(index_type, index_name):

    if index_type == [] or index_name == []:
        return []
    else:
        with conn:
            source = [
                {"label": x, "value": x}
                for x in get_source(conn, index_name, index_type)
            ]

        return source


# unit dropdown
@app.callback(
    Output("unit-dropdown-1", "options"),
    Input("source-dropdown-1", "value"),
    State("index-type-dropdown-1", "value"),
    State("index-name-dropdown-1", "value"),
)
def unit_1(source, index_type, index_name):

    if source == [] or index_type == [] or index_name == []:
        return []
    else:
        with conn:
            unit = [
                {"label": x, "value": x}
                for x in get_unit(conn, index_name, index_type, source)
            ]

        return unit


##############################
#           Row 2 dropdown   #
#############################


# Index_type dropdown
@app.callback(
    Output("index-type-dropdown-2", "options"),
    Input("index-name-dropdown-2", "value"),
)
def index_type_2(value):

    with conn:
        index = [{"label": x, "value": x} for x in get_unique_index_type(conn, value)]
        month = [{"label": x, "value": x} for x in get_settlement_date(conn, value)]

    return index + month


# source dropdown
@app.callback(
    Output("source-dropdown-2", "options"),
    Input("index-type-dropdown-2", "value"),
    State("index-name-dropdown-2", "value"),
)
def source_2(index_type, index_name):

    if index_type == [] or index_name == []:
        return []
    else:
        with conn:
            source = [
                {"label": x, "value": x}
                for x in get_source(conn, index_name, index_type)
            ]

        return source


# unit dropdown
@app.callback(
    Output("unit-dropdown-2", "options"),
    Input("source-dropdown-2", "value"),
    State("index-type-dropdown-2", "value"),
    State("index-name-dropdown-2", "value"),
)
def unit_2(source, index_type, index_name):

    if source == [] or index_type == [] or index_name == []:
        return []
    else:
        with conn:
            unit = [
                {"label": x, "value": x}
                for x in get_unit(conn, index_name, index_type, source)
            ]

        return unit
    

##############################
#           Row 3 dropdown   #
#############################


# Index_type dropdown
@app.callback(
    Output("index-type-dropdown-3", "options"),
    Input("index-name-dropdown-3", "value"),
)
def index_type_3(value):

    with conn:
        index = [{"label": x, "value": x} for x in get_unique_index_type(conn, value)]
        month = [{"label": x, "value": x} for x in get_settlement_date(conn, value)]

    return index + month


# source dropdown
@app.callback(
    Output("source-dropdown-3", "options"),
    Input("index-type-dropdown-3", "value"),
    State("index-name-dropdown-3", "value"),
)
def source_3(index_type, index_name):

    if index_type == [] or index_name == []:
        return []
    else:
        with conn:
            source = [
                {"label": x, "value": x}
                for x in get_source(conn, index_name, index_type)
            ]

        return source


# unit dropdown
@app.callback(
    Output("unit-dropdown-3", "options"),
    Input("source-dropdown-3", "value"),
    State("index-type-dropdown-3", "value"),
    State("index-name-dropdown-3", "value"),
)
def unit_3(source, index_type, index_name):

    if source == [] or index_type == [] or index_name == []:
        return []
    else:
        with conn:
            unit = [
                {"label": x, "value": x}
                for x in get_unit(conn, index_name, index_type, source)
            ]

        return unit


###########################
#       dropdown slider   #
###########################
@app.callback(
    Output("slider-dropdown", "options"),
    # Output('test', 'children'),
    Input("my-slider", "value"),
    State("unit-dropdown-1", "value"),
    State("unit-dropdown-2", "value"),
    State("unit-dropdown-3", "value"),
    State("source-dropdown-1", "value"),
    State("index-type-dropdown-1", "value"),
    State("index-name-dropdown-1", "value"),
    State("source-dropdown-2", "value"),
    State("index-type-dropdown-2", "value"),
    State("index-name-dropdown-2", "value"),
    State("source-dropdown-3", "value"),
    State("index-type-dropdown-3", "value"),
    State("index-name-dropdown-3", "value"),
)
def dropbox_slider(
    value,
    unit1,
    unit2,
    unit3,
    source1,
    index_type1,
    index_name1,
    source2,
    index_type2,
    index_name2,
    source3,
    index_type3,
    index_name3,
):

    if value in [3, 5, 7, 9]:
        time.sleep(1)
        try:
            price1 = get_prices(
                conn=conn,
                index_name=index_name1,
                index_type=index_type1,
                source=source1,
                unit=unit1,
            )
            y1 = list(price1.index.year.unique())
        except:
            y1 = []
            price1 = pd.DataFrame()

        try:
            price2 = get_prices(
                conn=conn,
                index_name=index_name2,
                index_type=index_type2,
                source=source2,
                unit=unit2,
            )
            y2 = list(price2.index.year.unique())
        except:
            y2 = []
            price2 = pd.DataFrame()
            
        try:
            price3 = get_prices(
                conn=conn,
                index_name=index_name3,
                index_type=index_type3,
                source=source3,
                unit=unit3,
            )
            y3 = list(price3.index.year.unique())
        except:
            y3 = []
            price3 = pd.DataFrame()     


        l = sorted(set(y1 + y2 + y3))
        options = [{"label": str(x), "value": x} for x in l]
        return options
    elif value == 11:
        months = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
        val = list(range(1, 13))
        val = list(zip(months, val))
        options = [{"label": x[0], "value": x[1]} for x in val]
        return options
    else:
        return []


##########################
#   Graphs Histo       #
########################


@app.callback(
    Output("graph-html", "children"),
    # Output('test', 'children'),
    Input("graph-button", "n_clicks"),
    Input("my-slider", "value"),
    State("unit-dropdown-1", "value"),
    State("unit-dropdown-2", "value"),
    State("unit-dropdown-3", "value"),
    State("source-dropdown-1", "value"),
    State("index-type-dropdown-1", "value"),
    State("index-name-dropdown-1", "value"),
    State("source-dropdown-2", "value"),
    State("index-type-dropdown-2", "value"),
    State("index-name-dropdown-2", "value"),
    State("source-dropdown-3", "value"),
    State("index-type-dropdown-3", "value"),
    State("index-name-dropdown-3", "value"),
    State("slider-dropdown", "value")
    # State("graph-histo", "figure")
)
def graph_histo(
    n,
    graph_type,
    unit1,
    unit2,
    unit3,
    source1,
    index_type1,
    index_name1,
    source2,
    index_type2,
    index_name2,
    source3,
    index_type3,
    index_name3,
    slct_years,
):
    if slct_years == []:
        slct_years = None

    try:
        if n is not None:
            try:
                price1 = get_prices(
                    conn=conn,
                    index_name=index_name1,
                    index_type=index_type1,
                    source=source1,
                    unit=unit1,
                )
            except:
                price1 = pd.DataFrame()

            try:
                price2 = get_prices(
                    conn=conn,
                    index_name=index_name2,
                    index_type=index_type2,
                    source=source2,
                    unit=unit2,
                )
            except:
                index_name2 = ''
                price2 = pd.DataFrame()
            try:
                price3 = get_prices(
                    conn=conn,
                    index_name=index_name3,
                    index_type=index_type3,
                    source=source3,
                    unit=unit3,
                )
            except:
                price3 = pd.DataFrame()

            # historic graph
            if graph_type == 1:
                
                # to create the secondary_y axis
                if len(set([x for x in [unit1, unit2, unit3] if x is not None])) > 1:
                    dummy = True
                else:
                    dummy = False

                fig = make_subplots(specs=[[{"secondary_y": True}]])

                try:
                    if unit1 == "WS":
                        u = "WS"
                    else:
                        u = "$"
                    for el in price1.columns:
                        fig.add_trace(
                            go.Scatter(
                                x=price1.index,
                                y=price1[el],
                                name=el,
                                mode="lines",
                                line={"width": 1},
                                connectgaps=True,
                                hovertemplate="<br><b>Date</b>: %{x|%B %d, %Y}"
                                + "<br><b>Value</b>: "
                                + str(u)
                                + " %{y}<br>",
                            )
                        )

                except:
                    pass

                try:
                    if unit2 == "WS":
                        u = "WS"
                    else:
                        u = "$"
                    for el in price2.columns:
                        fig.add_trace(
                            go.Scatter(
                                x=price2.index,
                                y=price2[el],
                                name=el,
                                mode="lines",
                                line={"width": 1},
                                connectgaps=True,
                                hovertemplate="<br><b>Date</b>: %{x|%B %d, %Y}"
                                + "<br><b>Value</b>: "
                                + str(u)
                                + " %{y}<br>",
                            ),
                            secondary_y=dummy,
                        )
                except:
                    pass

                try:
                    if unit2 == "WS":
                        u = "WS"
                    else:
                        u = "$"
                    for el in price3.columns:
                        fig.add_trace(
                            go.Scatter(
                                x=price3.index,
                                y=price3[el],
                                name=el,
                                mode="lines",
                                line={"width": 1},
                                connectgaps=True,
                                hovertemplate="<br><b>Date</b>: %{x|%B %d, %Y}"
                                + "<br><b>Value</b>: "
                                + str(u)
                                + " %{y}<br>",
                            ),
                            secondary_y=dummy,
                        )
                except:
                    pass
                if index_name2==None: index_name2=''
                if index_name3==None: index_name3=''
                if index_name1==None: index_name1=''
                fig, config = plotly_drawing(layout(fig, index_name1,index_name2, index_name3))
                
                
                return dcc.Graph(figure=fig, config=config)

            # seasonal monthly
            elif graph_type == 5:
                price = pd.concat([price1, price2, price3], axis=1)
                
                if index_type1[0]=='cash':
                    fwd = get_fwd_curve_from_db_price(conn, index_name=index_name1)
                    fwd = fwd[fwd.index_type!='cash'][['value', 'settlement_date']]
                    fwd.settlement_date = pd.to_datetime(fwd.settlement_date)
                    fwd = fwd.set_index('settlement_date')
                    f = seasonality(fwd, seasonality_period='month')
                else:
                    f=None
                data, years = seasonality(
                    price, seasonality_period="month", selected_years=slct_years
                )
                fig, config = plotly_drawing(
                    seasonality_graph(
                    data=data, years=years, seasonality="month", index_name=index_name1, 
                    fwd_tuple=f
                    )
                )
                return dcc.Graph(figure=fig, config=config )

            # seasonal weekly
            elif graph_type == 7:
                price = pd.concat([price1, price2, price3], axis=1)
                data, years = seasonality(
                    price, seasonality_period="week", selected_years=slct_years
                )
                fig, config = plotly_drawing(
                    seasonality_graph(
                    data=data, years=years, index_name=index_name1, seasonality="week"
                    )
                )
                return dcc.Graph(figure=fig, config=config)

            # seasonal quarter
          
            elif graph_type == 3:
                
                try:
                    p1 = get_prices_and_days(
                        conn=conn,
                        index_name=index_name1,
                        index_type=index_type1,
                        source=source1,
                        unit=unit1,
                    )
                except:
                    p1 = pd.DataFrame()

                try:
                    p2 = get_prices_and_days(
                        conn=conn,
                        index_name=index_name2,
                        index_type=index_type2,
                        source=source2,
                        unit=unit2,
                    )
                except:
                    p2 = pd.DataFrame()
                try:
                    p3 = get_prices_and_days(
                        conn=conn,
                        index_name=index_name3,
                        index_type=index_type3,
                        source=source3,
                        unit=unit3,
                    )
                except:
                    p3 = pd.DataFrame()

                
           
                # to create the secondary_y axis
                if len(set([x for x in [unit1, unit2, unit3] if x is not None])) > 1:
                    dummy = True
                else:
                    dummy = False

                fig = make_subplots(specs=[[{"secondary_y": True}]])

                try:

                    for el in p1.columns:
                        fig.add_trace(
                            go.Scatter(
                                x=p1.index,
                                y=p1[el],
                                name=el,
                                mode="lines",
                                line={"width": 1},
                                connectgaps=True,
                                
                            )
                        )

                except:
                    pass

                try:

                    for el in p2.columns:
                        fig.add_trace(
                            go.Scatter(
                                x=p2.index,
                                y=p2[el],
                                name=el,
                                mode="lines",
                                line={"width": 1},
                                connectgaps=True,
                               
                            ),
                            secondary_y=dummy,
                        )
                except:
                    pass

                try:
                    for el in p3.columns:
                        fig.add_trace(
                            go.Scatter(
                                x=p3.index,
                                y=p3[el],
                                name=el,
                                mode="lines",
                                line={"width": 1},
                                connectgaps=True,
                                
                            ),
                            secondary_y=dummy,
                        )
                except:
                    pass
                
                if index_name2==None: index_name2=''
                if index_name3==None: index_name3=''
                if index_name1==None: index_name1=''
                
                fig, config = plotly_drawing(layout_contract_analysis(fig, index_name1,index_name2, index_name3))
                fig.update_xaxes(autorange="reversed")
                
                return dcc.Graph(figure=fig, config=config)
            # seasonal daily
            elif graph_type == 9:
                price = pd.concat([price1, price2, price3], axis=1)
                data, years = seasonality(
                    price, seasonality_period="day", selected_years=slct_years
                )
                fig, config = plotly_drawing(
                    seasonality_graph(
                    data=data, years=years, index_name=index_name1, seasonality="day"
                    )
                )
                return dcc.Graph(figure=fig, config=config)

            # scatter plot
            elif graph_type == 11:
                price = pd.concat([price1, price2, price3], axis=1)
                fig = scatter_graph(price, selected_periods=slct_years)
                return dcc.Graph(figure=fig)

    except Exception as e:
        print(e)
        return html.P("An error occurred please reload")


########################################################
#                Graph Spread                          #
#######################################################


@app.callback(
    Output("graph-spread-html", "children"),
    # Output('test', 'children'),
    Input("graph-spread-button", "n_clicks"),
    Input("my-slider-spread", "value"),
    State("unit-dropdown-4", "value"),
    State("unit-dropdown-5", "value"),
    State("source-dropdown-4", "value"),
    State("index-type-dropdown-4", "value"),
    State("index-name-dropdown-4", "value"),
    State("source-dropdown-5", "value"),
    State("index-type-dropdown-5", "value"),
    State("index-name-dropdown-5", "value"),
    State("slider-dropdown-spread", "value")
    # State("graph-histo", "figure")
)
def graph_spread(
    n,
    graph_type,
    unit1,
    unit2,
    source1,
    index_type1,
    index_name1,
    source2,
    index_type2,
    index_name2,
    slct_years,
):
    if slct_years == []:
        slct_years = None

    try:
        if n is not None:
            try:
                price1 = get_prices(
                    conn=conn,
                    index_name=index_name1,
                    index_type=index_type1,
                    source=[source1],
                    unit=unit1,
                )
            except:
                price1 = pd.DataFrame()
                spread1 = pd.DataFrame()
            try:
                price2 = get_prices(
                    conn=conn,
                    index_name=index_name2,
                    index_type=index_type2,
                    source=[source2],
                    unit=unit2,
                )
            except:
                price2 = pd.DataFrame()
                spread2 = pd.DataFrame()

            if price1.shape[1] > 1:
                col = [
                    index_name1 + str("-") + str(x) + "-" + source1 + "(" + unit1 + ")"
                    for x in index_type1
                ]
                col = [x.replace("-Litasco", "") for x in col]
                col = col[:2]
                spread1 = pd.DataFrame(price1[col[0]] - price1[col[1]])
                spread1.columns = [
                    index_name1 + "-" + str(index_type1[0]) + "/" + str(index_type1[1])
                ]

            if price2.shape[1] > 1:
                col = [
                    index_name2 + str("-") + str(x) + "-" + source2 + "(" + unit2 + ")"
                    for x in index_type2
                ]
                col = [x.replace("-Litasco", "") for x in col]
                col = col[:2]
                spread2 = pd.DataFrame(price2[col[0]] - price2[col[1]])
                spread2.columns = [
                    index_name2 + "-" + str(index_type2[0]) + "/" + str(index_type2[1])
                ]

            # spread = pd.concat([spread1, spread2], join='outer', axis=1)

            if price2.shape[1] == 1 and price1.shape[1] == 1:
                spread = pd.DataFrame(price1.iloc[:, 0] - price2.iloc[:, 0])
                spread.columns = [price1.columns[0] + "/" + price2.columns[0]]

            # historic graph
            if graph_type == 1:
                # to create the secondary_y axis
                if len(set([unit1, unit2])) > 1:
                    dummy = True
                else:
                    dummy = False

                fig = make_subplots(specs=[[{"secondary_y": True}]])

                try:
                    if unit1 == "WS":
                        u = "WS"
                    else:
                        u = "$"
                    for el in spread1.columns:
                        fig.add_trace(
                            go.Scatter(
                                x=spread1.index,
                                y=spread1[el],
                                name=el,
                                connectgaps=True,
                                mode="lines",
                                line={"width": 1},
                                hovertemplate="<br><b>Date</b>: %{x|%B %d, %Y}"
                                + "<br><b>Value</b>: "
                                + str(u)
                                + " %{y}<br>",
                            )
                        )

                except:
                    pass

                try:
                    if unit2 == "WS":
                        u = "WS"
                    else:
                        u = "$"
                    for el in spread2.columns:
                        fig.add_trace(
                            go.Scatter(
                                x=spread2.index,
                                y=spread2[el],
                                name=el,
                                connectgaps=True,
                                mode="lines",
                                line={"width": 1},
                                hovertemplate="<br><b>Date</b>: %{x|%B %d, %Y}"
                                + "<br><b>Value</b>: "
                                + str(u)
                                + " %{y}<br>",
                            ),
                            secondary_y=dummy,
                        )
                except:
                    pass
                try:
                    for el in spread.columns:
                        fig.add_trace(
                            go.Scatter(
                                x=spread.index,
                                y=spread[el],
                                name=el,
                                connectgaps=True,
                                mode="lines",
                                line={"width": 1},
                                hovertemplate="<br><b>Date</b>: %{x|%B %d, %Y}"
                                + "<br><b>Value</b>: "
                                + str(u)
                                + " %{y}<br>",
                            ),
                        )
                except:
                    pass

                fig, config = plotly_drawing(layout(fig))
                return dcc.Graph(figure=fig, config=config)

            # seasonal monthly
            elif graph_type == 3:

                try:
                    spread = pd.concat([spread1, spread2], join="outer", axis=1)
                except:
                    pass

                data, years = seasonality(
                    spread, seasonality_period="month", selected_years=slct_years
                )

                
                fig, config = plotly_drawing(seasonality_graph(
                    data=data, years=years, seasonality="month", index_name=index_name1
                )
                )
                return dcc.Graph(figure=fig, config=config)

            # seasonal weekly
            elif graph_type == 5:
                spread = pd.concat([spread1, spread2], join="outer", axis=1)
                data, years = seasonality(
                    spread, seasonality_period="week", selected_years=slct_years
                )
                fig, config = plotly_drawing(
                    seasonality_graph(
                    data=data, years=years, index_name=index_name1, seasonality="week"
                    )
                )
                
                return dcc.Graph(figure=fig, config=config)


            # seasonal quarter
            elif graph_type == 7:
                spread = pd.concat([spread1, spread2], join="outer", axis=1)
                # seasonality(price=price, seasonality_period='quarter', selected_years=[2018,2019],index_name_q='TC2-TCE',
                #      index_type_q='Q2-2021')
                data, years = seasonality(
                    spread,
                    seasonality_period="quarter",
                    index_name_q=index_name1,
                    index_type_q=index_type1[0],
                    selected_years=slct_years,
                )
                fig = seasonality_graph(
                    data=data,
                    years=years,
                    index_name=index_name1,
                    seasonality="quarter",
                )
                return dcc.Graph(figure=fig)

            # seasonal daily
            elif graph_type == 9:
                spread = pd.concat([spread1, spread2], join="outer", axis=1)
                data, years = seasonality(
                    spread, seasonality_period="day", selected_years=slct_years
                )
                fig, config = plotly_drawing(
                     seasonality_graph(
                    data=data, years=years, index_name=index_name1, seasonality="day"
                    )
                )
                return dcc.Graph(figure=fig, config=config)
                

            # scatter plot
            elif graph_type == 11:
                spread = pd.concat([spread1, spread2], join="outer", axis=1)
                fig = scatter_graph(spread, selected_periods=slct_years)
                return dcc.Graph(figure=fig)

            else:
                pass

        else:
            pass
    except:
        return html.P("An error occurred please reload")


##############################
#           Row 4 dropdown   #
#############################


# Index_type dropdown
@app.callback(
    Output("index-type-dropdown-4", "options"),
    Input("index-name-dropdown-4", "value"),
)
def index_type_4(value):

    with conn:
        index = [{"label": x, "value": x} for x in get_unique_index_type(conn, value)]
        month = [{"label": x, "value": x} for x in get_settlement_date(conn, value)]
        # if len(month)>5:
        #    Q = [{"label": x, "value": x} for x in ['Q1', 'Q2', 'Q3', 'Q4']]
        # else:
        #    Q=[]
    return index + month


# source dropdown
@app.callback(
    Output("source-dropdown-4", "options"),
    Input("index-type-dropdown-4", "value"),
    State("index-name-dropdown-4", "value"),
)
def source_4(index_type, index_name):

    if index_type == [] or index_name == []:
        return []
    else:
        with conn:
            source = [
                {"label": x, "value": x}
                for x in get_source(conn, index_name, index_type)
            ]

        return source


# unit dropdown
@app.callback(
    Output("unit-dropdown-4", "options"),
    Input("source-dropdown-4", "value"),
    State("index-type-dropdown-4", "value"),
    State("index-name-dropdown-4", "value"),
)
def unit_4(source, index_type, index_name):

    if source == [] or index_type == [] or index_name == []:
        return []
    else:
        with conn:
            unit = [
                {"label": x, "value": x}
                for x in get_unit(conn, index_name, index_type, [source])
            ]

        return unit


##############################
#           Row 5 dropdown   #
#############################


# Index_type dropdown
@app.callback(
    Output("index-type-dropdown-5", "options"),
    Input("index-name-dropdown-5", "value"),
)
def index_type_5(value):

    with conn:
        index = [{"label": x, "value": x} for x in get_unique_index_type(conn, value)]
        month = [{"label": x, "value": x} for x in get_settlement_date(conn, value)]

    return index + month


# source dropdown
@app.callback(
    Output("source-dropdown-5", "options"),
    Input("index-type-dropdown-5", "value"),
    State("index-name-dropdown-5", "value"),
)
def source_5(index_type, index_name):

    if index_type == [] or index_name == []:
        return []
    else:
        with conn:
            source = [
                {"label": x, "value": x}
                for x in get_source(conn, index_name, index_type)
            ]

        return source


# unit dropdown
@app.callback(
    Output("unit-dropdown-5", "options"),
    Input("source-dropdown-5", "value"),
    State("index-type-dropdown-5", "value"),
    State("index-name-dropdown-5", "value"),
)
def unit_5(source, index_type, index_name):

    if source == [] or index_type == [] or index_name == []:
        return []
    else:
        with conn:
            unit = [
                {"label": x, "value": x}
                for x in get_unit(conn, index_name, index_type, [source])
            ]

        return unit


#################################
#       dropdown slider  Spread #
################################
@app.callback(
    Output("slider-dropdown-spread", "options"),
    # Output('test', 'children'),
    Input("my-slider-spread", "value"),
    State("unit-dropdown-4", "value"),
    State("unit-dropdown-5", "value"),
    State("source-dropdown-4", "value"),
    State("index-type-dropdown-4", "value"),
    State("index-name-dropdown-4", "value"),
    State("source-dropdown-5", "value"),
    State("index-type-dropdown-5", "value"),
    State("index-name-dropdown-5", "value"),
)
def dropbox_slider_spread(
    value,
    unit1,
    unit2,
    source1,
    index_type1,
    index_name1,
    source2,
    index_type2,
    index_name2,
):

    if value in [3, 5, 7, 9]:
        time.sleep(1)
        try:
            price1 = get_prices(
                conn=conn,
                index_name=index_name1,
                index_type=index_type1,
                source=[source1],
                unit=unit1,
            )
            y1 = list(price1.index.year.unique())
        except:
            y1 = []
            price1 = pd.DataFrame()

        try:
            price2 = get_prices(
                conn=conn,
                index_name=index_name2,
                index_type=index_type2,
                source=[source2],
                unit=unit2,
            )
            y2 = list(price2.index.year.unique())
        except:
            y2 = []
            price2 = pd.DataFrame()

        l = sorted(set(y1 + y2))
        options = [{"label": str(x), "value": x} for x in l]
        return options
    elif value == 11:
        months = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
        val = list(range(1, 13))
        val = list(zip(months, val))
        options = [{"label": x[0], "value": x[1]} for x in val]
        return options
    else:
        return []


# saved prices


@app.callback(
    Output("hidden-div", "children"),
    Input("data-button", "submit_n_clicks"),
    State("unit-dropdown-1", "value"),
    State("unit-dropdown-2", "value"),
    State("source-dropdown-1", "value"),
    State("index-type-dropdown-1", "value"),
    State("index-name-dropdown-1", "value"),
    State("source-dropdown-2", "value"),
    State("index-type-dropdown-2", "value"),
    State("index-name-dropdown-2", "value"),
)
def save_csv_price(
    n,
    unit1,
    unit2,
    source1,
    index_type1,
    index_name1,
    source2,
    index_type2,
    index_name2,
):

    if n is not None:
        try:
            price1 = get_prices(
                conn=conn,
                index_name=index_name1,
                index_type=index_type1,
                source=source1,
                unit=unit1,
            )
        except:
            price1 = pd.DataFrame()

        try:
            price2 = get_prices(
                conn=conn,
                index_name=index_name2,
                index_type=index_type2,
                source=source2,
                unit=unit2,
            )
        except:
            price2 = pd.DataFrame()

    save = pd.concat([price1, price2], join="outer", axis=0)
    save.to_csv(
        r"\\gvaps1\DATAROOT\data\SHARED\PALE\Dash\download_prices\last_prices.csv"
    )



######################################################################################################################
#                                               FWD Curves                                                          #
####################################################################################################################


# Dates dropdown
@app.callback(
    Output("dropdown-dates-fwd", "options"),
    # Output("graph-fwd-html", "children"),
    Input("dropdown-index-name-fwd", "value"),
    State("dropdown-index-name-fwd", "value"),
)
def dates_fwd(index_name1, index_name):

    if index_name == []:
        return []
    else:
        with conn:
            options = [
                {"label": x, "value": x}
                for x in get_fwd_dates_price(conn, index_name[0])
            ]
        # return html.P(str(options)[:15])
        return options


@app.callback(
    Output("graph-fwd-html", "children"),
    Input("dropdown-index-name-fwd", "value"),
    Input("dropdown-dates-fwd", "value"),
)
def graph_fwd(l_index_name, l_dates):

    fig = go.Figure()
    try:
        l_dates = sorted(l_dates, reverse=False)
        if len(l_dates) > 1:
            l_opacity = np.linspace(0.3, 1, len(l_dates))
        else:
            l_opacity = [1]
        colors = px.colors.qualitative.D3
        time.sleep(1)
        for i, el in enumerate(l_index_name):
            for j, d in enumerate(l_dates):
                try:
                    with conn:
                        temp = get_fwd_curve_from_db_price(conn, el, date=d)
                    #temp.settlement_date[0] = 'cash'
                    temp.index = temp.settlement_date
                    index_type = temp.index_type
                    temp = temp[["value"]]
                    name = el + " " + str(d)
                    temp.columns = [name]
                    fig.add_trace(
                        go.Scatter(
                            x=temp.index,
                            y=temp[name],
                            name=name,
                            mode="lines+markers",
                            hovertemplate="<br><b>%{text}</b>"
                            + "<br><b>Value</b>: $%{y}<br>",
                            text=["{}".format(x) for x in index_type],
                            line=dict(
                                color="rgba"
                                + str(hexa_to_rgb(colors[i], opacity=l_opacity[j]))
                            ),
                        )
                    )
                except:
                    temp = pd.DataFrame()

        # fig = layout(fig)
        fig.update_layout(
            title={"text": "<b>Forward Curves<b>", "font": {"size": 14}, "x": 0.5},
            template="plotly_white",
            legend=dict(
                orientation="v",
                yanchor="auto",
                y=1,
                xanchor="left",
                x=0,
                font={"size": 9},
                bgcolor="rgba(235,233,233,0.5)",
            ),
            margin=dict(l=10, r=10, b=30, t=30, pad=4),
            # hovermode='x unified',
            hoverlabel=dict(
                bgcolor="LightGrey",
            ),
        )
        fig.update_yaxes(autorange=True, gridcolor="rgb(184, 234, 253)")
        fig.update_xaxes(
            gridcolor="rgb(193, 252, 186)",
        )
        # return html.P(l_index_name[0])
        return dcc.Graph(figure=fig)
    except:
        return dcc.Graph(figure=fig)


###################################################################################
#                      REGIONAAL SUPPLY
#
####
#
#########
#
#########
#################################################


# --------------------------------------------------------------------------------------------------------------------------------
# Index_type dropdown
@app.callback(
    Output("index-type-dropdown", "options"),
    Input("index-name-dropdown", "value"),
)
def index_type_regional(value):

    with conn:
        index = [{"label": x, "value": x} for x in get_unique_index_type(conn, value)]

    return index


# --------------------------------------------------------------------------------------------------------------------------------


@app.callback(
    Output("graphs-positions-container", "children"),
    Input("update-button-positions", "n_clicks"),
    State("vessel-type-laden", "value"),
    State("clean-dirty-laden", "value"),
    State("zones-laden", "value"),
    State("resample-dropdown", "value"),
    State("my-start-date", "date"),
    State("vessel-type-ballast", "value"),
    State("clean-dirty-ballast", "value"),
    State("zones-ballast", "value"),
    State("index-name-dropdown", "value"),
    State("index-type-dropdown", "value"),
)
def ballast_laden(
    n,
    vessel_type_laden,
    clean_dirty_laden,
    zones_laden,
    resample_dropdown,
    my_start_date,
    vessel_type_ballast,
    clean_dirty_ballast,
    zones_ballast,
    index_name,
    index_type,
):

    if n is not None:
        Req = namedtuple("Req", "loaded_ballast type clean_dirty zones start_date")

        # pd.DataFrame({'x':zones_ballast}).to_csv('sdf.csv')
        if str(zones_laden).find("World") > 0:
            zones_laden = ["EOS", "WOS"]
        else:
            pass
        if str(zones_ballast).find("World") > 0:
            zones_ballast = ["EOS", "WOS"]
        else:
            pass

        if index_name.find("TCE") > 0:
            unit = "USD/DAY"
        else:
            unit = "USD/T"
        index_type = [index_type]

        # vessel_type_laden = [vessel_type_laden]
        # vessel_type_ballast = [vessel_type_ballast]

        my_start_date = [my_start_date]  # because of sql string format

        my_ballast = Req(
            sql_format(["ballast"]),
            sql_format(vessel_type_ballast),
            sql_format(clean_dirty_ballast),
            sql_format(zones_ballast),
            sql_format(my_start_date),
        )

        my_laden = Req(
            sql_format(["loaded"]),
            sql_format(vessel_type_laden),
            sql_format(clean_dirty_laden),
            sql_format(zones_laden),
            sql_format(my_start_date),
        )

        with conn:
            dic_traces = get_ballast_laden(
                conn, my_ballast, my_laden, resample_dropdown
            )

        fig_demand_supply, config = plotly_drawing(
            make_supply_demand_graph(dic_traces))

        laden = dic_traces["Laden Vessels"]["data"]
        # laden.to_csv('test.csv')
        ballast = dic_traces["Ballast Vessels"]["data"]

        with conn:
            fig_balance, config = plotly_drawing(
                make_balance_graph(
                conn,
                laden,
                ballast,
                index_name,
                index_type,
                unit,
                period=resample_dropdown,
                )
            )
        
        return [
            dbc.Col(
                html.Div(
                    dcc.Graph(id="graph-demand-supply", 
                    figure=fig_demand_supply, config=config),
                    className="pretty_container",
                ),
                # md=6,
            ),
            dbc.Col(
                html.Div(
                    dcc.Graph(id="graph-balance", 
                    figure=fig_balance, config=config),
                    className="pretty_container",
                )
            )
            # md=6,
            # justify="around",
            # ,style={"background-color": "#f9f9f9"}
        ]


# -------------------------------------------------------------------------------------------------------------
####################################################
#          Tonnage call backs
##################################################





# -----------------------------------------------------------------------------------------------------------------

# Index_type dropdown
@app.callback(
    Output("index-type-tonnage-dropdown", "options"),
    Input("index-name-tonnage-dropdown", "value"),
)
def index_type_tonnage(value):

    with conn:
        index = [{"label": x, "value": x} for x in get_unique_index_type(conn, value)]

    return index


# ---------------------------------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------------------------------------


@app.callback(
    Output("graph-tonnage", "figure"),
    Input("update-button-tonnage", "n_clicks"),
    State("ports-dropdown", "value"),
    State("vessel-class-dropdown", "value"),
    State("clean-dirty-dropdown", "value"),
    State("laycan-dropdown", "value"),
    State("market-dropdown", "value"),
    State("start-date-tonnage", "date"),
    State("index-name-tonnage-dropdown", "value"),
    State("index-type-tonnage-dropdown", "value"),
)
def update_graph_tonnage(
    n,
    port,
    vessel_class,
    subclass,
    laycan,
    mkt_dplt,
    start_date,
    index_name,
    index_type,
):

    if n is not None:
       
        index_type = [index_type]
        laycan = [laycan]
        my_tonnage = TonnageList()
        param_tonnage = [conn, port, vessel_class, index_name, index_type, start_date, mkt_dplt]
        to_plot = my_tonnage._get_tonnage_time_serie(
            *param_tonnage,
            subclass=subclass,
            
            laycan=laycan
        )
        fig_tonnage = my_tonnage._graph_tonnage_list_dash(to_plot, port, vessel_class)
        return fig_tonnage

if __name__ == "__main__":
    #app.run_server(debug=False, host="0.0.0.0", port=8050)
    app.run_server(debug=True,  port=3050)
