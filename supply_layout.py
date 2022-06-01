# -*- coding: utf-8 -*-
"""
Created on Mon Mar 22 08:39:14 2021

@author: pale
"""


import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import plotly.graph_objects as go
import sys
import datetime as dt
import dash_daq as daq
from itertools import cycle
import json
import plotly.express as px
palette = cycle(px.colors.qualitative.D3)

sys.path.append(r"L:\SHARED\PALE\my_python_modules\my_functions")
from my_functions import My_date
from supply_functions import (
    fleet_dev_per_ship,
    orderbook,
    individual_tankers,
    addition,
    demolition,
    scenario_age,
    scenario_constant,
    layout_plotly
)


def supply_layout():
    palette = cycle(px.colors.qualitative.D3)
    
    crude_fleet_mbbl, crude_fleet_no = fleet_dev_per_ship()
    crude_tankers_mbbl, crude_tankers_no = individual_tankers()
    dic_sce = scenario_age(crude_tankers_mbbl, [17, 19])
    # dic_sce = scenario_age(crude_tankers_mbbl, [17, 19])
    addition_mbbl, addition_no = addition()
    demolition_mbbl, demolition_no = demolition()
    orderbook_mbbl, orderbook_no = orderbook()
    x = scenario_constant(
        crude_fleet_mbbl, orderbook_mbbl, demolition_mbbl["total_mbbl"].mean()
    )

    dic_df = {
        "crude": {
            "fleet_dev": [x.to_json() for x in (crude_fleet_mbbl, crude_fleet_no)],
            "addition": [x.to_json() for x in (addition_mbbl, addition_no)],
            "individual_tankers": [
                x.to_json() for x in (crude_tankers_mbbl, crude_tankers_no)
            ],
            "demolition": [x.to_json() for x in (demolition_mbbl, demolition_no)],
            "orderbook": [x.to_json() for x in (orderbook_mbbl, orderbook_no)],
        },
        "clean": {
            "fleet_dev": [x.to_json() for x in fleet_dev_per_ship(True)],
            "addition": [x.to_json() for x in addition(True)],
            "individual_tankers": [x.to_json() for x in individual_tankers(True)],
            "demolition": [x.to_json() for x in demolition(True)],
            "orderbook": [x.to_json() for x in orderbook(True)],
        },
    }
    
    ##########################
    # Yearly dev graph bar   #
    ##########################
    
        
    
    yearly_fleet = crude_fleet_mbbl.copy()
    
    yearly_fleet['year'] = yearly_fleet.index.year
    yearly_fleet = yearly_fleet.groupby('year').last()
    

    data=[
        go.Bar(name='VLCC', x=yearly_fleet.index, y=yearly_fleet.VLCC_mbbl, marker_color=next(palette)),
        go.Bar(name='Suezmax', x=yearly_fleet.index, y=yearly_fleet.suezmax_mbbl, marker_color=next(palette)),
        go.Bar(name='Aframax', x=yearly_fleet.index, y=yearly_fleet.aframax_mbbl, marker_color=next(palette)),
        go.Bar(name='Panamax', x=yearly_fleet.index, y=yearly_fleet.panamax_mbbl, marker_color=next(palette)),
        #go.Bar(name='Total', x=yearly_fleet.index, y=yearly_fleet.total_no, marker_color=next(palette))
    ]
    
    fig_yearly_graph = go.Figure(data=data)
    
    
    fig_yearly_graph = layout_plotly(fig_yearly_graph, 'Dirty Fleet Development', template='ggplot2')
    
    
    
    
    
    ###########################
    #       DEMOLITION GRAPH  #
    ###########################

    unit = "mbbl"
    unit_u = unit.upper()
    ship = "total"
    ship_type = ship + "_" + unit
    ##############################

    fig_demo = go.Figure()

    fig_demo.add_trace(
        go.Scatter(
            x=demolition_mbbl.index,
            y=demolition_mbbl[ship_type],
            name="Demolition - " + unit_u,
            mode="lines",
            line={"width": 1, "color": "DodgerBlue"},
            # fill='toself'
        )
    )

    fig_demo.add_trace(
        go.Scatter(
            x=demolition_mbbl.index,
            y=demolition_mbbl[ship_type].rolling(window=24).quantile(0.25),
            name="25% - Quantile",
            line={
                "width": 1,
                "color": "grey",
            },
        )
    )
    fig_demo.add_trace(
        go.Scatter(
            x=demolition_mbbl.index,
            y=demolition_mbbl[ship_type].rolling(window=24).quantile(0.75),
            name="75% - Quantile",
            line={"width": 1, "color": "grey"},
            fill="tonexty",
        )
    )

    fig_demo.add_trace(
        go.Scatter(
            x=demolition_mbbl.index,
            y=demolition_mbbl[ship_type].rolling(window=24).quantile(0.5),
            name="24-Month rolling Median",
            line={"width": 2, "color": "black", "dash": "dot"},
        )
    )

    fig_demo.update_layout(
        template="ggplot2",
        title={
            "text": "<b>TOTAL - Demolition in {}<b>".format(unit_u),
            "font": {"size": 14},
            "x": 0.5,
        },
        # template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="left", x=0),
        margin=dict(l=30, r=10, b=50, t=30, pad=4),
    )

    ###################################
    #       Addition Graph            #
    ###################################

    fig_add = go.Figure()

    fig_add.add_trace(
        go.Scatter(
            x=addition_mbbl[addition_mbbl.state == "deliveries"].index,
            y=addition_mbbl[addition_mbbl.state == "deliveries"][ship_type],
            name="Deliveries - " + unit_u,
            mode="lines",
            line={"width": 1, "color": "DodgerBlue"},
            # fill='toself'
        )
    )

    fig_add.add_trace(
        go.Scatter(
            x=addition_mbbl[addition_mbbl.state == "orderbook"].index,
            y=addition_mbbl[addition_mbbl.state == "orderbook"][ship_type],
            name="orderbook - " + unit_u,
            mode="lines",
            line={"width": 2, "color": "firebrick"},
            # fill='toself'
        )
    )

    fig_add.add_trace(
        go.Scatter(
            x=addition_mbbl.index,
            y=addition_mbbl[ship_type].rolling(window=24).quantile(0.25),
            name="25% - Quantile",
            line={
                "width": 1,
                "color": "grey",
            },
        )
    )
    fig_add.add_trace(
        go.Scatter(
            x=addition_mbbl.index,
            y=addition_mbbl[ship_type].rolling(window=24).quantile(0.75),
            name="75% - Quantile",
            line={"width": 1, "color": "grey"},
            fill="tonexty",
        )
    )

    fig_add.add_trace(
        go.Scatter(
            x=addition_mbbl.index,
            y=addition_mbbl[ship_type].rolling(window=24).quantile(0.5),
            name="24-Month rolling Median",
            line={"width": 2, "color": "black", "dash": "dot"},
        )
    )

    fig_add.update_layout(
        template="ggplot2",
        title={
            "text": "<b>TOTAL - Deliveries+Orderbook in {}<b>".format(unit_u),
            "font": {"size": 14},
            "x": 0.5,
        },
        # template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="left", x=0),
        margin=dict(l=30, r=10, b=30, t=30, pad=4),
    )

    #############################
    #       Scenario            #
    ############################

    fig_sce = go.Figure()

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
        else:
            f = None

        orderbook_mbbl.fillna(0, inplace=True)
        scenario = (orderbook_mbbl.resample("M").mean().cumsum() - v).dropna(
            subset=["total_mbbl"]
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
            name="Mean Scenario",
            mode="lines",
            line={"width": 3, "dash": "dot", "color": "red"},
            # fill='tozeroy'
        )
    )

    fig_sce.update_layout(
        template="ggplot2",
        title={
            "text": "<b>TOTAL - Dirty Fleet Development in {}<b>".format(unit_u),
            "font": {"size": 14},
            "x": 0.5,
        },
        # template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=0.93, xanchor="left", x=0),
        margin=dict(l=30, r=10, b=30, t=30, pad=4),
    )

    div = html.Div(
        [   
                
                
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(dcc.Graph(id="graph-yearly", figure=fig_yearly_graph)),
                        className="pretty_container",
                        width={"size": 7, "offset": 0},
                    ),
                            dbc.Col(
                        html.Div(id='dummy', style={"background-color": "#f9f9f9"}),
                        #className="pretty_container",
                        width={"size": 5, "offset": 0},
                    )], style={"background-color": "#f9f9f9"}, justify="around"),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(dcc.Graph(id="graph-sce", figure=fig_sce)),
                        className="pretty_container",
                        md=7,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            html.Div(
                                                [
                                                    dcc.Dropdown(
                                                        id="clean-dropdown",
                                                        options=[
                                                            {
                                                                "label": "Dirty",
                                                                "value": "crude",
                                                            },
                                                            {
                                                                "label": "Clean",
                                                                "value": "clean",
                                                            },
                                                        ],
                                                        multi=False,
                                                        value="crude",
                                                    )
                                                ],
                                                className="pretty_container",
                                            ),
                                            md=5,
                                        ),
                                        dbc.Col(
                                            html.Div(
                                                [
                                                    dcc.RadioItems(
                                                        id="mbbl-button",
                                                        options=[
                                                            {
                                                                "label": "MBBL",
                                                                "value": "mbbl",
                                                            },
                                                            {
                                                                "label": "Number of Ships",
                                                                "value": "no",
                                                            },
                                                        ],
                                                        # labelStyle={
                                                        #   "display": "inline-block"
                                                        # },
                                                        value="mbbl",
                                                    )
                                                ],
                                                className="pretty_container",
                                            )
                                        ),
                                    ],
                                    justify="around",
                                ),
                                html.Div(
                                    [
                                        dcc.Dropdown(
                                            id="ship-dropdown",
                                            options=[
                                                {
                                                    "label": x.replace(
                                                        "_mbbl", ""
                                                    ).upper(),
                                                    "value": x.replace("_mbbl", ""),
                                                }
                                                for x in demolition_mbbl.columns
                                                if x != "state"
                                            ],
                                            multi=False,
                                            value="total",
                                        ),
                                    ],
                                    className="pretty_container",
                                ),
                                html.Div(
                                    [
                                        html.P(children="Scrapping rate scenarios"),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            dcc.Dropdown(
                                                                id="age-dropdown",
                                                                options=[
                                                                    {
                                                                        "label": x,
                                                                        "value": x,
                                                                    }
                                                                    for x in list(
                                                                        range(10, 24)
                                                                    )
                                                                ],
                                                                multi=True,
                                                                value=[17, 19],
                                                            )
                                                        ],
                                                        className="pretty_container",
                                                    ),
                                                ),
                                                dbc.Col(
                                                    html.Div(
                                                        id="my-slider",
                                                        children=[
                                                            daq.Slider(
                                                                id="constant-slider",
                                                                min=0,
                                                                max=10,
                                                                value=round(
                                                                    demolition_mbbl.total_mbbl.mean(),
                                                                    2,
                                                                ),
                                                                handleLabel={
                                                                    "showCurrentValue": True,
                                                                    "label": "value",
                                                                },
                                                                marks={
                                                                    str(
                                                                        round(
                                                                            demolition_mbbl.total_mbbl.mean(),
                                                                            2,
                                                                        )
                                                                    ): "Mean",
                                                                    str(
                                                                        round(
                                                                            demolition_mbbl.total_mbbl.quantile(
                                                                                0.5
                                                                            ),
                                                                            2,
                                                                        )
                                                                    ): "2-Q",
                                                                    str(
                                                                        round(
                                                                            demolition_mbbl.total_mbbl.quantile(
                                                                                0.75
                                                                            ),
                                                                            2,
                                                                        )
                                                                    ): "3-Q",
                                                                },
                                                                step=0.1,
                                                                size=250,
                                                            )
                                                        ],
                                                        className="pretty_container",
                                                    )
                                                ),
                                                dbc.Col(
                                                    dcc.ConfirmDialogProvider(
                                                        children=html.Button(
                                                            "Save Supply",
                                                        ),
                                                        id="save-button",
                                                        message="Please find the scenario saved under \\gvaps1\DATAROOT\data\SHARED\PALE\Dash\saved_supply",
                                                    ),
                                                ),
                                            ],
                                            justify="around",
                                        ),
                                    ],
                                    className="pretty_container",
                                ),
                            ],
                            className="pretty_container",
                        ),
                        md=3,
                    ),
                ],
                style={"background-color": "#f9f9f9"},
                justify="around",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(dcc.Graph(id="graph-demo", figure=fig_demo)),
                        className="pretty_container",
                        md=5,
                    ),
                    dbc.Col(
                        html.Div(dcc.Graph(id="graph-add", figure=fig_add)),
                        className="pretty_container",
                        md=5,
                    ),
                ],
                justify="around",
                style={"background-color": "#f9f9f9"},
            ),
            html.Div(
                id="hidden-div",
                children=[json.dumps(dic_df)],
                style={"display": "none"},
            ),
            html.Div(
                id="hidden-div-sce",
                children=json.dumps({k: v.to_json() for k, v in dic_sce.items()}),
                style={"display": "none"},
            ),
            html.Div(id="hidden-supply", children=[], style={"display": "none"}),
        ],
        className="body",
    )

    return div
