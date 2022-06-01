# -*- coding: utf-8 -*-
"""
Created on Thu Apr 22 11:50:43 2021

@author: pale
"""

import pandas as pd
import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
from dash_table.Format import Format, Scheme
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import plotly.graph_objects as go

from arbs_functions import ArbsMapping


def arbs_layout():
    p_loc = r"\\gvaps1\DATAROOT\data\SHARED\PALE\Arbs\locations.csv"
    p_val = r"\\gvaps1\DATAROOT\data\SHARED\PALE\Arbs\Arbs.csv"

    div = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.H3("Middle Distillates Arbs", style={"align": "right"}),
                        className="mini_container",
                        md=3,
                    )
                ],
                justify="center",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        className="pretty_container",
                        children=dcc.Graph(
                            id="map_dist",
                            figure=ArbsMapping().table_map(p_val, p_loc)[1],
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        className="pretty_container",
                        children=dcc.Graph(
                            id="table_dist",
                            figure=ArbsMapping().table_map(p_val, p_loc)[0],
                        ),
                        md=5,
                    ),
                ],
                justify="around",
            ),
        ],
        style={"background-color": "#f9f9f9"},
    )
    return div


app = dash.Dash(__name__, prevent_initial_callbacks=True)
# app.title = 'Shipping S&D'
app.layout = arbs_layout
if __name__ == "__main__":
    app.run_server(debug=True, port=3050)
