# -*- coding: utf-8 -*-
"""
Created on Wed May 19 08:41:47 2021

@author: pale
"""
import dash
import pandas as pd
import dash_table
import dash_html_components as html
from dash_table.Format import Format, Scheme
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import plotly.graph_objects as go
import sys
import datetime as dt
import dash_daq as daq
from plotly.subplots import make_subplots
import pyodbc
from collections import namedtuple


sys.path.append(r"L:\SHARED\PALE\my_python_modules\my_functions")
from my_functions_old import get_prices, My_date

from regional_supply_functions_new import (
    get_padd,
    get_zones,
    get_ballast_laden,
    make_supply_demand_graph,
    sql_format,
    get_index_name,
    make_balance_graph,
    get_unique_index_type,
    TonnageList,
)


from regional_supply_layout_new import regional_supply_layout

global conn
conn = pyodbc.connect("Driver={SQL Server};"
    "Server=GVASQL19Lis;"
    "Database = Fundamentals;"
    "Trusted_Connection=yes")

app = dash.Dash(__name__, prevent_initial_callbacks=True)
# app.title = 'Shipping S&D'
app.layout = regional_supply_layout


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

        fig_demand_supply = make_supply_demand_graph(dic_traces)
        laden = dic_traces["Laden Vessels"]["data"]
        # laden.to_csv('test.csv')
        ballast = dic_traces["Ballast Vessels"]["data"]

        with conn:
            fig_balance = make_balance_graph(
                conn,
                laden,
                ballast,
                index_name,
                index_type,
                unit,
                period=resample_dropdown,
            )
        return [
            dbc.Col(
                html.Div(
                    dcc.Graph(id="graph-demand-supply", figure=fig_demand_supply),
                    className="pretty_container",
                ),
                # md=6,
            ),
            dbc.Col(
                html.Div(
                    dcc.Graph(id="graph-balance", figure=fig_balance),
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
    app.run_server(debug=True, port=3051)
