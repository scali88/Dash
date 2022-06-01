# -*- coding: utf-8 -*-
"""
Created on Tue Mar 16 09:42:22 2021

@author: pale
"""

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

from plotly.subplots import make_subplots
import plotly.express as px
from itertools import cycle

# colors
palette = cycle(px.colors.sequential.Rainbow)

import statsmodels.api as sm
from sklearn import metrics


sys.path.append(r"L:\SHARED\PALE\my_python_modules\my_functions")
from my_functions import My_date
from functions import (
    import_jbc_models,
    prices_and_curve,
    get_fwd_dates,
    ols_cu_price,
    get_scenaris,
    get_fwd_curve_from_db,
)
from vlcc_tool_layout import vlcc_layout


today = My_date()

app = dash.Dash(__name__, prevent_initial_callbacks=True)
app.layout = vlcc_layout


@app.callback(
    Output("intermediate-value-jbc", "children"), Input("scenario-dropdown", "value")
)
def jsonn(name):
    df_base = get_scenaris()[name].copy()
    df_base.Date = pd.to_datetime(df_base.Date)
    df_base = df_base.round(4)
    return df_base.to_json(orient="split")


#############################
#   update table           #
###########################
@app.callback(
    Output("tab", "children"),
    
    Input("scenario-dropdown", "value"),
)
def table(name):
    df = get_scenaris()[name].copy()

    df.Date = pd.to_datetime(df.Date)

    df = df.sort_values(by="Date", ascending=False)

    df.Date = df.Date.apply(lambda x: x.strftime("%Y-%m-%d"))
    df = df.round(4)

    return dash_table.DataTable(
        id="d_s-table",
        columns=[
            {"name": ["", "Date"], "id": "Date", "type": "datetime", "editable": False}
        ]
        + [
            {
                "name": ["Demand - MMBL", i],
                "id": i,
                "type": "numeric",
                "format": Format(precision=4, scheme=Scheme.decimal),
            }
            for i in df.columns[1:8]
        ]
        + [
            {
                "name": ["Supply", i],
                "id": i,
                "type": "numeric",
                "format": Format(precision=4, scheme=Scheme.decimal),
            }
            for i in df.columns[8:12]
        ]
        + [
            {
                "name": ["", i],
                "id": i,
                "type": "numeric",
                "format": Format(precision=4, scheme=Scheme.decimal),
            }
            for i in df.columns[12:]
        ],
        data=df.to_dict("records"),
        style_cell_conditional=[
            {"if": {"column_id": "Date"}, "textAlign": "left", "width": "5%"},
        ],
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "rgb(248, 248, 248)"},
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
        page_size=14,
        merge_duplicate_headers=True,
    )


# sum on the demand supply df
@app.callback(
    Output("d_s-table", "data"),
    Input("d_s-table", "data_timestamp"),
    State("d_s-table", "data"),
)
def update_columns(timestamp, rows):

    for row in rows:
        try:
            row["ton_day"] = round(
                float(row["AG-Asia"])
                + float(row["AG-Europe"])
                + float(row["AG-US"])
                + float(row["Latam-Asia"])
                + float(row["WAF-Asia"])
                + float(row["Small_flows"]),
                4,
            )

        except:
            row["ton_day"] = "NA"

        try:
            row["Total"] = round(
                float(row["VLCC fleet"])
                - float(row["Storage"])
                - float(row["Sanctions"]),
                4,
            )
        except:
            row["Total"] = "NA"
        try:
            row["cu"] = round(float(row["ton_day"]) / float(row["Total"]), 4)
        except:
            row["cu"] = "NA"
    return rows


# graph diference line
@app.callback(
    Output("graph-cu", "figure"),
    Input("d_s-table", "data"),
    Input("d_s-table", "columns"),
    Input("month-diff-dropdown", "value"),
    Input("rolling-dropdown", "value"),
    Input("intermediate-value-jbc", "children"),
    Input("generic-year", "on"),
    Input("index-name-dropdown", "value"),
    Input("index-type-dropdown", "value"),
)
def display_output_cu(
    rows, columns, value, rolling, json_old, switch, index_name, index_type
):

    df = pd.read_json(json_old, orient="split").copy()
    df.Date = pd.to_datetime(df.Date)
    df.set_index(df.Date, inplace=True)
    df = df.sort_index(ascending=True)
    df = df.merge(
        prices_and_curve(
            index_name=index_name,
            index_type=index_type,
            date="last",
            offset_2020=switch,
        ),
        left_index=True,
        right_index=True,
    )

    df_cu = pd.DataFrame(rows, columns=[c["name"][1] for c in columns])
    df_cu.Date = pd.to_datetime(df_cu.Date)
    df_cu.set_index("Date", inplace=True)
    df_cu = df_cu.sort_index(ascending=True)
    df_cu = df_cu.merge(
        prices_and_curve(
            index_name=index_name,
            index_type=index_type,
            date="last",
            offset_2020=switch,
        ),
        left_index=True,
        right_index=True,
    )

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=df_cu.index,
            y=df_cu.cu,
            name="Adjusted-Model",
            line={"width": 1, "color": "green"},
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df[: today.string].Date,
            y=df[: today.string].cu,
            name="Litasco Model CU - Actual",
            line={"width": 2, "color": "red"},
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df[today.string :].index,
            y=df[today.string :].cu,
            name="Litasco CU Model-FWD",
            line={"width": 2, "color": "red"},
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df[index_name],
            name=index_name,
            line={"width": 2, "color": "black"},
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title={"text": "VLCC CU Model", "font": {"size": 14}},
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=30, r=10, b=30, t=30, pad=4),
    )

    # fig.add_trace(
    #   go.Scatter(
    #      x=plot_new.index,
    #     y=plot_new.TD3_eiger_forecast,
    #     name="Adjusted Model",
    #    line={"width": 2, "color": "green"},
    # )
    # )

    return fig


#######################
# Scatter plot        #
######################
@app.callback(
    Output("graph-scatter", "figure"),
    Input("d_s-table", "data"),
    Input("d_s-table", "columns"),
    Input("month-diff-dropdown", "value"),
    Input("rolling-dropdown", "value"),
    Input("fwd-curves-dropdown", "value"),
    Input("generic-year", "on"),
    Input("index-name-dropdown", "value"),
    Input("index-type-dropdown", "value"),
)
def display_output_sct(
    rows, columns, value, rolling, dates, switch, index_name, index_type
):
    dates_db = get_fwd_dates().sort_values(by="date", ascending=False).date
    max_date = max(dates_db)

    df_cu = pd.DataFrame(rows, columns=[c["name"][1] for c in columns])
    df_cu.Date = pd.to_datetime(df_cu.Date)
    df_cu.set_index("Date", inplace=True)
    df_cu = df_cu.sort_index(ascending=True)
    # df_cu.to_csv('why.csv')

    df_cu = df_cu.merge(
        prices_and_curve(
            index_name=index_name,
            index_type=index_type,
            date="last",
            offset_2020=switch,
        ),
        left_index=True,
        right_index=True,
    )

    temp1 = (
        +df_cu[["cu", index_name]]
        - df_cu[["cu", index_name]].shift(value).rolling(rolling).mean()
    )
    if rolling != 1:
        temp1 = (
            +df_cu[["cu", index_name]]
            - df_cu[["cu", index_name]].shift(value).rolling(rolling).mean()
        )
    #temp1.to_csv('why.csv')
    # plot = dic_models["kpler_flow_reg"].predict(sm.add_constant(temp1.cu))
    plot, r2 = ols_cu_price(temp1.copy(), index_name=index_name)
    plot.name = "index_name" + "-forecast"
    plot = temp1[["cu"]].merge(plot, left_index=True, right_index=True)

    labels = pd.date_range(
        start=temp1[today.string :].index[1],
        periods=len(temp1[today.string :].index),
        freq="M",
    )
    labels = [
        x.strftime("%b-%Y") + " M" + str(i + 1) for i, x in enumerate(labels.date)
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=temp1[: today.string].cu,
            y=temp1[: today.string][index_name],
            name=index_name + " Price Difference",
            mode="markers",
            marker={"symbol": "circle", "size": 8, "color": "black"},
            text=temp1[: today.string].index.date,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=temp1[today.string :].cu,
            y=temp1[today.string :][index_name],
            name=index_name + " Price Difference - Last",
            mode="markers",
            marker={"symbol": "circle-open", "size": 10, "color": "black"},
            text=labels,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=plot.cu,
            y=plot["index_name" + "-forecast"],
            text=temp1.index.date,
            name="Litasco Price Difference Model",
            mode="lines",
            line={"color": "red"},
        )
    )

    fig.update_layout(
        title={
            "text": index_name + " Price Difference Forecast vs CU(%) difference",
            "font": {"size": 14},
        },
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=-0.02, xanchor="right", x=1),
        margin=dict(l=30, r=10, b=50, t=30, pad=4),
    )

    if dates != max_date:
        for dte in [x for x in dates if x != max_date]:
            df_cu_bis = df_cu.drop(columns=index_name)
            df_cu_bis = df_cu_bis.merge(
                prices_and_curve(
                    index_name=index_name,
                    index_type=index_type,
                    date=dte,
                    offset_2020=switch,
                ),
                left_index=True,
                right_index=True,
            )
            df_cu_bis = df_cu_bis.sort_index(ascending=True)
            if rolling != 1:
                temp2 = (
                    +df_cu_bis[["cu", index_name]]
                    - df_cu_bis[["cu", index_name]].shift(value).rolling(rolling).mean()
                )
            else:
                temp2 = +df_cu_bis[["cu", index_name]] - df_cu_bis[
                    ["cu", index_name]
                ].shift(value)
            labels = get_fwd_curve_from_db(index_name, date=dte).sort_values(
                by="settlement_date"
            )
            labels.settlement_date = pd.to_datetime(labels.settlement_date)
            # labels = [x.strftime('%b-%Y')+' M'+str(i+1) for i, x in enumerate(labels.date)]
            labels = [
                x.strftime("%b-%Y") + " M" + str(i + 1)
                for i, x in enumerate(labels.settlement_date)
            ]

            fig.add_trace(
                go.Scatter(
                    x=temp2[today.string :].cu,
                    y=temp2[today.string :][index_name],
                    name=dte,
                    mode="markers",
                    marker={"symbol": "circle", "size": 8, "color": next(palette)},
                    text=labels,
                )
            )

    return fig


# R2
@app.callback(
    Output("r2", "children"),
    Input("d_s-table", "data"),
    Input("d_s-table", "columns"),
    Input("month-diff-dropdown", "value"),
    Input("rolling-dropdown", "value"),
    Input("generic-year", "on"),
    Input("index-name-dropdown", "value"),
    Input("index-type-dropdown", "value"),
)
def r2(rows, columns, value, rolling, switch, index_name, index_type):

    df_cu = pd.DataFrame(rows, columns=[c["name"][1] for c in columns])
    df_cu.Date = pd.to_datetime(df_cu.Date)
    df_cu.set_index("Date", inplace=True)
    df_cu = df_cu.sort_index(ascending=True)
    # df_cu.to_csv('why.csv')
    df_cu = df_cu.merge(
        prices_and_curve(
            index_name=index_name,
            index_type=index_type,
            date="last",
            offset_2020=switch,
        ),
        left_index=True,
        right_index=True,
    )
    df_cu = df_cu.sort_index(ascending=True)    
    temp1 = +df_cu[["cu", index_name]] - df_cu[["cu", index_name]].shift(value)
    plot, r2 = ols_cu_price(temp1.copy(), index_name=index_name)
    if rolling != 1:
        temp1 = (
            +df_cu[["cu", index_name]]
            - df_cu[["cu", index_name]].shift(value).rolling(rolling).mean()
        )
        # temp1.to_csv('test.csv')
        rr = temp1.copy()
        plot, r2 = ols_cu_price(rr, index_name=index_name)

    # plot = dic_models["kpler_flow_reg"].predict(sm.add_constant(temp1.cu))

    return "R2: " + str(round(r2, 3))


# saved scenario
@app.callback(
    Output("hidden", "children"),
    Input("save-button", "submit_n_clicks"),
    Input("d_s-table", "data"),
    Input("d_s-table", "columns"),
)
def save_csv_price(submit_n_clicks, rows, columns):
    if submit_n_clicks:

        df_cu = pd.DataFrame(rows, columns=[c["name"][1] for c in columns])
        df_cu.to_csv(
            r"\\gvaps1\DATAROOT\data\SHARED\PALE\Dash\saved_scenario\last_scenario_csv.csv"
        )


if __name__ == "__main__":
    app.run_server(debug=True, port=3045)
