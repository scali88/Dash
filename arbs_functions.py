# -*- coding: utf-8 -*-
"""
Created on Thu Apr 22 11:45:45 2021

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


class ArbsMapping:
    """
    Class to Map and send Arbs based on ANBD pricer
    """

    def table_map(self, path_df, path_loc):

        df_values = self._load(path_df, path_loc)
        table = self._table(df_values)
        map_ = self._map(df_values)
        return table, map_

    @classmethod
    def _load(cls, path_df, path_loc):
        """
        #load the df
        """
        df_values = pd.read_csv(path_df, usecols=[0, 1, 2, 3, 4, 5, 6, 7])
        df_loc = pd.read_csv(path_loc)

        df_values["from_"] = df_values.Arbs.apply(lambda x: x.split(">")[0])
        df_values["to_"] = df_values.Arbs.apply(lambda x: x.split(">")[1])
        df_values["name"] = (
            df_values.Arbs + "-" + df_values.Product + "|" + df_values.Type
        )
        df_values["lat"] = df_values.apply(
            lambda x: cls._coord(
                x["from_"], x["to_"], x["Type"], df_loc=df_loc, type_=True
            ),
            axis=1,
        )
        df_values["lon"] = df_values.apply(
            lambda x: cls._coord(
                x["from_"],
                x["to_"],
                x["Type"],
                df_loc=df_loc,
                type_=True,
                kind="longitude",
            ),
            axis=1,
        )

        df_values["lat"] = df_values["lat"].fillna(
            df_values.apply(
                lambda x: cls._coord(
                    x["from_"], x["to_"], x["Type"], df_loc=df_loc, type_=False
                ),
                axis=1,
            )
        )

        df_values["lon"] = df_values["lon"].fillna(
            df_values.apply(
                lambda x: cls._coord(
                    x["from_"],
                    x["to_"],
                    x["Type"],
                    df_loc=df_loc,
                    type_=False,
                    kind="longitude",
                ),
                axis=1,
            )
        )
        df_values["name"]
        return df_values.round(3)

    @classmethod
    def _coord(cls, from_, to_, vessel, df_loc, type_=True, kind="latitude"):

        if type_ == True:
            try:
                # print(from_, to_, vessel)
                geo = (
                    df_loc.dropna(subset=["Type"])
                    .loc[
                        (df_loc.dropna(subset=["Type"]).alias == from_)
                        & (df_loc.dropna(subset=["Type"]).Type == vessel),
                        kind,
                    ]
                    .values[0],
                    df_loc.loc[df_loc.alias == to_, kind].values[0],
                )

            except:
                geo = np.nan

        else:
            try:
                # print(from_, to_, vessel, df_loc)
                geo = (
                    df_loc.loc[df_loc.alias == from_, kind].values[0],
                    df_loc.loc[df_loc.alias == to_, kind].values[0],
                )
            except:
                geo = np.nan
        return geo

    @staticmethod
    def color(c):
        if c > 0 and c < 1:
            col = "orange"
            show = True
        elif c >= 1:
            col = "red"
            show = False
        elif c <= 0:
            col = "green"
            show = True
        else:
            col = "red"
            show = False
        return col, show

    @classmethod
    def _table(cls, df_values):
        """retrun the table with the values"""
        df_table = df_values.sort_values(by="Color", ascending=True)[
            ["Arbs", "Product", "M0", "M1", "M2", "Units", "Type"]
        ]
        colors = (
            df_values.sort_values(by="Color", ascending=True)
            .dropna()
            .Color.apply(lambda x: cls.color(x)[0])
            .tolist()
        )

        n = [i for i, x in enumerate(colors) if x != "green"][0]
        table_values = [df_table[k].tolist() for k in df_table.columns]
        if n > 0:
            if n > 0:
                for el in table_values:
                    el[:n] = ["<b>{}</b>".format(x) for x in el[:n]]
            else:
                pass

        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=["{}".format(x) for x in df_table],
                        # fill_color='paleturquoise',
                        line=dict(color="rgb(0, 0, 0)"),
                        align="left",
                        font=dict(color=["rgb(255, 255, 255)"], size=13),
                        fill=dict(color="rgb(102, 0, 0)"),
                    ),
                    cells=dict(
                        values=table_values,
                        # fill_color='lavender',
                        line=dict(color="#506784"),
                        font=dict(color=[colors], size=12),
                        align="left",
                        height=8,
                        fill=dict(color=["#F6F5F5"]),
                    ),
                )
            ]
        )
        fig.update_layout(margin=dict(l=0, r=0, b=0, t=0, pad=0))
        return fig

    @classmethod
    def _map(cls, df_values):

        fig = go.Figure()

        for t in (
            df_values.loc[df_values.groupby("Arbs")["Color"].idxmin()]
            .dropna()
            .itertuples(index=False)
        ):

            fig.add_trace(
                go.Scattergeo(
                    lat=t[-2],
                    lon=t[-1],
                    mode="lines",
                    hoverinfo="text",
                    text=t[0],
                    name=t[10] + "|" + str(min(t[1], t[2], t[3])) + t[4],
                    line=dict(width=4, color=cls.color(t[5])[0]),
                    visible=cls.color(t[5])[1],
                )
            )

        fig.update_layout(
            title_text="Middle Distillate Arbs",
            showlegend=True,
            geo=dict(
                # fitbounds="locations",
                scope="world",
                projection_type="equirectangular",
                showland=True,
                showlakes=False,
                showcountries=True,
                landcolor="Wheat",
                bgcolor="Aliceblue",
            ),
            margin=dict(l=0, r=0, b=0, t=0, pad=0),
            # paper_bgcolor='SkyBlue',
            # plot_bgcolor='SkyBlue',
            # plot_bgcolor='grey',
            legend=dict(
                orientation="v",
                yanchor="auto",
                y=1,
                xanchor="left",
                x=0,
                font={"size": 9},
                bgcolor="rgba(235,233,233,0.9)",
                font_color="black",
            ),
        )
        # fig.update_geos(fitbounds="locations")
        return fig
