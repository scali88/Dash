# -*- coding: utf-8 -*-
"""
Created on Tue Mar 16 09:35:02 2021

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

import plotly.express as px
from itertools import cycle
# colors
palette = cycle(px.colors.sequential.Rainbow)




sys.path.append(r"L:\SHARED\PALE\my_python_modules\my_functions")
from my_functions import My_date, get_prices
from functions import import_jbc_models, prices_and_curve, get_fwd_dates, ols_cu_price, get_scenaris

#########################################
# THE VLCC SCENARIO TOOL                #
#########################################


def vlcc_layout():
    today = My_date()
    dic_scenaris = get_scenaris()
    index_name = 'TD3_eiger-TCE'
    index_type='M1'
    
    df_base = list(dic_scenaris.items())[0][1]
    #df_base =df_base.drop(columns=['TD3_eiger'])
    # df_base.sort_values(by='Date', ascending=False, inplace=True)
    df_base.Date = pd.to_datetime(df_base.Date)
    df_base = df_base.round(4)
    
    
    df_table = df_base.sort_values(by="Date", ascending=False)
    df_table.Date = df_table.Date.apply(lambda x: x.strftime("%Y-%m-%d"))
    
    temp1 = df_base.set_index("Date")
    temp1 = temp1.sort_index(ascending=True)
    temp1 = temp1.merge(prices_and_curve(date='last'), left_index=True, right_index=True)
    temp1 = +temp1[["cu", index_name]] - temp1[["cu", index_name]].shift(13).rolling(3).mean()
    plot, r2 = ols_cu_price(temp1.copy())
   
    temp2 = df_base.set_index("Date")
    temp2 = temp2.merge(prices_and_curve(date='last'), left_index=True, right_index=True)
    
    plot, r2 = ols_cu_price(temp1.copy())
    plot.name = 'TD3_eiger_forecast'
    plot = temp1[['cu']].merge(plot, left_index=True, right_index=True)


    # Create figure CU
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Scatter(
            x=temp2[:today.string].index,
            y=temp2[:today.string].cu,
            name="Litasco Model CU - Actual",
            line={"width": 2, "color": "red"},
        )
    )
    
    fig.add_trace(
        go.Scatter(x=temp2[today.string:].index, y=temp2[today.string:].cu, name="Litasco CU Model-FWD", line={"width": 2, 'color':'red'})
    )
    
    fig.add_trace(
        go.Scatter(x=temp2.index, y=temp2[index_name], name=index_name+' '+index_type, line={"width": 2, 'color':'black'}), secondary_y=True)
    
    
    fig.update_layout(
        title={"text": "VLCC CU Model", "font": {"size": 14}},
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=30, r=10, b=30, t=30, pad=4),
    )

   
    
    # Scatter plot
    fig_sct = go.Figure()
    fig_sct.add_trace(
        go.Scatter(
            x=temp1[: today.string].cu,
            y=temp1[: today.string][index_name],
            name="TD3 Price Difference",
            mode="markers",
            marker={"symbol": "circle", "size": 8, "color": "black"},
            text=temp1[: today.string].index.date,
        )
    )
    fig_sct.add_trace(
        go.Scatter(
            x=temp1[today.string :].cu,
            y=temp1[today.string :][index_name],
            name="TD3 Price Difference",
            mode="markers",
            marker={"symbol": "circle-open", "size": 10, "color": "black"},
            text=temp1[today.string :].index.date,
        )
    )
    fig_sct.add_trace(
        go.Scatter(
            x=plot.cu,
            y=plot.TD3_eiger_forecast,
            text=temp1.index.date,
            name="Litasco Price Difference Model",
            mode="lines",
            line={"color": "red"},
        )
    )
    
    fig_sct.update_layout(
        title={
            "text": index_name+" Price Difference Forecast vs CU(%) difference",
            "font": {"size": 14},
        },
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=-0.02, xanchor="right", x=1),
        margin=dict(l=30, r=10, b=50, t=30, pad=4),
    )
    
    dates = get_fwd_dates().sort_values(by='date', ascending=False).date
    max_date = max(dates)
    routes = ['TD3_eiger', 'TD3_eiger-TCE', 'TD20', 'TD20-TCE']
    return  html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.Div(dcc.Graph(id="graph-cu", figure=fig)),
                    className="pretty_container",
                    md=4,
                ),
                dbc.Col(
                    html.Div(dcc.Graph(id="graph-scatter", figure=fig_sct)),
                    className="pretty_container",
                    md=5,
                ),
                        
                dbc.Col(
                    html.Div([
                            dbc.Row([ dbc.Col(
                            dcc.Dropdown(id="index-name-dropdown", 
                                          options=[{'label':x, 'value':x } for x in routes],
                                          multi=False,
                                          value='TD3_eiger-TCE'),md=7),
                         dbc.Col(
                        dcc.Dropdown(id="index-type-dropdown", 
                                          options=[{'label':'cash', 'value': 'cash' }]+
                                          [{'label':'M'+str(x), 'value':'M'+str(x) } for x in list(range(24)) ],
                                          multi=False,
                                          value='M1')),
                                     ]
                                    ),
                            
                            
                            html.Div([dcc.Dropdown(id="fwd-curves-dropdown", 
                                          options=[{'label':x, 'value':x } for x in dates],
                                          multi=True,
                                          value=max(dates))])
                ,
                daq.BooleanSwitch(id='generic-year',
                          on=False,
                          label="Make 2020 a Generic year",
                          labelPosition="top"),

                    
                html.P( children='R2 - is based on the period from 2016-01-01 to 2021-02-28'),
                html.P(id='r2', children='R2: ' + str(round(r2, 3)), className='indicator_value'),
                dcc.ConfirmDialogProvider(
                        children=html.Button(
                                'Save Scenario',
                                ),
                                id='save-button',
                                message='Please find the scenario saved under \\gvaps1\DATAROOT\data\SHARED\PALE\Dash\saved_scenario '
                                ),
              
                
                ],
                ),
                    className="pretty_container",md=2
                    
                
                )
            ],
            style={"background-color": "#f9f9f9"},
        ),
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        id="tab",
                        children=[
                            dash_table.DataTable(
                                id="d_s-table",
                                columns=[
                                    {
                                        "name": ["", "Date"],
                                        "id": "Date",
                                        "type": "datetime",
                                        "editable": False,
                                    }
                                ]
                                + [
                                    {
                                        "name": ["Demand - MBBL", i],
                                        "id": i,
                                        "type": "numeric",
                                        "format": Format(
                                            precision=4, scheme=Scheme.decimal
                                        ),
                                    }
                                    for i in df_base.columns[1:8]
                                ]
                                + [
                                    {
                                        "name": ["Supply - MBBL", i],
                                        "id": i,
                                        "type": "numeric",
                                        "format": Format(
                                            precision=4, scheme=Scheme.decimal
                                        ),
                                    }
                                    for i in df_base.columns[8:12]
                                ]
                                + [
                                    {
                                        "name": ["", i],
                                        "id": i,
                                        "type": "numeric",
                                        "format": Format(
                                            precision=4, scheme=Scheme.decimal
                                        ),
                                    }
                                    for i in df_base.columns[12:]
                                ],
                                data=df_table.to_dict("records"),
                                style_cell_conditional=[
                                    {
                                        "if": {"column_id": "Date"},
                                        "textAlign": "left",
                                        "width": "5%",
                                    },
                                ],
                                style_data_conditional=[
                                    {
                                        "if": {"row_index": "odd"},
                                        "backgroundColor": "rgb(248, 248, 248)",
                                    },
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
                                page_size=11,
                                merge_duplicate_headers=True,
                            )
                        ],
                        className="pretty_container",
                        style={"padding-bottom": "50px"},
                    ),
                    width=8,
                ),
                dbc.Col(
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.P("Select a Scenario"),
                                    dcc.Dropdown(
                                        id="scenario-dropdown",
                                        options=[{'label':k, 'value':k} for k in dic_scenaris.keys()],
                                        value=list(dic_scenaris.keys())[0],
                                    ),
                                ],
                                className="control dropdown-styles",
                            ),
                            html.Div(
                                [
                                    html.P("Select an offset Period"),
                                    dcc.Dropdown(
                                        id="month-diff-dropdown",
                                        options=[
                                            {"label": "1", "value": 1},
                                            {"label": "2", "value": 2},
                                            {"label": "3", "value": 3},
                                            {"label": "12", "value": 12},
                                            {"label": "13", "value": 13},
                                            {"label": "24", "value": 24},
                                        ],
                                        value=13,
                                    ),
                                ],
                                className="control dropdown-styles",
                            ),
                            
                            html.Div(
                                [
                                    html.P("Select a rolling period"),
                                    dcc.Dropdown(
                                        id="rolling-dropdown",
                                        options=[
                                            {"label": "1", "value": 1},
                                            {"label": "2", "value": 2},
                                            {"label": "3", "value": 3},
                                            {"label": "6", "value": 6},
                                        ],
                                        value=3,
                                        style={"font": "Asap"},
                                    ),
                                ],
                                className="control dropdown-styles",
                            ),
                        ],
                        className="pretty_container",
                        style={"margin-bottom": "9rem"},
                    ),
                ),
                dbc.Col(html.Div("One of three columns"), width=1),
                # Hidden div inside the app that stores the intermediate value
                
                html.Div(
                    id="intermediate-value-jbc",
                    children=df_base.to_json(orient="split"),
                    style={"display": "none"},
                ),
                html.Div(
                    id="hidden",
                    children=[],
                    style={"display": "none"},
                ),
            ],
            style={"background-color": "#f9f9f9"},
        ),
    ],
    className="body",
)

