# -*- coding: utf-8 -*-
"""
Created on Tue May 11 13:23:13 2021

@author: pale
"""
import dash
import pandas as pd
import dash_table
import dash_html_components as html
from dash_table.Format import Format, Scheme
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
    TonnageList,
    get_unique_index_type,
)


def regional_supply_layout():

    conn = pyodbc.connect("Driver={SQL Server};"
    "Server=GVASQL19Lis;"
    "Database = Fundamentals;"
    "Trusted_Connection=yes")

    my_tonnage = TonnageList()
    with conn:
        liste_ports = my_tonnage.ports
        list_index_name = get_index_name(conn)
        liste_padd = get_padd(conn)
        liste_zones = get_zones(conn)
        
    liste_zones = ["World"] + liste_zones
    liste_zones += liste_padd
    # liste_zones = ['a', 'b', 'World']

    ##################################
    #     Supply Demand Graph       #
    #################################

    vessel_type = ["VLCC"]
    clean_dirty = ["Clean", "Dirty"]
    zones = ["EOS", "WOS"]
    period = 5
    start_date = [My_date().timedelta(-120).string]  # because of sql string format
    index_name = "TD3C-TCE"
    index_type = ["cash"]
    unit = "USD/DAY"

    # Class to make the sql request
    Req = namedtuple("Req", "loaded_ballast type clean_dirty zones start_date")

    my_ballast = Req(
        sql_format(["ballast"]),
        sql_format(vessel_type),
        sql_format(clean_dirty),
        sql_format(zones),
        sql_format(start_date),
    )

    my_laden = Req(
        sql_format(["loaded"]),
        sql_format(vessel_type),
        sql_format(clean_dirty),
        sql_format(zones),
        sql_format(start_date),
    )
    with conn:
        dic_traces = get_ballast_laden(conn, my_ballast, my_laden, period)
    fig_demand_supply = make_supply_demand_graph(dic_traces)

    ##################################
    #              D/S Balance       #
    #################################
    # --------------------
    laden = dic_traces["Laden Vessels"]["data"]
    ballast = dic_traces["Ballast Vessels"]["data"]
    with conn:
        fig_balance = make_balance_graph(
            conn, laden, ballast, index_name, index_type, unit, period=period
        )

    ##########################################################
    #             Tonnage List Graph                         #
    #########################################################

    param_tonnage = [
        conn,
        "Ras Tanura",
        "VLCC",
        index_name,
        index_type,
        My_date().timedelta(-120).string,['Spot', 'Relet']
    ]
    to_plot = my_tonnage._get_tonnage_time_serie(*param_tonnage )
    fig_tonnage = my_tonnage._graph_tonnage_list_dash(to_plot, "Ras Tanura", "VLCC")
    #fig_tonnage = go.Figure()
    # ---------------------------------------------------------------------------------------------------------------------------------------------------------

    div = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.Label(
                            [
                                "Ports      ",
                                dcc.Dropdown(
                                    id="ports-dropdown",
                                    options=[
                                        {"label": x, "value": x} for x in liste_ports
                                    ],
                                    value="Ras Tanura",
                                    placeholder="Port",
                                    multi=False,
                                    style={"font-size": "100%", "width": "150%"},
                                ),
                            ],
                            style={"font-size": "80%"},
                        )
                    ),
                    dbc.Col(
                        [
                            html.Label(
                                [
                                    "Size Class",
                                    dcc.Dropdown(
                                        id="vessel-class-dropdown",
                                        options=my_tonnage.vessel_class_signal,
                                        placeholder="Class",
                                        value="VLCC",
                                        multi=False,
                                        style={"font-size": "100%", "width": "120%"}
                                        # value=index,
                                    ),
                                ],
                                style={"font-size": "80%"},
                            )
                        ]
                    ),
                    dbc.Col(
                        html.Label(
                            [
                                "Clean/Dirty",
                                dcc.Dropdown(
                                    id="clean-dirty-dropdown",
                                    options=[
                                        {"label": x, "value": x}
                                        for x in ["Clean", "Dirty"]
                                    ],
                                    value="Dirty",
                                    placeholder="Clean/Dirty",
                                    multi=False,
                                    style={"font-size": "100%", "width": "120%"},
                                ),
                            ],
                            style={"font-size": "80%"},
                        )
                    ),
                    dbc.Col(
                        html.Label(
                            [
                                "Laycan In X Days",
                                dcc.Dropdown(
                                    id="laycan-dropdown",
                                    options=[{"label": x, "value": x} for x in my_tonnage.days],
                                     value=5,
                                    placeholder="Days",
                                    multi=False,
                                    style={"font-size": "100%"},
                                ),
                            ],
                            style={"font-size": "80%"},
                        )
                    ),
                    dbc.Col(
                        [
                            html.Label(
                                [
                                    "Market Dplt",
                                    dcc.Dropdown(
                                        id="market-dropdown",
                                        options=[{"label": x, "value": x}
                                            for x in my_tonnage.market_deployment],
                                        placeholder="Market",
                                        value=['Spot', 'Relet'],
                                        multi=True,
                                        style={"font-size": "90%"}
                                        # value=index,
                                    ),
                                ],
                                style={"font-size": "80%"},
                            )
                        ]
                    ),
                    dbc.Col(
                        [
                            html.Label(
                                ["Starting Date"],
                                style={"font-size": "90%", "width": "90%"},
                            ),
                            dcc.DatePickerSingle(
                                id="start-date-tonnage",
                                date=My_date().timedelta(-180).date,
                                display_format="YYYY-MM-DD",
                                style={"font-size": "80%", "width": "70%"},
                            ),
                        ]
                    ),
                   
                    dbc.Col(
                        [
                            html.Label(["Index Name"], style={"font-size": "80%"}),
                            dcc.Dropdown(
                                id="index-name-tonnage-dropdown",
                                options=[
                                    {"label": x, "value": x} for x in list_index_name
                                ],
                                placeholder="Index Name",
                                value="TD3C-TCE",
                                multi=False,
                                style={"font-size": "80%"}
                                # value=index,
                            ),
                        ],
                    ),
                    dbc.Col(
                        [
                            html.Label(["Index Type"], style={"font-size": "80%"}),
                            dcc.Dropdown(
                                id="index-type-tonnage-dropdown",
                                options=[
                                    {"label": x, "value": x}
                                    for x in get_unique_index_type(conn, "TD3C-TCE")
                                ],
                                placeholder="Index Type",
                                multi=False,
                                value="cash",
                                style={"font-size": "80%"},
                            ),
                        ]
                    ),
                    dbc.Button(
                        id="update-button-tonnage",
                        children="Update",
                        outline=True,
                        color="success",
                    ),
                ],
                className="pretty_container",
                no_gutters=True,
            ),
            dbc.Row(
                id="graphs-tonnage-container",
                children=[
                    dbc.Col(
                        html.Div(dcc.Graph(id="graph-tonnage", figure=fig_tonnage)),
                        className="pretty_container",
                    ),
                    # md=6,
                ],
            ),
            # ------------------------------------------------------------------------------------------------------------------
            #########################################################
            #                    Positions                         #
            ########################################################
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label(
                                [
                                    "Size Class - Laden",
                                    dcc.Dropdown(
                                        id="vessel-type-laden",
                                        options=[
                                            {"label": x, "value": x}
                                            for x in [
                                                "VLCC",
                                                "LR3",
                                                "LR2",
                                                "LR1",
                                                "MR2",
                                                "MR1",
                                            ]
                                        ],
                                        placeholder="Class",
                                        value=["VLCC"],
                                        multi=True,
                                        style={"font-size": "90%"}
                                        # value=index,
                                    ),
                                ],
                                style={"font-size": "80%"},
                            )
                        ]
                    ),
                    dbc.Col(
                        html.Label(
                            [
                                "Clean/Dirty - Laden",
                                dcc.Dropdown(
                                    id="clean-dirty-laden",
                                    options=[
                                        {"label": x, "value": x}
                                        for x in ["Clean", "Dirty", "Other"]
                                    ],
                                    value=["Clean", "Dirty"],
                                    placeholder="Clean/Dirty",
                                    multi=True,
                                    style={"font-size": "90%"},
                                ),
                            ],
                            style={"font-size": "80%"},
                        )
                    ),
                    dbc.Col(
                        html.Label(
                            [
                                "Zones - Laden",
                                dcc.Dropdown(
                                    id="zones-laden",
                                    options=[
                                        {"label": x, "value": x} for x in liste_zones
                                    ],
                                    value=["World"],
                                    placeholder="Zones",
                                    multi=True,
                                    style={"font-size": "90%", "width": "110%"},
                                ),
                            ],
                            style={"font-size": "80%"},
                        )
                    ),
                    dbc.Col(
                        html.Label(
                            [
                                "Resample Period",
                                dcc.Dropdown(
                                    id="resample-dropdown",
                                    options=[
                                        {"label": "Weekly", "value": "W"},
                                        {"label": "Daily", "value": "D"},
                                        {"label": "5-day MA", "value": 5},
                                        {"label": "15-day MA", "value": 15},
                                        {"label": "30-day MA", "value": 30},
                                    ],
                                    placeholder="Period",
                                    value=5,
                                    multi=False,
                                    style={"font-size": "90%", "width": "110%"},
                                ),
                            ],
                            style={"font-size": "80%"},
                        )
                    ),
                    dbc.Col(
                        [
                            html.Label(
                                ["Starting Date"],
                                style={"font-size": "90%", "width": "90%"},
                            ),
                            dcc.DatePickerSingle(
                                id="my-start-date",
                                # date=dt.date(2021, 1, 1),
                                date=My_date().timedelta(-180).date,
                                display_format="YYYY-MM-DD",
                                style={"font-size": "80%", "width": "70%"},
                            ),
                        ]
                    ),
                    dbc.Col(
                        [
                            html.Label(
                                [
                                    "Size Class - Ballast",
                                    dcc.Dropdown(
                                        id="vessel-type-ballast",
                                        options=[
                                            {"label": x, "value": x}
                                            for x in [
                                                "VLCC",
                                                "LR3",
                                                "LR2",
                                                "LR1",
                                                "MR2",
                                                "MR1",
                                            ]
                                        ],
                                        placeholder="CLass",
                                        value=["VLCC"],
                                        multi=True,
                                        style={"font-size": "90%"}
                                        # value=index,
                                    ),
                                ],
                                style={"font-size": "80%"},
                            )
                        ]
                    ),
                    dbc.Col(
                        html.Label(
                            [
                                "Clean/Dirty - Ballast",
                                dcc.Dropdown(
                                    id="clean-dirty-ballast",
                                    options=[
                                        {"label": x, "value": x}
                                        for x in ["Clean", "Dirty", "Other"]
                                    ],
                                    value=["Clean", "Dirty"],
                                    placeholder="Clean/Dirty",
                                    multi=True,
                                    style={"font-size": "90%"},
                                ),
                            ],
                            style={"font-size": "80%"},
                        )
                    ),
                    dbc.Col(
                        html.Label(
                            [
                                "Zones - Ballast",
                                dcc.Dropdown(
                                    id="zones-ballast",
                                    options=[
                                        {"label": x, "value": x} for x in liste_zones
                                    ],
                                    value=["World"],
                                    placeholder="Zones",
                                    multi=True,
                                    style={"font-size": "90%", "width": "110%"},
                                ),
                            ],
                            style={"font-size": "80%"},
                        )
                    ),
                    dbc.Col(
                        [
                            html.Label(["Index Name"], style={"font-size": "80%"}),
                            dcc.Dropdown(
                                id="index-name-dropdown",
                                options=[
                                    {"label": x, "value": x} for x in list_index_name
                                ],
                                placeholder="Index Name",
                                value="TD3C-TCE",
                                multi=False,
                                style={"font-size": "80%"}
                                # value=index,
                            ),
                        ],
                    ),
                    dbc.Col(
                        [
                            html.Label(["Index Type"], style={"font-size": "80%"}),
                            dcc.Dropdown(
                                id="index-type-dropdown",
                                options=[
                                    {"label": x, "value": x}
                                    for x in get_unique_index_type(conn, "TD3C-TCE")
                                ],
                                placeholder="Index Type",
                                multi=False,
                                value="cash",
                                style={"font-size": "80%"},
                            ),
                        ]
                    ),
                    dbc.Button(
                        id="update-button-positions",
                        children="Update",
                        outline=True,
                        color="primary",
                    ),
                ],
                className="pretty_container",
                no_gutters=True,
            ),
            ##################################
            #         Graphs                 #
            ##################################
            dbc.Row(
                id="graphs-positions-container",
                children=[
                    dbc.Col(
                        html.Div(
                            dcc.Graph(
                                id="graph-demand-supply", figure=fig_demand_supply
                            ),
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
                ],
            ),
        ],
        style={"background-color": "#f9f9f9"},
    )
    return div


# app = dash.Dash(__name__, prevent_initial_callbacks=True)
# app.title = 'Shipping S&D'
# app.layout = regional_supply_layout


# if __name__ == "__main__":
#    app.run_server(debug=True, port=3050)
