# -*- coding: utf-8 -*-
"""
Created on Tue Mar 23 15:04:06 2021

@author: pale
"""

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


import plotly.express as px
from itertools import cycle

# colors
palette = cycle(px.colors.sequential.Rainbow)

from prices_functions import get_index_name, get_prices, get_unique_index_type


def prices_layout():

    conn = pyodbc.connect("Driver={SQL Server};"
        "Server=GVASQL19Lis;"
        "Database = Fundamentals;"
        "Trusted_Connection=yes")

    list_index_name = get_index_name(conn)

    def row_dropdowns(i, multi_source=True, id_name='',id_type=[], srce=[], uu=''):

        return dbc.Row(
            [
                dbc.Col(
                    dcc.Dropdown(
                        id="index-name-dropdown-{}".format(i),
                        options=[{"label": x, "value": x} for x in list_index_name],
                        placeholder="Index Name",
                        value = id_name,
                        multi=False,
                        style={"font-size": "85%"}
                        # value=index,
                    ),
                ),
                dbc.Col(
                    dcc.Dropdown(
                        id="index-type-dropdown-{}".format(i),
                        options=[],
                        value = id_type,
                        placeholder="Index Type",
                        multi=True,
                        style={"font-size": "85%"},
                    )
                ),
                dbc.Col(
                    dcc.Dropdown(
                        id="source-dropdown-{}".format(i),
                        options=[
                            {"label": "Baltic", "value": "Baltic"},
                            {"label": "Litasco", "value": "Litasco"},
                        ],
                        multi=multi_source,
                        value = srce,
                        placeholder="Source",
                        style={"font-size": "85%"},
                    )
                ),
                dbc.Col(
                    dcc.Dropdown(
                        id="unit-dropdown-{}".format(i),
                        placeholder="Unit",
                        options=[
                            {"label": "USD/DAY", "value": "USD/DAY"},
                            {"label": "USD/T", "value": "USD/T"},
                            {"label": "WS", "value": "WS"},
                        ],
                        #value = uu,
                        multi=False,
                        style={"font-size": "85%"},
                    )
                ),
            ],
            no_gutters=True,
        )

    div = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            id="graph-html",
                            children=dcc.Graph(
                                id="graph-histo", config={"responsive": True}
                            ),
                        ),
                        className="pretty_container",
                        md=8,
                    ),
                    dbc.Col(
                        [
                            dbc.Row(
                                dbc.Col(
                                    html.Div(
                                        className="mini_container",
                                        children=[
                                            html.H6(
                                                "Historic Data",
                                            )
                                        ],
                                    ),
                                    width={"size": 5},
                                ),
                                justify="center",
                            ),
                            html.Div(
                                className="pretty_container",
                                children=[row_dropdowns(1)],
                            ),
                            html.Div(
                                className="pretty_container",
                                children=[row_dropdowns(2)],
                            ),
                            html.Div(
                                className="pretty_container",
                                children=[row_dropdowns(3)],
                            ),
                            html.Div(
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Button(
                                                "Update Graph",
                                                id="graph-button",
                                                # className="mr-1",
                                            ),
                                        ),
                                        dbc.Col(
                                            dcc.ConfirmDialogProvider(
                                                children=html.Button("Download Data"),
                                                id="data-button",
                                                message="Please find the prices saved under \\gvaps1\DATAROOT\data\SHARED\PALE\Dash\download_prices",
                                            ),
                                            width=3,
                                        ),
                                    ],
                                    justify="between",
                                    style={"margin": "0.1rem"},
                                )
                            ),
                        ]
                    ),
                ],
                style={"background-color": "#f9f9f9"},
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Slider(
                            id="my-slider",
                            min=0,
                            max=14,
                            value=1,
                            step=None,
                            marks={
                                1: {
                                    "label": "Historical Graph",
                                    "style": {"color": "#54CCFC"},
                                },
                                3: {
                                    "label": "Contracts Analysis",
                                    "style": {"color": "#54CCFC"},
                                },
                                5: {
                                    "label": "Seasonal Graph-M",
                                    "style": {"color": "#54CCFC"},
                                },
                                7: {
                                    "label": "Seasonal Graph-W",
                                    "style": {"color": "#54CCFC"},
                                },
                                9: {
                                    "label": "Seasonal Graph-D",
                                    "style": {"color": "#54CCFC"},
                                },
                                11: {
                                    "label": "Scatter-Graph",
                                    "style": {"color": "#54CCFC"},
                                },
                                
                            },
                            included=False,
                        ),
                        width={"size": 9, "offset": 0},
                        style={"margin": "rem"},
                    ),
                    dbc.Col(
                        html.Div(
                            id="html-dropbox-slider",
                            children=[
                                dcc.Dropdown(
                                    id="slider-dropdown",
                                    options=[],
                                    placeholder="Seasonality Periods",
                                    multi=True,
                                    style={"font-size": "85%"},
                                )
                            ],
                            className="pretty_container",
                        ),
                        width={"size": 2},
                    ),
                ],
                className="pretty_container",
                style={"margin-top": "0.5rem", "margin-bottom": "0.5rem"},
            ),
            ##########################################
            #             SPREADS                    #
            ##########################################
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            id="graph-spread-html",
                            children=dcc.Graph(
                                id="graph-spread", config={"responsive": True}
                            ),
                        ),
                        className="pretty_container",
                        md=8,
                    ),
                    dbc.Col(
                        [
                            dbc.Row(
                                dbc.Col(
                                    html.Div(
                                        className="mini_container",
                                        children=[html.H6("Spread Analysis")],
                                        style={
                                            "align": "center",
                                            "font-size": "85%",
                                        },
                                    ),
                                    width={"size": 5},
                                ),
                                justify="center",
                            ),
                            html.Div(
                                className="pretty_container",
                                children=[row_dropdowns(4, multi_source=False)],
                            ),
                            html.Div(
                                className="pretty_container",
                                children=[row_dropdowns(5, multi_source=False)],
                            ),
                            html.Div(
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Button(
                                                "Update Graph",
                                                id="graph-spread-button",
                                                className="mr-1",
                                            ),
                                            width={"size": 6, "offset": 5},
                                        )
                                    ]
                                )
                            ),
                        ]
                    ),
                ],
                style={"background-color": "#f9f9f9"},
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Slider(
                            id="my-slider-spread",
                            min=0,
                            max=14,
                            value=1,
                            step=None,
                            marks={
                                1: {
                                    "label": "Historical Graph",
                                    "style": {"color": "#54CCFC"},
                                },
                                3: {
                                    "label": "Seasonal Graph-M",
                                    "style": {"color": "#54CCFC"},
                                },
                                5: {
                                    "label": "Seasonal Graph-W",
                                    "style": {"color": "#54CCFC"},
                                },
                                7: {
                                    "label": "Seasonal Graph-Q",
                                    "style": {"color": "#54CCFC"},
                                },
                                9: {
                                    "label": "Seasonal Graph-D",
                                    "style": {"color": "#54CCFC"},
                                },
                                11: {
                                    "label": "Scatter-Graph",
                                    "style": {"color": "#54CCFC"},
                                },
                                13: {
                                    "label": "Spread1_VS_Spread2",
                                    "style": {"color": "#54CCFC"},
                                },
                            },
                            included=False,
                        ),
                        width={"size": 9, "offset": 0},
                        style={"margin": "rem"},
                    ),
                    dbc.Col(
                        html.Div(
                            id="html-dropbox-slider-spread",
                            children=[
                                dcc.Dropdown(
                                    id="slider-dropdown-spread",
                                    options=[],
                                    placeholder="Seasonality Periods",
                                    multi=True,
                                    style={"font-size": "85%"},
                                )
                            ],
                            className="pretty_container",
                        ),
                        width={"size": 2},
                    ),
                ],
                className="pretty_container",
                style={"margin-top": "0.5rem", "margin-bottom": "0.5rem"},
            ),
            html.Div(
                id="hidden-div",
                children=[],
                style={"display": "none"},
            ),
            #############################################################################
            #                     Fwd Curves                                            #
            #############################################################################
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            id="graph-fwd-html",
                            children=dcc.Graph(
                                id="graph-fwd", config={"responsive": True}
                            ),
                        ),
                        className="pretty_container",
                        md=8,
                    ),
                    dbc.Col(
                        [
                            dbc.Row(
                                dbc.Col(
                                    html.Div(
                                        className="mini_container",
                                        children=[
                                            html.H6(
                                                "forward Curves",
                                            )
                                        ],
                                        style={
                                            "align": "center",
                                            "font-size": "85%",
                                        },
                                    ),
                                    width={"size": 5},
                                ),
                                justify="center",
                            ),
                            dbc.Row(
                                className="pretty_container",
                                children=[
                                    dbc.Col(
                                        dcc.Dropdown(
                                            id="dropdown-index-name-fwd",
                                            placeholder="Index Name",
                                            options=[
                                                {"label": x, "value": x}
                                                for x in list_index_name
                                            ],
                                            multi=True,
                                            style={"font-size": "85%"}
                                            # value=index,
                                        ),
                                    ),
                                    dbc.Col(
                                        dcc.Dropdown(
                                            id="dropdown-dates-fwd",
                                            options=[],
                                            placeholder="Dates",
                                            multi=True,
                                            style={"font-size": "85%"},
                                        )
                                    ),
                                ],
                            ),
                        ]
                    ),
                ]
            ),
        ],
        style={"background-color": "#f9f9f9"},
    )

    return div
