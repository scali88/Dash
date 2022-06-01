
import numpy as np
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
import pyodbc
from plotly.subplots import make_subplots
import plotly.express as px
import time
import logging
import traceback

from prices_functions import (
    get_index_name,
    get_prices,
    get_prices_and_days,
    get_unique_index_type,
    get_settlement_date,
    get_source,
    get_unit,
    layout,
    layout_contract_analysis,
    time_serie_to_year,
    seasonality,
    seasonality_graph,
    scatter_graph,
    get_fwd_curve_from_db_price,
    get_fwd_dates_price,
    hexa_to_rgb,
    plotly_drawing
)
from prices_layout import prices_layout

global conn
conn = pyodbc.connect(
"Driver={SQL Server};"
"Server=GVASQL19Lis;"
"Database = Fundamentals;"
"Trusted_Connection=yes")

app = dash.Dash(__name__, prevent_initial_callbacks=True)
# app.title = 'Shipping S&D'
app.layout = prices_layout


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

    if value in [5, 7, 9]:
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
                
                #print(data, years, f)
                
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

            # compare two contratcs
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

            else:
                pass

        else:
            pass
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

                fig = layout(fig)
                return dcc.Graph(figure=fig)

            # seasonal monthly
            elif graph_type == 3:

                try:
                    spread = pd.concat([spread1, spread2], join="outer", axis=1)
                except:
                    pass

                data, years = seasonality(
                    spread, seasonality_period="month", selected_years=slct_years
                )

                fig = seasonality_graph(
                    data=data, years=years, seasonality="month", index_name=index_name1
                )
                return dcc.Graph(figure=fig)

            # seasonal weekly
            elif graph_type == 5:
                spread = pd.concat([spread1, spread2], join="outer", axis=1)
                data, years = seasonality(
                    spread, seasonality_period="week", selected_years=slct_years
                )
                fig = seasonality_graph(
                    data=data, years=years, index_name=index_name1, seasonality="week"
                )
                return dcc.Graph(figure=fig)

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
                fig = seasonality_graph(
                    data=data, years=years, index_name=index_name1, seasonality="day"
                )
                return dcc.Graph(figure=fig)

            # scatter plot
            elif graph_type == 11:
                spread = pd.concat([spread1, spread2], join="outer", axis=1)
                fig = scatter_graph(spread, selected_periods=slct_years)
                return dcc.Graph(figure=fig)

            else:
                pass

        else:
            pass
    except Exception as e:
       
        print(e)
        
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
                    temp.settlement_date[0] = 'cash'
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


if __name__ == "__main__":
    app.run_server(debug=True, port=3060)
