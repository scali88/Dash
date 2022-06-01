# -*- coding: utf-8 -*-
"""
Created on Mon Mar 22 09:40:25 2021

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
import sys
import datetime as dt
import pickle
import glob
import json
import dash_daq as daq
from itertools import cycle
import plotly.express as px

sys.path.append(r"L:\SHARED\PALE\my_python_modules\my_functions")
from my_functions import My_date
from supply_functions import fleet_dev_per_ship, orderbook, individual_tankers, addition, demolition, scenario_age, scenario_constant, layout_plotly
from supply_layout import supply_layout


app = dash.Dash(__name__, prevent_initial_callbacks=True)
app.title = 'Shipping S&D'
app.layout=supply_layout


#change ships options
@app.callback(
    Output("ship-dropdown", "options"),
    Input("clean-dropdown", "value"),
    Input("hidden-div", 'children')
)
def ship_options(value, json_data):
    df = pd.read_json(json.loads(json_data[0])[value]['fleet_dev'][0])
        
    options=[{'label':x.replace('_mbbl', '').upper(), 'value':x.replace('_mbbl', '') } for x in df.columns if x!='state']
    
    return options

#change ships value
@app.callback(
    Output("ship-dropdown", "value"),
    Input("clean-dropdown", "value"),
)
def ship_value(clean):
    
    if clean:    
        return 'total'

# change slider values
        
@app.callback(
    Output("my-slider", "children"),
    Input("clean-dropdown", "value"),
    Input("ship-dropdown", "value"),
    Input("mbbl-button", "value"),
    Input("hidden-div", 'children')

)
def slider_value(clean, ship, mbbl, json_data ):
    
     ## fetch the right element of the tuple 
    if mbbl == 'mbbl':
        dummy = 0
    else:
        dummy = 1
     
    unit = mbbl
    ship_type = ship + "_" + unit
    
    df = pd.read_json(json.loads(json_data[0])[clean]['demolition'][dummy])
    if ship=='total':
        marks = {str(round(df[ship_type].mean(), 2)):'Mean',
                               str(round(df[ship_type].quantile(0.5), 2)):'2-Q',
                                   str(round(df[ship_type].quantile(0.75), 2)):'3-Q'}
    else:
        marks = {str(round(df[ship_type].mean(), 2)):'Mean',
                               str(round(df[ship_type].quantile(0.5), 2)):'2-Q',
                                   str(round(df[ship_type].quantile(0.75), 2)):'3-Q'}
    
    child = daq.Slider(id='constant-slider',
                    min=0,
                    max=df[ship_type].mean()*3,
                    value=round(df[ship_type].mean(), 2),
                    handleLabel={"showCurrentValue": True,"label": "Value"},
                    marks=marks,
                    step=0.1, size=250
                )
    return child
    

    
###################################
#         Demolition graph        #
###################################        
@app.callback(
    Output("graph-demo", "figure"),
    Input("clean-dropdown", "value"),
    Input("ship-dropdown", "value"),
    Input("mbbl-button", "value"),
    Input("hidden-div", 'children')
)
def demo_graph(clean, ship, mbbl, json_data):
    
    ## fetch the right element of the tuple 
    if mbbl == 'mbbl':
        dummy = 0
    else:
        dummy = 1
        
    df = pd.read_json(json.loads(json_data[0])[clean]['demolition'][dummy])
    
    unit = mbbl
    unit_u = unit.upper()
    ship_type = ship + "_" + unit
    
    if clean == 'crude':clean_allias = 'Dirty' 
    else: clean_allias='Clean'
    
    fig_demo = go.Figure()

    fig_demo.add_trace(
        go.Scatter(
            x=df.index,
            y=df[ship_type],
            name="Demolition - " + unit_u,
            mode="lines",
            line={"width": 1, "color": "DodgerBlue"},
            # fill='toself'
        )
    )

    fig_demo.add_trace(
        go.Scatter(
            x=df.index,
            y=df[ship_type].rolling(window=24).quantile(0.25),
            name="25% - Quantile",
            line={
                "width": 1,
                "color": "grey",
            },
        )
    )
    fig_demo.add_trace(
        go.Scatter(
            x=df.index,
            y=df[ship_type].rolling(window=24).quantile(0.75),
            name="75% - Quantile",
            line={"width": 1, "color": "grey"},
            fill="tonexty",
        )
    )

    fig_demo.add_trace(
        go.Scatter(
            x=df.index,
            y=df[ship_type].rolling(window=24).quantile(0.5),
            name="24-Month rolling Median",
            line={"width": 2, "color": "black", "dash": "dot"},
        )
    )

    fig_demo.update_layout(template='ggplot2',
        title={
            "text": "<b>{} - {} Demolition in {}<b>".format(ship.upper(), clean_allias, unit_u),
            "font": {"size": 14},
            "x": 0.5,
        },
        # template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="left", x=0),
        margin=dict(l=30, r=10, b=50, t=30, pad=4),
    )
    
    
    return fig_demo

#########################################
#            ADDTION graph              #
#########################################
@app.callback(
    Output("graph-add", "figure"),
    Input("clean-dropdown", "value"),
    Input("ship-dropdown", "value"),
    Input("mbbl-button", "value"),
    Input("hidden-div", 'children')
)
def addition_graph(clean, ship, mbbl, json_data):
    
    ## fetch the right element of the tuple 
    if mbbl == 'mbbl':
        dummy = 0
    else:
        dummy = 1
        
    df = pd.read_json(json.loads(json_data[0])[clean]['addition'][dummy])
    df.fillna(0, inplace=True)
    unit = mbbl
    unit_u = unit.upper()
    ship_type = ship + "_" + unit
    
    if clean == 'crude':clean_allias = 'Dirty' 
    else: clean_allias='Clean'
    
    fig_add = go.Figure()

    fig_add.add_trace(
        go.Scatter(
            x=df[df.state == "deliveries"].index,
            y=df[df.state == "deliveries"][ship_type],
            name="Deliveries - " + unit_u,
            mode="lines",
            line={"width": 1, "color": "DodgerBlue"},
            # fill='toself'
        )
    )

    fig_add.add_trace(
        go.Scatter(
            x=df[df.state == "orderbook"].index,
            y=df[df.state == "orderbook"][ship_type],
            name="orderbook - " + unit_u,
            mode="lines",
            line={"width": 2, "color": "firebrick"},
            # fill='toself'
        )
    )

    fig_add.add_trace(
        go.Scatter(
            x=df.index,
            y=df[ship_type].rolling(window=24).quantile(0.25),
            name="25% - Quantile",
            line={
                "width": 1,
                "color": "grey",
            },
        )
    )
    fig_add.add_trace(
        go.Scatter(
            x=df.index,
            y=df[ship_type].rolling(window=24).quantile(0.75),
            name="75% - Quantile",
            line={"width": 1, "color": "grey"},
            fill="tonexty",
        )
    )

    fig_add.add_trace(
        go.Scatter(
            x=df.index,
            y=df[ship_type].rolling(window=24).quantile(0.5),
            name="24-Month rolling Median",
            line={"width": 2, "color": "black", "dash": "dot"},
        )
    )

    fig_add.update_layout(template='ggplot2',
        title={
            "text": "<b>{} - {} Deliveries+Orderbook in {}<b>".format(ship.upper(), clean_allias, unit_u),
            "font": {"size": 14},
            "x": 0.5,
        },
        # template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="left", x=0),
        margin=dict(l=30, r=10, b=50, t=30, pad=4),
    )
    
    return fig_add

#save sceanrio change in hidden div
@app.callback(
    Output("hidden-div-sce", "children"),
    Input("clean-dropdown", "value"),
    Input("mbbl-button", "value"),
    Input('age-dropdown', 'value'),
    Input("hidden-div", 'children'),
)

def hidden_scenario(clean, mbbl, age, json_data):
    
    ## fetch the right element of the tuple 
    if mbbl == 'mbbl':
        dummy = 0
    else:
        dummy = 1
        
    df = pd.read_json(json.loads(json_data[0])[clean]['individual_tankers'][dummy])
   
    dic_sce = scenario_age(df, age)
    return json.dumps({k:v.to_json() for k, v in dic_sce.items()})
  



    
##########################
#       Scenario         #
##########################

@app.callback(
    Output("graph-sce", "figure"),
    Input("clean-dropdown", "value"),
    Input("mbbl-button", "value"),
    Input("ship-dropdown", "value"),
    Input("hidden-div", 'children'),
    Input("hidden-div-sce", 'children'),
    Input('constant-slider', 'value')
)
    
def graph_sce(clean, mbbl, ship, json_data, sce_data, constant):
    
    if mbbl == 'mbbl':
        dummy = 0
    else:
        dummy = 1
    
    unit = mbbl
    unit_u = unit.upper()
    ship_type = ship + "_" + unit
    if clean == 'crude':clean_allias = 'Dirty' 
    else: clean_allias='Clean'
    
    crude_fleet_mbbl = pd.read_json(json.loads(json_data[0])[clean]['fleet_dev'][dummy])
    orderbook_mbbl = pd.read_json(json.loads(json_data[0])[clean]['orderbook'][dummy])
    
    
    orderbook_mbbl.index = pd.DatetimeIndex(orderbook_mbbl.index)
    orderbook_mbbl.fillna(0, inplace=True)
    #crude_fleet_mbbl.index = pd.to_datetime(crude_fleet_mbbl.index)
    
    fig_sce = go.Figure()
    dic_sce = json.loads(sce_data)
    
    x = scenario_constant(crude_fleet_mbbl, orderbook_mbbl, constant)
    
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
            #f = None
        else:
            f = None
        
        v = pd.read_json(v)
        
        
        s = v.copy()
        s.index = pd.DatetimeIndex(s.index)
        
        scenario = (orderbook_mbbl.resample("M").mean().cumsum() - s).dropna(
            subset=["total_"+unit]
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
        name="Constant scenario",
        mode='lines',
        line={"width": 3, "dash": "dot", 'color':'red'},
        #fill='tozeroy'
        )
    )

    fig_sce.update_layout(template='ggplot2',
        title={
            "text": "<b>{} - {} Fleet Development in {}<b>".format(ship.upper(), clean_allias, unit_u),
            "font": {"size": 14},
            "x": 0.5,
        },
        # template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=0.93, xanchor="left", x=0),
        margin=dict(l=30, r=10, b=30, t=30, pad=4),
    )
    
    return fig_sce

# saved aupply
@app.callback(Output('hidden-supply', 'children'),
              Input('save-button', 'submit_n_clicks'),
               Input("graph-sce", "figure"),
             )
def save_csv(submit_n_clicks, fig_sce):
    if submit_n_clicks:
        
        l=[]
        for el in fig_sce['data']:
            if el['name'].find('scenario')>0:
                l.append(pd.DataFrame(index=el['x'], data=el['y'], columns=[el['name']]))
        save = pd.concat(l, join='inner', axis=1)
        save.to_csv(r"\\gvaps1\DATAROOT\data\SHARED\PALE\Dash\saved_supply\last_supply_scenario.csv")
        
        
        
##############################
#     Yearly Graph Bar chart #
#############################
@app.callback(
    Output("graph-yearly", "figure"),
    Input("clean-dropdown", "value"),
    Input("mbbl-button", "value"),
    Input("hidden-div", 'children')
)
def yearly_graph(clean, mbbl, json_data):
    
    ## fetch the right element of the tuple 
    if mbbl == 'mbbl':
        dummy = 0
    else:
        dummy = 1
        
    df = pd.read_json(json.loads(json_data[0])[clean]['fleet_dev'][dummy])
    df.to_csv('testdfdf.csv')
    df.index = pd.to_datetime(df.index)
    yearly_fleet = df.copy()
    
    yearly_fleet['year'] = yearly_fleet.index.year
    yearly_fleet = yearly_fleet.groupby('year').last()
    yearly_fleet.to_csv('test.csv')
    palette = cycle(px.colors.qualitative.D3)
    
    if clean == 'crude':
        if mbbl == 'mbbl':
            data=[
            go.Bar(name='VLCC', x=yearly_fleet.index, y=yearly_fleet.VLCC_mbbl, marker_color=next(palette)),
            go.Bar(name='Suezmax', x=yearly_fleet.index, y=yearly_fleet.suezmax_mbbl, marker_color=next(palette)),
            go.Bar(name='Aframax', x=yearly_fleet.index, y=yearly_fleet.aframax_mbbl, marker_color=next(palette)),
            go.Bar(name='Panamax', x=yearly_fleet.index, y=yearly_fleet.panamax_mbbl, marker_color=next(palette)),
            #go.Bar(name='Total', x=yearly_fleet.index, y=yearly_fleet.total_no, marker_color=next(palette))
        ]
        else:
            data=[
            go.Bar(name='VLCC', x=yearly_fleet.index, y=yearly_fleet.VLCC_no, marker_color=next(palette)),
            go.Bar(name='Suezmax', x=yearly_fleet.index, y=yearly_fleet.suezmax_no, marker_color=next(palette)),
            go.Bar(name='Aframax', x=yearly_fleet.index, y=yearly_fleet.aframax_no, marker_color=next(palette)),
            go.Bar(name='Panamax', x=yearly_fleet.index, y=yearly_fleet.panamax_no, marker_color=next(palette)),
            #go.Bar(name='Total', x=yearly_fleet.index, y=yearly_fleet.total_no, marker_color=next(palette))
        ]
        fig_yearly_graph = go.Figure(data=data)
        fig_yearly_graph = layout_plotly(fig_yearly_graph, 'Dirty Fleet Development', template='ggplot2')
            
    else:
        
        if mbbl == 'mbbl':
            data=[
            
            go.Bar(name='Suezmax', x=yearly_fleet.index, y=yearly_fleet.suezmax_mbbl, marker_color=next(palette)),
            go.Bar(name='Aframax', x=yearly_fleet.index, y=yearly_fleet.aframax_mbbl, marker_color=next(palette)),
            go.Bar(name='Panamax', x=yearly_fleet.index, y=yearly_fleet.panamax_mbbl, marker_color=next(palette)),
            go.Bar(name='MR', x=yearly_fleet.index, y=yearly_fleet.MR_mbbl, marker_color=next(palette)),
            go.Bar(name='Handy', x=yearly_fleet.index, y=yearly_fleet.handy_mbbl, marker_color=next(palette))
        ]
        else:
            data=[
            
            go.Bar(name='Suezmax', x=yearly_fleet.index, y=yearly_fleet.suezmax_no, marker_color=next(palette)),
            go.Bar(name='Aframax', x=yearly_fleet.index, y=yearly_fleet.aframax_no, marker_color=next(palette)),
            go.Bar(name='Panamax', x=yearly_fleet.index, y=yearly_fleet.panamax_no, marker_color=next(palette)),
            go.Bar(name='MR', x=yearly_fleet.index, y=yearly_fleet.MR_no, marker_color=next(palette)),
            go.Bar(name='Handy', x=yearly_fleet.index, y=yearly_fleet.handy_no, marker_color=next(palette))
        ]
        fig_yearly_graph = go.Figure(data=data)
        fig_yearly_graph = layout_plotly(fig_yearly_graph, 'Clean Fleet Development', template='ggplot2')
    
    return fig_yearly_graph





if __name__ == "__main__":
    app.run_server(debug=True, port=3055)