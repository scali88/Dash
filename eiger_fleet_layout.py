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


def eiger_fleet_layout():
    eiger_fleet = pd.read_excel(r"\\gvaps1\DATAROOT\data\SHIPPING DESK\Eiger Fleet\Eiger Fleet 30Jun.xlsx",
                           usecols='A',skiprows=1)
    eiger_fleet = eiger_fleet.dropna()
    eiger_fleet.columns = ['IMO']
    eiger_fleet.IMO = eiger_fleet.IMO.astype(int)
    eiger_fleet.IMO = eiger_fleet.IMO.astype(str)
    
    
    sql="""SELECT  * FROM Fundamentals.dbo.Kpler_daily_fleet_positions
    WHERE [snapshot_date]=(
    SELECT max([snapshot_date]) FROM Fundamentals.dbo.Kpler_daily_fleet_positions) 
    """
    conn = pyodbc.connect("Driver={SQL Server};"
                        "Server=GVASQL19Lis;"
                        "Database = Fundamentals;"
                        "Trusted_Connection=yes"
                    )
    with conn:
        df_p = pd.read_sql(sql, conn)

    eiger_fleet = df_p[df_p.IMO.isin(eiger_fleet.IMO)]
    eiger_fleet.AIS_timestamp = pd.to_datetime(eiger_fleet.AIS_timestamp)
    eiger_fleet.AIS_timestamp = eiger_fleet.AIS_timestamp.dt.strftime('%Y-%m-%d %H:%M')
    eiger_fleet = eiger_fleet.sort_values(by='vessel_type')
    fig = go.Figure()
    
    dic_color = {'VLCC':'red',
                'LR3':'Orange',
                'LR2': 'Purple',
                'LR1': 'Light Green',
                'MR': 'DodgerBlue'}
    
    for r in eiger_fleet.iterrows():
        r = r[1]
        fig.add_trace(
            go.Scattergeo(
            lat = [r['Ais_latitude']],
            lon = [r['AIS_longitude']],
            name = r['name'] +' | ' +r['vessel_type'],
            mode = 'markers',
            marker_symbol = 'star-triangle-up',
            marker=dict(size=12),
            marker_line=dict(width=1, color='black'),
            hovertemplate="""<br><b>{}</b><br>Speed</b>: {} Kn</b>
            <br>AIS Date: {}""".format(r['name'], r['AIS_speed'], r['AIS_timestamp']),
            
            marker_color = dic_color[r['vessel_type']],
            ))
    
    
    fig.update_layout(
                #title_text="Eiger Fleet",
                showlegend=True,
                geo=dict(
                    # fitbounds="locations",
                    #scope="world",
                    #projection_type="equirectangular",
                    showland=True,
                    showlakes=False,
                    showcountries=True,
                    landcolor="Wheat",
                    bgcolor="Aliceblue",
                ),
               
                # paper_bgcolor='SkyBlue',
                # plot_bgcolor='SkyBlue',
                # plot_bgcolor='grey',
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=0.9,
                    xanchor="left",
                    x=-0.22,
                    font={"size": 9},
                    bgcolor="rgba(235,233,233,0.9)",
                    font_color="black",
                ),
                #width=1000,
                #height=900,
                 margin=dict(l=0, r=0, b=0, t=0, pad=0),

            )

   
    div = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.H3("   Eiger Fleet Map", style={"align": "center"}),
                        className="mini_container",
                        md=2,
                    )
                ],
                justify="center",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        className="pretty_container",
                        children=dcc.Graph(
                            id="map_eiger",
                            figure=fig,
                        ),
                        md=8,
                    ),
                   
                ],
                justify="center",
            ),
        ],
        style={"background-color": "#f9f9f9"},
    )
    return div

