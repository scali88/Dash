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
index_name = "TC6-TCE"
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

prices = get_prices(index_name, index_type, ["Litasco"], unit).fillna(
        method="ffill"
    )
print(prices)