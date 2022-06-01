# -*- coding: utf-8 -*-
"""
Created on Wed Jul  7 16:16:48 2021

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
import pyodbc
import sys

from fundamentals_functions import Graph, WeeklyReport

def mrs_med_layout():
    control = pd.read_csv(r"\\gvaps1\DATAROOT\data\SHARED\PALE\Dash_2.0_git\fundamentals_control.csv")

    all_fixtures = WeeklyReport().get_fixtures(vessel_type=[ 'MR1', 'MR2'])
    fixture_ts_med = all_fixtures[
        (all_fixtures.load_area.isin(['East Mediterranean', 'West Mediterranean']))
    &(all_fixtures.subclass=='Clean')].groupby(['fixture_date', 'vessel_class'])[['IMO']].count().unstack()
    fixture_ts_med.columns = [x[1] for x in fixture_ts_med]
    fixture_ts_med['MRs'] = fixture_ts_med.sum(1)
    fixture_ts_med.index = pd.to_datetime(fixture_ts_med.index)

    not_to_plot = ['2019-02', '2018-12']
    list_g = []
    for el in fixture_ts_med.columns:
        
        list_g.append(Graph().cumulative_graph(fixture_ts_med[[el]], el, control.MRs_MED.tolist(),
                                graph_title= 'Monthly MED {} Pace of Fixing'.format(el),
                                colors = [ 'DodgerBlue', 'pink', 'brown', 'orange', 'red'],
                                legend_measures='since 2019-01',
                                measures_to_show=['mean', 'quantile_75', 'quantile_25'],
                        periods_not_to_plot=not_to_plot, 
                                x_axis_title='<b>Nb of days before the end of the month',
                                y_axis_title='<b>Nb of vessels',

                                plot_all_traces=False))

    for el in list_g:
        el.layout['height']=400
        el.layout['width']=580
   
    div = html.Div(
        [
            dbc.Row(
            [
                dbc.Col(
                    html.Div(dcc.Graph(id="mr1-fx", figure=list_g[0])),
                    #className="pretty_container",
                    md=4,
                    
                ),
                dbc.Col(
                    html.Div(dcc.Graph(id="mr2-fx", figure=list_g[1])),
                    #className="pretty_container",
                    md=4,
                    
                ),
                dbc.Col(
                    html.Div(dcc.Graph(id="mrs-fx", figure=list_g[2])),
                    #className="pretty_container",
                    md=4,
                    
                ),
            ],
            #className="g-0",
            style={"background-color": "#f9f9f9", "padding":'1rem'},
            align='center'
                )
        ]
    )
    return div


app = dash.Dash(__name__, prevent_initial_callbacks=True)
# app.title = 'Shipping S&D'
app.layout = mrs_med_layout
if __name__ == "__main__":
    app.run_server(debug=True, port=3050)

