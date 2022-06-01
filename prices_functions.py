# -*- coding: utf-8 -*-
"""
Created on Tue Mar 23 15:06:45 2021

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

sys.path.append(r"L:\SHARED\PALE\my_python_modules\my_functions")
from my_functions_old import My_date

import plotly.express as px
from itertools import cycle

# colors
palette = cycle(px.colors.qualitative.G10)

global conn
conn = pyodbc.connect("Driver={SQL Server};"
"Server=GVASQL19Lis;"
"Database = Fundamentals;"
"Trusted_Connection=yes")


def get_prices(
    conn,
    index_name="TD3_eiger-TCE",
    index_type=["M1", "cash"],
    source=["Litasco", "Baltic"],
    unit="USD/DAY",
):
    """return price and index"""
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

    index_month = [
        dt.datetime.strptime(x, "%b-%Y") for x in index_type if x[:3] in months
    ]
    index_month = [x.replace(day=monthrange(x.year, x.month)[1]) for x in index_month]
    index_month = [x.strftime("%Y-%m-%d") for x in index_month]

    if index_month != []:
        index_month_sql = (
            str(["{}".format(x) for x in index_month]).replace("[", "").replace("]", "")
        )
        sql_month = """SELECT * FROM Fundamentals.dbo.[Shipping Prices] 
            WHERE index_name='{}'
            AND [settlement_date] IN ({}) AND source='Litasco' 
            AND index_type<>'cash' AND unit='{}' AND settlement_month>0 """.format(
            index_name, index_month_sql, unit
        )
        df_m = pd.read_sql(sql_month, conn)
        df_m.index_type = df_m.settlement_date.apply(
            lambda x: dt.datetime.strptime(x, "%Y-%m-%d").strftime("%b-%Y")
        )
    else:
        df_m = pd.DataFrame()

    index_type_sql = (
        str(["{}".format(x) for x in index_type]).replace("[", "").replace("]", "")
    )
    source = str(["{}".format(x) for x in source]).replace("[", "").replace("]", "")

    sql = """SELECT * FROM Fundamentals.dbo.[Shipping Prices] 
        WHERE index_name='{}'
        AND [index_type] IN ({}) AND source IN ({}) AND unit='{}' """.format(
        index_name, index_type_sql, source, unit
    )
    df = pd.read_sql(sql, conn)
    df = pd.concat([df, df_m], join="outer", axis=0)
    df = df[["date", "index_name", "index_type", "source", "value"]]
    td3 = df.pivot(columns=["index_type", "source"], values=["value"], index="date")
    col = [
        index_name + str("-") + str(x[1]) + "-" + x[2] + "(" + unit + ")"
        for x in td3.columns.ravel()
    ]
    col = [x.replace("-Litasco", "") for x in col]
    td3.columns = col
    # td3[index_type] = td3.mean(axis=1)
    td3.index = pd.to_datetime(td3.index)
    # td3 = td3[[index_type]]
    return td3


def get_unique_index_type(conn, index_name="TD3C-TCE"):
    
    
    sql = """SELECT DISTINCT [index_type] FROM Fundamentals.dbo.[Shipping Prices] 
    WHERE index_name='{}' """.format(
        index_name
    )
    df = pd.read_sql(sql, conn)

    return df.index_type.tolist()


def get_index_name(conn):

    sql = """SELECT DISTINCT [index_name] FROM Fundamentals.dbo.[Shipping Prices] 
       """
    df = pd.read_sql(sql, conn)

    return sorted(df.index_name.tolist())


def get_settlement_date(conn, index_name):

    sql = """SELECT DISTINCT [settlement_date] FROM Fundamentals.dbo.[Shipping Prices] WHERE index_name='{}' AND [index_type]<>'cash' """.format(
        index_name
    )
    df = pd.read_sql(sql, conn)
    l = df.settlement_date.apply(
        lambda x: dt.datetime.strptime(x, "%Y-%m-%d").strftime("%b-%Y")
    ).tolist()
    try:
        l.remove('Jan-1900')
    except:
        pass
    return l


def get_source(conn, index_name, index_type):
    
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
    index_month = [
        dt.datetime.strptime(x, "%b-%Y") for x in index_type if x[:3] in months
    ]
    if len(index_month)>0:
        return ['Litasco']
    else:
        index_type = (
            str(["{}".format(x) for x in index_type]).replace("[", "").replace("]", "")
        )
        sql = """SELECT DISTINCT [source] FROM Fundamentals.dbo.[Shipping Prices] WHERE index_name='{}' AND [index_type] IN ({}) """.format(
            index_name, index_type
        )
        df = pd.read_sql(sql, conn)
        return df.source.tolist()


def get_unit(conn, index_name, index_type, source):
    
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

    index_month = [dt.datetime.strptime(x, "%b-%Y") for x in index_type if x[:3] in months]
    index_month = [x.replace(day=monthrange(x.year, x.month)[1]) for x in index_month]
    index_month = [x.strftime("%Y-%m-%d") for x in index_month]
    
    if index_month != []:
        index_month_sql = (
            str(["{}".format(x) for x in index_month]).replace("[", "").replace("]", "")
        )
        sql = """SELECT DISTINCT [unit] FROM Fundamentals.dbo.[Shipping Prices] WHERE index_name='{}' AND [settlement_date] IN ({}) 
        AND [source]=='Litasco' """.format(
        index_name, index_month_sql, source
        )
        df = pd.read_sql(sql, conn)
    else:
        index_type = (
            str(["{}".format(x) for x in index_type]).replace("[", "").replace("]", "")
        )
        source = str(["{}".format(x) for x in source]).replace("[", "").replace("]", "")
        sql = """SELECT DISTINCT [unit] FROM Fundamentals.dbo.[Shipping Prices] WHERE index_name='{}' AND [index_type] IN ({}) 
        AND [source] IN ({})""".format(
            index_name, index_type, source
        )
        df = pd.read_sql(sql, conn)
    return df.unit.tolist()


def layout_contract_analysis(fig, index_name1='', index_name2='', index_name3=''):

    if index_name2!='' or index_name3!='':
        indexs = index_name1+'_'+index_name2+'_'+index_name3
    else:
        indexs = index_name1
    
    fig.update_layout(
        title={"text": "<b>Historic graph-{}<b>".format(indexs), "font": {"size": 14}, "x": 0.5},
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
 
    fig.update_yaxes(autorange=True, fixedrange=False, gridcolor="rgb(184, 234, 253)")
    fig.update_xaxes(
        autorange='reversed',
        gridcolor="rgb(193, 252, 186)",
    )

    return fig

def layout(fig, index_name1='', index_name2='', index_name3=''):

    if index_name2!='' or index_name3!='':
        indexs = index_name1+'_'+index_name2+'_'+index_name3
    else:
        indexs = index_name1
    
    fig.update_layout(
        title={"text": "<b>Historic graph-{}<b>".format(indexs), "font": {"size": 14}, "x": 0.5},
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
    # Add range slider
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list(
                    [
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(count=6, label="6m", step="month", stepmode="backward"),
                        dict(count=1, label="YTD", step="year", stepmode="todate"),
                        dict(count=1, label="1y", step="year", stepmode="backward"),
                        dict(step="all"),
                    ]
                )
            ),
            #rangeslider=dict(visible=True),
           # 'type="date",
        )
    )
    fig.update_yaxes(autorange=True, fixedrange=False, gridcolor="rgb(184, 234, 253)")
    fig.update_xaxes(
        #dtick="M3",
        autorange=True,
        ticklabelmode="period",
        #tickformat="%b\n%Y",
        gridcolor="rgb(193, 252, 186)",
    )

    return fig


def time_serie_to_year(df):
    """ convert a historic time serie to a dict of df per year, index need to be datetime"""
    col = df.columns
    years = df[[col[0]]].groupby(df.index.year).sum().index.tolist()
    dic = {}

    for y in years:
        dic[str(y)] = df[df.index.year == y]

    return dic

def seasonality(
    price,
    seasonality_period="month",
    selected_years=None
    
):
    """convert df to a yearly dataframe"""

    ## On cree un graph de sesonalite si on a qu'un indexname/indextype
    if price.shape[1] == 1:
        temp = price.copy()
        index_name = temp.columns[0]
        temp["year"] = temp.index.year
        average = seasonality_period
        

        if average == "week":
            temp["week"] = temp.index.isocalendar().week
            temp = temp[temp.week < 53]
            temp = temp.groupby(["week", "year"], as_index=False).mean()
            pivot = temp.pivot(values=index_name, index="week", columns=["year"])

        elif average == "month":
            temp["month"] = temp.index.month
            temp = temp.groupby(["month", "year"], as_index=False).mean()
            pivot = temp.pivot(values=index_name, index="month", columns=["year"])

        elif average == "day":
            # def days_since_dte(x, year):
            #    return (x-dt.datetime(year,1,1)).days
            # temp['day'] = temp.reset_index().apply(lambda x: days_since_dte(x['date'], x['year']), axis=1)
            temp["week"] = temp.index.isocalendar().week
            temp["day"] = temp.index.isocalendar().day
            temp = temp[temp.week < 53]
            pivot = temp.pivot(
                values=index_name, index=["week", "day"], columns=["year"]
            )

        pivot = pivot.dropna(axis=1, how='all')
        years = sorted(set(pivot.columns))
        years_av = [x for x in years if x!=2020]
        # pivot['Max'] = pivot[years].interpolate().max(axis=1)
        pivot["Max"] = pivot[years_av].fillna(pivot[years].max(axis=1)).max(axis=1)
        pivot["Min"] = pivot[years_av].fillna(pivot[years].min(axis=1)).min(axis=1)
        if selected_years == None:
            length = len(years_av[-5 :])
            pivot[str(length) + "Year-Avg(without 2020)"] = (
                pivot[years_av[-5 :]].mean(axis=1)
            )
        else:
            pivot["Slct Years"] = pivot[selected_years].mean(axis=1)
        pivot = pivot.round(2)
        return pivot, years

    else:
        dic_year = time_serie_to_year(price)
        years = None
        return dic_year, years



def seasonality_graph(data, index_name, years=None, seasonality="month", fwd_tuple= None):
    """plot the seasonality graph"""
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
    palette = cycle(px.colors.qualitative.Set2)
    palette_fwd = cycle(['#990000', '#537c30', 'purple', 'orange'])
    if type(data) == dict:

        dic_year = data
        fig_y = go.Figure()
        if seasonality == "day":
            l = []
            for k, v in dic_year.items():
                temp = v.groupby(
                    [v.index.isocalendar().week, v.index.isocalendar().day]
                ).mean()
                temp.columns = [str(k) + str("-") + x for x in temp.columns]
                l.append(temp)
            temp = pd.concat(l, axis=1)
            temp = temp.reset_index(drop=True)

            for el in temp.columns:
                fig_y.add_trace(
                    go.Scatter(
                        x=temp.index,
                        y=temp[el],
                        name=el,
                        mode="lines",
                        line={"width": 2},
                        hovertemplate="<br><b>Period </b>: %{x}"
                        + "<br><b>Value</b>: $%{y}<br>"
                        # fill='tozeroy'
                    )
                )
        else:
            for k, v in dic_year.items():
                for el in v.columns:

                    if seasonality == "month":
                        temp = v.groupby(v.index.month).mean()
                        index = months
                    elif seasonality == "week":
                        temp = v.groupby(v.index.isocalendar().week).mean()
                        index = temp.index

                    fig_y.add_trace(
                        go.Scatter(
                            x=index,
                            y=temp[el],
                            name=str(k) + str("-") + el,
                            mode="lines+markers",
                            line={"width": 2},
                            hovertemplate="<br><b>Period </b>: %{x}"
                            + "<br><b>Value</b>: $%{y}<br>"
                            # fill='tozeroy'
                        )
                    )
        fig_y.update_layout(
            title={"text": "<b>Seasonality graph<b>", "font": {"size": 14}, "x": 0.55},
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
        )
        fig_y.update_xaxes(
            gridcolor="rgb(184, 234, 253)"
            # nticks=12,
        )
        fig_y.update_yaxes(
            gridcolor="rgb(193, 252, 186)"
            # nticks=12,
        )

        return fig_y

    else:

        fig = go.Figure()
        size = 4
        connect = False
        if seasonality == "month":
            index = months
        elif seasonality == "week":
            index = data.index

        if seasonality == "day":

            # index=data.reset_index().index
            data = data.reset_index()
            index = data.index
            size = 2
            connect = True

            # plotting trace
            
            tick_name = [
                "Week-" + str(x[0]) + " Day-" + str(x[1])
                for x in tuple(zip(data.week, data.day))
            ]

            fig.add_trace(
                go.Scatter(
                    x=index,
                    y=data["Max"],
                    fill=None,
                    mode=None,
                    name="Max",
                    line_color="lightgray",
                    showlegend=True,
                    connectgaps=connect,
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=index,
                    y=data["Min"],
                    fill="tonexty",  # fill area between trace0 and trace1
                    mode=None,
                    line_color="lightgray",
                    showlegend=True,
                    name="Min",
                    connectgaps=connect,
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=index,
                    y=data.iloc[:, -1],
                    name=data.iloc[:, -1].name,
                    line=dict(color="black", width=2, dash="dot"),
                    hovertemplate="<br><b>Period </b>: %{x}"
                    + "<br><b>Value</b>: $%{y}<br>",
                )
            )
            for el in years:
                
                dates = data.apply(
                    lambda x: dt.datetime.strptime(
                        str(el) + "-W" + str(int(x["week"])) + "-" + str(int(x["day"])),
                        "%Y-W%W-%w",
                    ),
                    axis=1,
                )
                if el==My_date().date.year:
                    colors='red'
                else:
                    colors = next(palette)
                
                if el>2018:
                    show = True
                else:
                    show = 'legendonly'
                    
                fig.add_trace(
                    go.Scatter(
                        x=index,
                        y=data[el],
                        visible=show,
                        name=str(el),
                        line=dict(width=size, color=colors),
                        hovertemplate="<br><b>%{text}</b>"
                        + "<br><b>Value</b>: $%{y}<br>",
                        text=[
                            "{}".format(dates[i].strftime("%Y-%m-%d"))
                            for i in data.index
                        ],
                        connectgaps=connect,
                    )
                )
            fig.update_layout(
                xaxis=dict(
                    tickmode="array", tickvals=index[::40], ticktext=tick_name[::40]
                )
            )
        else:
            fig.add_trace(
                go.Scatter(
                    x=index,
                    y=data["Max"],
                    fill=None,
                    mode = 'lines',
                    line_color="lightgray",
                    showlegend=True,
                    name="Max",
                    connectgaps=connect,
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=index,
                    y=data["Min"],
                    mode = 'lines',
                    fill="tonexty",  # fill area between trace0 and trace1
                    line_color="lightgray",
                    showlegend=True,
                    name="Min",
                    connectgaps=connect,
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=index,
                    y=data.iloc[:, -1],
                    mode = 'lines',
                    name=data.iloc[:, -1].name,
                    line=dict(color="black", width=2, dash="dot"),
                    hovertemplate="<br><b>Period </b>: %{x}"
                    + "<br><b>Value</b>: $%{y}<br>",
                )
            )
            for el in years:
                if el==My_date().date.year:
                    colors='red'
                else:
                    colors = next(palette)
                
                if el>2018:
                    show = True
                else:
                    show = 'legendonly'
                    
                fig.add_trace(
                    go.Scatter(
                        x=index,
                        y=data[el],
                        name=el,
                        visible=show,
                        mode = 'lines',
                        line=dict(width=size, color=colors),
                        hovertemplate="<br><b>Period </b>: %{x}"
                        + " "
                        + str(el)
                        + "<br><b>Value</b>: $%{y}<br>",
                        connectgaps=connect,
                    )
                )
            if fwd_tuple is not None:
                data, years = fwd_tuple
                for el in years:
                    fig.add_trace(
                    go.Scatter(
                        x=index,
                        y=data[el],
                        name=str(el)+'-fwd',
                        visible=show,
                        mode = 'lines',
                        line=dict(width=3, color=next(palette_fwd),
                                 dash='dash'),
                        hovertemplate="<br><b>Period </b>: %{x}"
                        + " "
                        + str(el)+'-fwd'
                        + "<br><b>Value</b>: $%{y}<br>",
                        connectgaps=connect,
                    )
                )
                    

        fig.update_layout(
            title={
                "text": "<b>Seasonality graph-{}<b>".format(index_name),
                "font": {"size": 14},
                "x": 0.55,
            },
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
        )
        fig.update_xaxes(
            gridcolor="rgb(184, 234, 253)"
            # nticks=12,
        )
        fig.update_yaxes(
            gridcolor="rgb(193, 252, 186)"
            # nticks=12,
        )
        return fig

def scatter_graph(price, selected_periods=None):
    if selected_periods != None:
        price = price[price.index.month.isin(selected_periods)]
    else:
        pass
    price['year'] = price.index.year
    price.year  = price.year.astype('category')
    price['date'] = price.index.strftime('%Y-%m-%d')
    
    fig = px.scatter(price, x=price.columns[0], y=price.columns[1], trendline="ols",
                     color_discrete_sequence=px.colors.qualitative.G10,color=price.year,
                    hover_data = ['date'])
    
    fig1 = px.scatter(price, x=price.columns[0], y=price.columns[1], 
                      color_discrete_sequence=px.colors.qualitative.G10, trendline="ols", 
                    )
    fig1.data[1]['marker']['color'] = 'black'
    fig.add_trace(fig1.data[1])
    fig.update_layout(
        title={"text": "<b>Scatter graph<b>", "font": {"size": 14}, "x": 0.55},
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
    )
    fig.update_xaxes(
        gridcolor="rgb(184, 234, 253)"
        # nticks=12,
    )
    fig.update_yaxes(
        gridcolor="rgb(193, 252, 186)"
        # nticks=12,
    )
    return fig


def get_fwd_curve_from_db_price(conn, index_name, date="last"):
    """get forward curve for a specific route on a specific date"""

    index_month = ['cash']+["M" + str(i) for i in range(1,25)]
    index_month_sql = (
        str(["{}".format(x) for x in index_month]).replace("[", "").replace("]", "")
    )

    if date != "last":
        try:
            sql = """SELECT * FROM Fundamentals.dbo.[Shipping Prices] 
        WHERE index_name='{}' 
        AND date='{}' AND source='Litasco' AND index_type IN ({}) """.format(
                index_name, date, index_month_sql
            )
            df = pd.read_sql(sql, conn)
        except:
            return print("error with requested index or date")
    else:
        try:
            sql = """SELECT * FROM Fundamentals.dbo.[Shipping Prices] 
            WHERE index_name='{}' AND source='Litasco'
            AND index_type IN ({})
            AND date=(SELECT MAX(date) FROM Fundamentals.dbo.[Shipping Prices] WHERE index_name='{}') """.format(
                index_name, index_month_sql, index_name
            )
            df = pd.read_sql(sql, conn)
        except:
            return print("error with requested index or date")
    df = df.sort_values(by="settlement_date")
    df.settlement_date = df.settlement_date.apply(lambda x: dt.datetime.strptime(x,'%Y-%m-%d').strftime(format='%b-%Y'))
    return df


def get_fwd_dates_price(conn, index_name="TD3_eiger-TCE"):
    """return the list of the fwd dates available"""

    try:
        sql = """SELECT DISTINCT [date] FROM Fundamentals.dbo.[Shipping Prices] 
        WHERE index_name='{}' 
        AND source='Litasco'
        AND index_type='M1' """.format(
            index_name
        )
        df = pd.read_sql(sql, conn)
        df = df.sort_values(by="date", ascending=False)
        return df.date.tolist()
    except:
        return []


def hexa_to_rgb(hexx, opacity=None):
    h = hexx.lstrip("#")
    if opacity != None:
        r = [int(h[i : i + 2], 16) for i in (0, 2, 4)]
        r.append(opacity)
        return tuple(r)
    else:
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))



def deco_plotly_drawing(fonc):
    '''decorateur permettant de dessiner sur le graph plotly et de modifier le titre'''
    def new_graph(*args, **kwargs):
        
        fig = fonc(*args, **kwargs)
        
        fig.update_layout(dragmode='zoom',
                  # style of new shapes
                  newshape=dict(line_color='black',
                                fillcolor='#FFC2B9',
                                opacity=0.5))
        config = {'edits':{'legendPosition':False, 'titleText':True},
                    'modeBarButtonsToAdd':['drawline',
                                                'drawopenpath',
                                                'drawclosedpath',
                                                'drawcircle',
                                                'drawrect',
                                                'eraseshape'],'displaylogo': False
                                               }
        return fig, config
    return new_graph

@deco_plotly_drawing
def plotly_drawing(fonc):
    '''return an udpated output to draw on plotly graph'''
    return fonc

def get_prices_and_days(
    conn,
    index_name="TD3_eiger-TCE",
    index_type=["cash"],
    source=["Litasco"],
    unit="USD/DAY",
):
    """return prices and nb of days before settlement"""
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
    
    index_month = [dt.datetime.strptime(x, "%b-%Y") for x in index_type if x[:3] in months]
    index_month = [x.replace(day=monthrange(x.year, x.month)[1]) for x in index_month]
    index_month = [x.strftime("%Y-%m-%d") for x in index_month]

    if index_month != []:
        index_month_sql = (
            str(["{}".format(x) for x in index_month]).replace("[", "").replace("]", "")
        )
        sql_month = """SELECT * FROM Fundamentals.dbo.[Shipping Prices] 
            WHERE index_name='{}'
            AND [settlement_date] IN ({}) AND source='Litasco' 
            AND index_type<>'cash' AND unit='{}' and settlement_month>0 """.format(
            index_name, index_month_sql, unit
        )
        df_m = pd.read_sql(sql_month, conn)
        df_m.index_type = df_m.settlement_date.apply(
            lambda x: dt.datetime.strptime(x, "%Y-%m-%d").strftime("%b-%Y")
        )
        df_m.settlement_date = pd.to_datetime(df_m.settlement_date)
        df_m.date = pd.to_datetime(df_m.date)
    else:
        df_m = pd.DataFrame()

    index_type_sql = (
        str(["{}".format(x) for x in index_type]).replace("[", "").replace("]", "")
    )
    source = str(["{}".format(x) for x in source]).replace("[", "").replace("]", "")

    sql = """SELECT * FROM Fundamentals.dbo.[Shipping Prices] 
        WHERE index_name='{}'
        AND [index_type] IN ({}) AND source IN ({}) AND unit='{}' """.format(
        index_name, index_type_sql, source, unit
    )
    df = pd.read_sql(sql, conn)
    df = df[df.index_type!='cash']
    df.date = pd.to_datetime(df.date)
    df.settlement_date = pd.to_datetime(df.settlement_date)
        
    df = pd.concat([df, df_m], join="outer", axis=0)
    
    
    df['days_diff'] = (df.settlement_date - df.date).dt.days
    td3 = df.pivot(columns=["index_type"], values=["value"], index="days_diff")
    
    col = [
        index_name + str("-") + str(x[1])+ "(" + unit + ")"
        for x in td3.columns.ravel()
    ]
    
    td3.columns = col
    
    return td3