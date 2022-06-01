# -*- coding: utf-8 -*-
"""
Created on Wed May 12 12:57:26 2021

@author: pale
"""


import pandas as pd
import numpy as np
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
from calendar import monthrange
from collections import namedtuple

import plotly.express as px
from itertools import cycle

sys.path.append(r"L:\SHARED\PALE\my_python_modules\my_functions")
from my_functions_old import get_prices, My_date

# colors

palette = cycle(px.colors.qualitative.G10)

global conn
conn = pyodbc.connect("Driver={SQL Server};"
"Server=GVASQL19Lis;"
"Database = Fundamentals;"
"Trusted_Connection=yes")


# --------------------------------------------------------------------------------------------------------------------------------
def get_zones(conn):

    temp = []
    for el in ["EOS", "polygons", "polygons_1", "polygons_2", "polygons_3"]:
        sql = """SELECT DISTINCT {} FROM Fundamentals.dbo.[vessels_position_dash] 
           """.format(
            el
        )
        df = pd.read_sql(sql, conn)
        df.columns = ["zones"]
        temp.append(df)
    df = pd.concat(temp, axis=0).iloc[:, 0].unique().tolist()
    df.remove(None)
    #df.remove("nan")
    return df


# --------------------------------------------------------------------------------------------------------------------------------
def get_padd(conn):

    sql = """SELECT DISTINCT padd FROM Fundamentals.dbo.[vessels_position_dash] 
           """
    df = pd.read_sql(sql, conn).padd.tolist()
    return df


# --------------------------------------------------------------------------------------------------------------------------------


def get_index_name(conn):

    sql = """SELECT DISTINCT [index_name] FROM Fundamentals.dbo.[Shipping Prices] WHERE [source]='Litasco' 
       """
    df = pd.read_sql(sql, conn)

    return sorted(df.index_name.tolist())


# ---------------------------------------------------------------------------------------------------------------------------------
def get_unique_index_type(conn, index_name="TD3C-TCE"):

    sql = """SELECT DISTINCT [index_type] FROM Fundamentals.dbo.[Shipping Prices] WHERE index_name='{}' """.format(
        index_name
    )
    df = pd.read_sql(sql, conn)

    return df.index_type.tolist()


# --------------------------------------------------------------------------------------------------------------------------------
def sql_format(l):
    s = str(["{}".format(x) for x in l]).replace("[", "").replace("]", "")
    return s


# --------------------------------------------------------------------------------------------------------------------------------


def get_ballast_laden(conn, my_ballast, my_laden, period=None):
    """get the data from db, my_ballast and my_laden are classes"""

    sql_ballast = """SELECT  date, IMO FROM Fundamentals.dbo.vessels_position_dash
                WHERE [state1] in ({}) AND
                [vessel_type] IN ({}) AND
                [family] IN ({}) AND (
                padd IN ({}) OR EOS IN ({}) OR polygons IN ({}) OR polygons_1 IN ({})
                OR polygons_2 IN ({}) OR polygons_3 IN ({}) )

                AND [date]>{} """.format(
        my_ballast.loaded_ballast,
        my_ballast.type,
        my_ballast.clean_dirty,
        my_ballast.zones,
        my_ballast.zones,
        my_ballast.zones,
        my_ballast.zones,
        my_ballast.zones,
        my_ballast.zones,
        my_ballast.start_date,
    )

    sql_laden = """SELECT  date, IMO FROM Fundamentals.dbo.vessels_position_dash
                WHERE [state1] in ({}) AND
                [vessel_type] IN ({}) AND
                [family] IN ({}) AND (
                padd IN ({}) OR EOS IN ({}) OR polygons IN ({}) OR polygons_1 IN ({})
                OR polygons_2 IN ({}) OR polygons_3 IN ({}))
                AND [date]>{} """.format(
        my_laden.loaded_ballast,
        my_laden.type,
        my_laden.clean_dirty,
        my_laden.zones,
        my_laden.zones,
        my_laden.zones,
        my_laden.zones,
        my_ballast.zones,
        my_ballast.zones,
        my_laden.start_date,
    )

    with conn:
        laden = pd.read_sql(sql_laden, conn).groupby("date").IMO.count()
        ballast = pd.read_sql(sql_ballast, conn).groupby("date").IMO.count()

    for el in [laden, ballast]:
        el.index = pd.to_datetime(el.index)
        # el = el.set_index('date')
    if period == "D" or period == None:
        pass
    elif period == "W":
        laden = laden.resample(period).mean().round(0)
        ballast = ballast.resample(period).mean().round(0)
    else:
        laden = laden.rolling(period).mean().round(0).dropna()
        ballast = ballast.rolling(period).mean().round(0).dropna()

    dic_traces = {
        "Laden Vessels": {"data": laden, "color": "DodgerBlue"},
        "Ballast Vessels": {"data": ballast, "color": "Orange"},
        "Total Vessels": {"data": ballast + laden, "color": "White"},
    }
    return dic_traces


# --------------------------------------------------------------------------------------------------------------------------------


def make_supply_demand_graph(dic_traces):

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    for k, v in dic_traces.items():
        if k == "Total Vessels":
            dummy = True
            dummy_legend = "legendonly"
        else:
            dummy = False
            dummy_legend = True
        fig.add_trace(
            go.Scatter(
                x=v["data"].index,
                y=v["data"],
                name=k,
                showlegend=True,
                visible=dummy_legend,
                mode="lines",
                line={"width": 2, "color": v["color"]},
                hovertemplate="<br><b>Date</b>: %{x|%B %d, %Y}"
                + "<br><b>Value</b>: "
                + " %{y}<br>",
            ),
            secondary_y=dummy,
        )

    fig.update_layout(
        title={
            "text": "<b>Demand-Supply Fleet Metrics<b>",
            "font": {"size": 14},
            "x": 0.5,
            "y": 0.98,
        },
        template="plotly_dark",
        legend=dict(
            orientation="h",
            yanchor="auto",
            y=1.08,
            xanchor="left",
            x=-0.10,
            font={"size": 10},
            # bgcolor="rgba(235,233,233,0.5)",
        ),
        margin=dict(l=10, r=10, b=30, t=50, pad=4),
    )
    fig.update_xaxes(
        #   gridcolor="rgb(184, 234, 253)"
        # nticks=15,
    )
    fig.update_yaxes(
        #  gridcolor="rgb(193, 252, 186)"
        # nticks=12,
        title=dict(text="No. of vessels")
    )

    return fig


# ---------------------------------------------------------------------------------------------------------------------------
def make_balance_graph(conn, laden, ballast, index_name, index_type, unit, period=None):

    prices = get_prices(index_name, index_type, ["Litasco"], unit).fillna(
        method="ffill"
    )
    # laden.to_csv('test_p.csv')
    if period == "D" or period == None:
        pass
    elif period == "W":
        prices = prices.resample(period).mean().round(3)
    else:
        prices = prices.rolling(period).mean().round(3).dropna()

    prices = prices[laden.index[0] : laden.index[-1]]

    laden_ballast = laden - ballast
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=laden_ballast.index,
            y=laden_ballast,
            # name=k,
            showlegend=False,
            # mode="ba",
            # line={"width": 2, 'color':v['color']},
            hovertemplate="<br><b>Date</b>: %{x|%B %d, %Y}"
            + "<br><b>Value</b>: "
            + " %{y}<br>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=prices.index,
            y=prices.iloc[:, 0],
            name=prices.columns[0],
            mode="lines",
            line={"width": 2, "color": "red"},
            connectgaps=True,
            hovertemplate="<br><b>Date</b>: %{x|%B %d, %Y}"
            + "<br><b>Value</b>: "
            + str(unit)
            + " %{y}<br>",
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title={
            "text": "<b>Demand - Supply Fleet Metrics<b>",
            "font": {"size": 14},
            "x": 0.5,
        },
        template="plotly_dark",
        legend=dict(
            orientation="h",
            yanchor="auto",
            y=1.08,
            xanchor="left",
            x=-0.05,
            font={"size": 12},
            # bgcolor="rgba(235,233,233,0.5)",
        ),
        margin=dict(l=10, r=10, b=30, t=50, pad=4),
        yaxis2=dict(title="Freight, " + unit, gridcolor="rgba(184, 234, 253,0)"),
        yaxis=dict(title="Laden minus Ballast", gridcolor="rgba(184, 234, 253,0)"),
    )

    fig.update_yaxes(
        #   gridcolor="rgb(184, 234, 253)"
        # nticks=15,
    )

    return fig


# -------------------------------------------------------------------------------------------------------------------


class TonnageList:
    
    def __init__(self):
        ports = pd.read_csv(r"\\gvaps1\DATAROOT\data\SHARED\PALE\Dash\ports_signal.csv")
        self.ports = ports.ports.tolist()
        
        l=['VLCC', 'Suezmax', 'Aframax', 'Panamax', 'MR1', 'MR2']
        dic = {'VLCC':'VLCC',
                          'Suezmax':'LR3',
                          'Aframax': 'LR2',
                          'Panamax':'LR1',
                          'MR1':'MR1',
                          'MR2':'MR2'}
        values = [dic[x] for x in l]
        options = [ {"label": x, "value": y}
                    for x,y in list(zip(values, l))]  
        self.vessel_class_signal = options
        self.market_deployment = ['Spot', 'Relet', 'Contract', 'Program']
        self.days = [5, 10, 15, 20, 25, 30]
        
    @classmethod
    def _get_ports(cls,conn):
        #sql = """SELECT DISTINCT port FROM [Signal_tonnage_list] WHERE date=(SELECT MAX(date) FROM Signal_tonnage_list)
         # """
        sql = """SELECT DISTINCT port FROM Fundamentals.dbo.[Signal_tonnage_list] 
        WHERE date='2021-06-01' AND laycan_end_in_days=5
           """
        with conn:
            df = pd.read_sql(sql, conn).port.tolist()
        return df
    
    @classmethod
    def _get_vessel_class(cls, conn, port):
        sql = """SELECT DISTINCT vessel_class FROM Fundamentals.dbo.[Signal_tonnage_list] WHERE date='2021-06-01' AND laycan_end_in_days=5
           AND port='{}' """.format(port)
        with conn:
            df = pd.read_sql(sql, conn).vessel_class.tolist()
        
        if len(df)>0:
            dic = {'VLCC':'VLCC',
                  'Suezmax':'LR3',
                  'Aframax': 'LR2',
                  'Panamax':'LR1',
                  'MR1':'MR1',
                  'MR2':'MR2'}
            values = [dic[x] for x in df]
            options = [ {"label": x, "value": y}
                        for x,y in list(zip(values, df))]
                            
        else:
            options = []
        return options
    
    
    @classmethod
    def _get_tonnage_list(cls, port='Bonny', market_deployment = ['Spot', 'Relet', 'Contract', 'Program'],
                        vessel_class = 'Suezmax', subclass = 'Dirty', laycan_end_in_days = [5,10,15,20,25,30],
                        start_date='2020-01-01'):
        
        market_deployment = cls.sql_format(market_deployment)
        laycan_end_in_days = cls.sql_format(laycan_end_in_days)
        
        sql = """SELECT laycan_end_in_days, date, COUNT(imo) FROM Fundamentals.dbo.[Signal_tonnage_list] WHERE
            port='{}' AND vessel_class='{}' AND subclass='{}' AND market_deployment_point_in_time IN ({})
            AND date>='{}' AND laycan_end_in_days IN ({}) 
            GROUP BY laycan_end_in_days,date""".format(port, vessel_class, subclass, 
                                                       market_deployment, start_date, laycan_end_in_days)
        with conn:
            df = pd.read_sql(sql, conn)
        df.date = pd.to_datetime(df.date)
        df = df.pivot(index='date', columns='laycan_end_in_days')
        df.columns = [str(x[1]) for x in df.columns.ravel()]
        return df


    @staticmethod
    def sql_format(l):
        s = str(["{}".format(x) for x in l]).replace("[", "").replace("]", "")
        return s
    
    
    @classmethod
    def _graph_tonnage_list_dash(cls, df_short, port, vessel_class):
        sma_15 = df_short.fillna(method='ffill').rolling(15).mean()
        sma_15.columns = ['SMA-15 '+x for x in df_short.columns]
        sma_30 = df_short.fillna(method='ffill').rolling(30).mean()
        sma_30.columns = ['SMA-30 '+x for x in df_short.columns]

        lines_layout = ['solid', 'dash', 'dot']
        show_lines = [True, 'legendonly', 'legendonly']


        fig = make_subplots(specs=[[{"secondary_y": True}]])

        for i ,el in enumerate([df_short, sma_15, sma_30]):
            fig.add_trace(
                go.Scatter(
                    x = el.index,
                    y = el.iloc[:,0],
                    name = el.columns[0]+' Days',
                    connectgaps=True,
                    mode = 'lines',
                    visible = show_lines[i],
                    line = {'width':2, 'color':'DodgerBlue', 'dash':lines_layout[i]},
                    hovertemplate="<br><b>Date</b>: %{x|%B %d, %Y}"
                            + "<br><b>Value</b>: "
                            + " %{y}<br>"))


            fig.add_trace(
                go.Scatter(
                    x = el.index,
                    y = el.iloc[:,1],
                    name = el.columns[1],
                    visible = show_lines[i],
                    mode = 'lines',
                    connectgaps=True,
                    line = {'width':2, 'color':'red', 'dash':lines_layout[i]},
                    hovertemplate="<br><b>Date</b>: %{x|%B %d, %Y}"
                            + "<br><b>Value</b>: "
                            + " %{y}<br>"), secondary_y=True)


        fig.update_layout(
                        title={
                            "text": "<b>Tonnage List - {} - {}<b>".format(port, vessel_class),
                            "font": {"size": 14},
                            "x": 0.5,
                            "y":0.98
                        },
                        template="plotly_dark",
                        legend=dict(
                            orientation="h",
                            yanchor="auto",
                            y=1.08,
                            xanchor="left",
                            x=-0.10,
                            font={"size": 10},
                            #bgcolor="rgba(235,233,233,0.5)",
                        ),
                        yaxis=dict(
                            title='No. of vessels'),
                        margin=dict(l=10, r=10, b=30, t=60, pad=4),
                    
                    )

        return fig
    
    @classmethod
    def _get_tonnage_time_serie(cls, conn, port, vessel_class,
                               index_name, index_type,
                               start_date, market_dplt=['Spot', 'Relet', 'Contract', 'Program'],
                                source=['Litasco'], subclass='Dirty', laycan=[5],
                                default_param=False):


        if index_name.find('TCE')>0:
            unit = 'USD/DAY'
        else:
            unit='USD/T'


        prices = get_prices(index_name=index_name, index_type=index_type, source=source, unit=unit)
        temp = TonnageList()._get_tonnage_list(port=port, start_date=start_date,
                                                  vessel_class=vessel_class, subclass=subclass,
                                               market_deployment=market_dplt,
                                              laycan_end_in_days=laycan)

        x = temp.merge(prices, how='left', right_index=True, left_index=True)

        return x.copy()
        
        
        