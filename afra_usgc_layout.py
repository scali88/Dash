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

def afra_usgc_layout():
    control = pd.read_csv(r"\\gvaps1\DATAROOT\data\SHARED\PALE\Dash_2.0_git\fundamentals_control.csv")

    list_g = []
    for el in ['Aframax', 'Suezmax', 'VLCC']:
        all_fixtures = WeeklyReport().get_fixtures(vessel_type=[el])

        fixtures_ts_us = all_fixtures[(all_fixtures.load_area.isin(['US Gulf']))&
        (all_fixtures.subclass=='Dirty')].groupby('fixture_date')[['IMO']].count()
        fixtures_ts_us.index = pd.to_datetime(fixtures_ts_us.index)


        if el=='VLCC':
            not_to_plot = ['2020-04', '2019-03']
        elif el == 'USGC':
            not_to_plot = ['2019-02', '2018-12']
        else:
            not_to_plot = []
        list_g.append(Graph().cumulative_graph(fixtures_ts_us, 'IMO', control.Afra_USGC.tolist(),
                                graph_title= 'Monthly USGC {} Pace of Fixing'.format(el),
                                colors = [ 'DodgerBlue', 'yellow', 'brown', 'orange', 'red'],
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
                    html.Div(dcc.Graph(id="afra-fx", figure=list_g[0])),
                    #className="pretty_container",
                    md=4,
                    
                ),
                dbc.Col(
                    html.Div(dcc.Graph(id="suez-fx", figure=list_g[1])),
                    #className="pretty_container",
                    md=4,
                    
                ),
                dbc.Col(
                    html.Div(dcc.Graph(id="vlcc-fx", figure=list_g[2])),
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
app.layout = afra_usgc_layout
if __name__ == "__main__":
    app.run_server(debug=True, port=3050)

