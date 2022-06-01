# -*- coding: utf-8 -*-
"""
Created on Mon Mar 22 08:51:59 2021

@author: pale
"""


import pandas as pd
import numpy as np

import re
import datetime as dt
import glob
import sys
import plotly.graph_objects as go
sys.path.append(r"L:\SHARED\PALE\my_python_modules\my_functions")
from my_functions import My_date

from random import seed, randint

cbm_to_bbl = 6.2898
dwt_to_cbm_crude = 1.085
dwt_to_cbm_prod = 1.12


# FLEET DEV
def fleet_dev_per_ship(clean=False):
    """retrun the crude fleet in mbbl and number per ship size"""
    files = glob.glob(
        r"\\gvaps1\DATAROOT\data\SHARED\PALE\Shipping\Clarckson_data\crude_fleet_development\*.xlsx"
    )
    crude_fleet = pd.read_excel(files[0], skiprows=4, usecols="A:I")[1:-14]

    crude_fleet.columns = [
        "date",
        "VLCC_no",
        "VLCC_dwt",
        "suezmax_no",
        "suezmax_dwt",
        "aframax_no",
        "aframax_dwt",
        "panamax_no",
        "panamax_dwt",
    ]

    crude_fleet.date = pd.to_datetime(crude_fleet.date)
    crude_fleet["total_dwt"] = crude_fleet[
        [x for x in crude_fleet.columns if x.find("dwt") > 0]
    ].sum(axis=1)
    crude_fleet["total_no"] = crude_fleet[
        [x for x in crude_fleet.columns if x.find("no") > 0]
    ].sum(axis=1)

    files = glob.glob(
        r"\\gvaps1\DATAROOT\data\SHARED\PALE\Shipping\Clarckson_data\clean_fleet_development\*.xlsx"
    )
    clean_fleet_1 = pd.read_excel(files[0], skiprows=4)[1:-18]

    clean_fleet_1.columns = [
        "date",
        "suezmax_no",
        "suezmax_dwt",
        "aframax_no",
        "aframax_dwt",
        "panamax_no",
        "panamax_dwt",
        "handy_no",
        "handy_dwt",
        "total_no",
        "total_dwt",
        "MR_no",
        "MR_dwt",
    ]
    clean_fleet_1["total_no"] = clean_fleet_1["total_no"] - clean_fleet_1["handy_no"]
    clean_fleet_1["total_dwt"] = clean_fleet_1["total_dwt"] - clean_fleet_1["handy_dwt"]
    clean_fleet_1 = clean_fleet_1[
        [
            "date",
            "suezmax_no",
            "suezmax_dwt",
            "aframax_no",
            "aframax_dwt",
            "panamax_no",
            "panamax_dwt",
            "total_no",
            "total_dwt",
        ]
    ]

    for el in (crude_fleet, clean_fleet_1):
        el.date = pd.to_datetime(el.date)
        el.set_index(el.date, inplace=True)
        el.drop(columns="date", inplace=True)

    crude_fleet = crude_fleet[clean_fleet_1.index[0] :]
    clean_fleet_1[["VLCC_no", "VLCC_dwt"]] = 0
    crude_fleet = crude_fleet - clean_fleet_1

    crude_fleet_mbbl = (
        crude_fleet[[x for x in crude_fleet.columns if x.find("dwt") > 0]]
        * dwt_to_cbm_crude
    )
    crude_fleet_mbbl = crude_fleet_mbbl * cbm_to_bbl
    crude_fleet_mbbl.columns = [
        x.replace("dwt", "mbbl") for x in crude_fleet_mbbl.columns
    ]
    crude_fleet_mbbl = crude_fleet_mbbl.astype(float)
    crude_fleet_mbbl["state"] = "fleet_dev"
    crude_fleet_mbbl = crude_fleet_mbbl.round(4)
    crude_fleet_no = crude_fleet[[x for x in crude_fleet.columns if x.find("no") > 0]]
    crude_fleet_no["state"] = "fleet_dev"
    if clean == True:
        files = glob.glob(
            r"\\gvaps1\DATAROOT\data\SHARED\PALE\Shipping\Clarckson_data\clean_fleet_development\*.xlsx"
        )
        clean_fleet = pd.read_excel(files[0], skiprows=4)[1:-18]
        clean_fleet.columns = [
            "date",
            "suezmax_no",
            "suezmax_dwt",
            "aframax_no",
            "aframax_dwt",
            "panamax_no",
            "panamax_dwt",
            "handy_no",
            "handy_dwt",
            "total_no",
            "total_dwt",
            "MR_no",
            "MR_dwt",
        ]
        clean_fleet["handy_no"] = clean_fleet["handy_no"] - clean_fleet.MR_no
        clean_fleet["handy_dwt"] = clean_fleet["handy_dwt"] - clean_fleet.MR_dwt
        # clean_deliveries.date = clean_deliveries.date.apply(lambda x: x.date())
        clean_fleet.date = pd.to_datetime(clean_fleet.date)
        # clean_fleet['total_dwt'] = clean_fleet.total_dwt

        clean_fleet_mbbl = (
            clean_fleet.set_index("date")[
                [x for x in clean_fleet.columns if x.find("dwt") > 0]
            ]
            * dwt_to_cbm_prod
        )
        clean_fleet_mbbl = clean_fleet_mbbl * cbm_to_bbl
        clean_fleet_mbbl.columns = [
            x.replace("dwt", "mbbl") for x in clean_fleet_mbbl.columns
        ]
        clean_fleet_mbbl = clean_fleet_mbbl.astype(float)
        clean_fleet_mbbl["state"] = "fleet_dev"
        clean_fleet_no = clean_fleet.set_index("date")[
            [x for x in clean_fleet.columns if x.find("no") > 0]
        ]
        clean_fleet_no = clean_fleet_no.astype(int)
        clean_fleet_no["state"] = "fleet_dev"
        return clean_fleet_mbbl, clean_fleet_no
    return crude_fleet_mbbl, crude_fleet_no


# d DELIVERIES
def deliveries(clean=False):
    files = glob.glob(
        r"\\gvaps1\DATAROOT\data\SHARED\PALE\Shipping\Clarckson_data\crude_deliveries\*.xlsx"
    )

    crude_deliveries = pd.read_excel(files[0], skiprows=4)[1:-14]

    crude_deliveries.columns = [
        "date",
        "VLCC_no",
        "VLCC_dwt",
        "suezmax_no",
        "suezmax_dwt",
        "aframax_no",
        "aframax_dwt",
        "panamax_no",
        "panamax_dwt",
    ]

    crude_deliveries.date = pd.to_datetime(crude_deliveries.date)
    crude_deliveries["total_dwt"] = crude_deliveries[
        [x for x in crude_deliveries.columns if x.find("dwt") > 0]
    ].sum(axis=1)
    crude_deliveries["total_no"] = crude_deliveries[
        [x for x in crude_deliveries.columns if x.find("no") > 0]
    ].sum(axis=1)

    files = glob.glob(
        r"\\gvaps1\DATAROOT\data\SHARED\PALE\Shipping\Clarckson_data\clean_deliveries\*.xlsx"
    )
    clean_deliveries_1 = pd.read_excel(files[0], skiprows=4)[1:-18]

    clean_deliveries_1.columns = [
        "date",
        "suezmax_no",
        "suezmax_dwt",
        "aframax_no",
        "aframax_dwt",
        "panamax_no",
        "panamax_dwt",
        "handy_no",
        "handy_dwt",
        "total_no",
        "total_dwt",
        "MR_no",
        "MR_dwt",
    ]
    clean_deliveries_1["total_no"] = (
        clean_deliveries_1["total_no"] - clean_deliveries_1["handy_no"]
    )
    clean_deliveries_1["total_dwt"] = (
        clean_deliveries_1["total_dwt"] - clean_deliveries_1["handy_dwt"]
    )

    clean_deliveries_1 = clean_deliveries_1[
        [
            "date",
            "suezmax_no",
            "suezmax_dwt",
            "aframax_no",
            "aframax_dwt",
            "panamax_no",
            "panamax_dwt",
            "total_no",
            "total_dwt",
        ]
    ]

    # clean_deliveries_1['total_dwt'] = clean_deliveries_1.total_dwt*1000000

    for el in (crude_deliveries, clean_deliveries_1):
        el.date = pd.to_datetime(el.date)
        el.set_index(el.date, inplace=True)
        el.drop(columns="date", inplace=True)

    crude_deliveries = crude_deliveries[clean_deliveries_1.index[0] :]
    clean_deliveries_1[["VLCC_no", "VLCC_dwt"]] = 0
    crude_deliveries = crude_deliveries - clean_deliveries_1

    crude_deliveries_mbbl = (
        crude_deliveries[[x for x in crude_deliveries.columns if x.find("dwt") > 0]]
        / 1000000
    )
    crude_deliveries_mbbl = (
        crude_deliveries_mbbl[
            [x for x in crude_deliveries_mbbl.columns if x.find("dwt") > 0]
        ]
        * dwt_to_cbm_crude
    )
    crude_deliveries_mbbl = crude_deliveries_mbbl * cbm_to_bbl
    crude_deliveries_mbbl.columns = [
        x.replace("dwt", "mbbl") for x in crude_deliveries_mbbl.columns
    ]
    crude_deliveries_mbbl = crude_deliveries_mbbl.astype(float)
    crude_deliveries_mbbl["state"] = "deliveries"
    crude_deliveries_no = crude_deliveries[
        [x for x in crude_deliveries.columns if x.find("no") > 0]
    ]
    crude_deliveries_no["state"] = "deliveries"
    if clean == True:
        files = glob.glob(
            r"\\gvaps1\DATAROOT\data\SHARED\PALE\Shipping\Clarckson_data\clean_deliveries\*.xlsx"
        )
        clean_deliveries = pd.read_excel(files[0], skiprows=4)[1:-18]
        clean_deliveries.columns = [
            "date",
            "suezmax_no",
            "suezmax_dwt",
            "aframax_no",
            "aframax_dwt",
            "panamax_no",
            "panamax_dwt",
            "handy_no",
            "handy_dwt",
            "total_no",
            "total_dwt",
            "MR_no",
            "MR_dwt",
        ]
        clean_deliveries["handy_no"] = (
            clean_deliveries["handy_no"] - clean_deliveries.MR_no
        )
        clean_deliveries["handy_dwt"] = (
            clean_deliveries["handy_dwt"] - clean_deliveries.MR_dwt
        )
        # clean_deliveries.date = clean_deliveries.date.apply(lambda x: x.date())
        clean_deliveries.date = pd.to_datetime(clean_deliveries.date)
        clean_deliveries["total_dwt"] = clean_deliveries.total_dwt * 1000000

        clean_deliveries_mbbl = (
            clean_deliveries.set_index("date")[
                [x for x in clean_deliveries.columns if x.find("dwt") > 0]
            ]
            * dwt_to_cbm_prod
            / 1000000
        )
        clean_deliveries_mbbl = clean_deliveries_mbbl * cbm_to_bbl
        clean_deliveries_mbbl.columns = [
            x.replace("dwt", "mbbl") for x in clean_deliveries_mbbl.columns
        ]
        clean_deliveries_mbbl["state"] = "deliveries"
        clean_deliveries_no = clean_deliveries.set_index("date")[
            [x for x in clean_deliveries.columns if x.find("no") > 0]
        ]
        clean_deliveries_no["state"] = "deliveries"
        return clean_deliveries_mbbl, clean_deliveries_no

    return crude_deliveries_mbbl, crude_deliveries_no


# ORDERBOOK
def orderbook(clean=False):
    seed(2)
    if clean == True:
        files = glob.glob(
            r"L:\SHARED\PALE\Shipping\Clarckson_data\clean_orderbook\*.xlsx"
        )
        dates = []
        l = []
        for f in files:
            match = re.search(r"(\d+-\d+-\d+)", f)
            dates.append(match.group(1))
            temp = pd.read_excel(f, skiprows=3).dropna(subset=["Type"])
            temp = temp[(temp["Type"].isin(["Products", "Chem & Oil"]))]
            temp["type"] = (
                re.search(r"^[^_]*", f[f.find("orderbook") + 10 :]).group(0).upper()
            )
            temp["snapshot_date"] = match.group(1)
            temp["built_date"] = temp.Built.apply(
                lambda x: x[:4] + "-0" + str(randint(1, 9)) if len(x) < 6 else x
            )
            temp.built_date = pd.to_datetime(temp.built_date)
            l.append(temp)
        orderbook = pd.concat(l, axis=0).reset_index(drop=True)
        orderbook["CBM_adjusted"] = orderbook["Size"] * dwt_to_cbm_prod / 1000000
        orderbook["mbbl"] = orderbook["CBM_adjusted"] * cbm_to_bbl
        orderbook["state"] = "orderbook"
        orderbook["product"] = "clean"

        no_od = (
            orderbook.groupby(["built_date", "type"], as_index=False)
            .count()
            .pivot(columns="type", values=["Status"], index=["built_date"])
        )

        mbbl_od = (
            orderbook.groupby(["built_date", "type"], as_index=False)
            .sum()[["built_date", "type", "mbbl"]]
            .pivot(columns="type", values=["mbbl"], index=["built_date"])
        )

        mbbl_od.rename(
            columns={
                "HANDY": "handy_mbbl",
                "LR1": "panamax_mbbl",
                "LR2": "aframax_mbbl",
                "MR": "MR_mbbl",
            },
            inplace=True,
        )

        no_od.rename(
            columns={
                "HANDY": "handy_no",
                "LR1": "panamax_no",
                "LR2": "aframax_no",
                "MR": "MR_no",
            },
            inplace=True,
        )

        no_od.columns = [x[1] for x in no_od.columns.ravel()]
        no_od["total_no"] = no_od.sum(axis=1)
        mbbl_od.columns = [x[1] for x in mbbl_od.columns.ravel()]
        mbbl_od["total_mbbl"] = mbbl_od.sum(axis=1)
        no_od["state"] = "orderbook"
        mbbl_od["state"] = "orderbook"
        return mbbl_od, no_od
    else:
        files = glob.glob(
            r"L:\SHARED\PALE\Shipping\Clarckson_data\crude_orderbook\*.xlsx"
        )
        dates = []
        l = []
        for f in files:
            match = re.search(r"(\d+-\d+-\d+)", f)
            dates.append(match.group(1))
            temp = pd.read_excel(f, skiprows=3).dropna(subset=["Type"])
            temp = temp[(temp["Type"] == "Tanker")]
            temp["type"] = (
                re.search(r"^[^_]*", f[f.find("orderbook") + 10 :]).group(0).upper()
            )
            temp["snapshot_date"] = match.group(1)
            temp["built_date"] = temp.Built.apply(
                lambda x: x[:4] + "-06" if len(x) < 6 else x
            )
            temp.built_date = pd.to_datetime(temp.built_date)
            l.append(temp)
        crude_orderbook = pd.concat(l, axis=0).reset_index(drop=True)
        crude_orderbook["CBM_adjusted"] = (
            crude_orderbook["Size"] * dwt_to_cbm_crude / 1000000
        )
        crude_orderbook["mbbl"] = crude_orderbook["CBM_adjusted"] * cbm_to_bbl
        crude_orderbook["state"] = "crude_orderbook"
        # crude_orderbook['product'] = 'crude'

        crude_no_od = (
            crude_orderbook.groupby(["built_date", "type"], as_index=False)
            .count()
            .pivot(columns="type", values=["Status"], index=["built_date"])
        )

        crude_mbbl_od = (
            crude_orderbook.groupby(["built_date", "type"], as_index=False)
            .sum()[["built_date", "type", "mbbl"]]
            .pivot(columns="type", values=["mbbl"], index=["built_date"])
        )

        crude_mbbl_od.rename(
            columns={
                "HANDY": "handy_mbbl",
                "PANAMAX": "panamax_mbbl",
                "AFRAMAX": "aframax_mbbl",
                "MR": "MR_mbbl",
                "SUEZMAX": "suezmax_mbbl",
                "VLCC": "VLCC_mbbl",
            },
            inplace=True,
        )

        crude_no_od.rename(
            columns={
                "HANDY": "handy_no",
                "PANAMAX": "panamax_no",
                "AFRAMAX": "aframax_no",
                "MR": "MR_no",
                "SUEZMAX": "suezmax_no",
                "VLCC": "VLCC_no",
            },
            inplace=True,
        )

        crude_no_od.columns = [x[1] for x in crude_no_od.columns.ravel()]
        crude_no_od["total_no"] = crude_no_od.sum(axis=1)
        crude_no_od["state"] = "orderbook"

        crude_mbbl_od.columns = [x[1] for x in crude_mbbl_od.columns.ravel()]
        crude_mbbl_od["total_mbbl"] = crude_mbbl_od.sum(axis=1)
        crude_mbbl_od["state"] = "orderbook"
        return crude_mbbl_od, crude_no_od


## Addtion


def addition(clean=False):
    if clean == True:
        clean_mbbl_od, clean_no_od = orderbook(clean=True)
        clean_deliveries_mbbl, clean_deliveries_no = deliveries(clean=True)
        addition_mbbl = pd.concat(
            [
                clean_deliveries_mbbl,
                clean_mbbl_od[clean_deliveries_mbbl.index[-1] + dt.timedelta(days=5) :],
            ],
            axis=0,
        )

        addition_no = pd.concat(
            [
                clean_deliveries_no,
                clean_no_od[clean_deliveries_no.index[-1] + dt.timedelta(days=5) :],
            ],
            axis=0,
        )

        return addition_mbbl, addition_no
    else:
        crude_deliveries_mbbl, crude_deliveries_no = deliveries()
        crude_mbbl_od, crude_no_od = orderbook()

        addition_mbbl = pd.concat(
            [
                crude_deliveries_mbbl,
                crude_mbbl_od[crude_deliveries_mbbl.index[-1] + dt.timedelta(days=5) :],
            ],
            axis=0,
        )

        addition_no = pd.concat(
            [
                crude_deliveries_no,
                crude_no_od[crude_deliveries_no.index[-1] + dt.timedelta(days=5) :],
            ],
            axis=0,
        )

    return addition_mbbl, addition_no


# crude demolition
def demolition(clean=False):

    if clean == True:
        files = glob.glob(
            r"\\gvaps1\DATAROOT\data\SHARED\PALE\Shipping\Clarckson_data\clean_demolition\*.xlsx"
        )
        clean_demolition = pd.read_excel(files[0], skiprows=4)[1:-18]

        clean_demolition.columns = [
            "date",
            "suezmax_no",
            "suezmax_dwt",
            "aframax_no",
            "aframax_dwt",
            "panamax_no",
            "panamax_dwt",
            "handy_no",
            "handy_dwt",
            "total_no",
            "total_dwt",
            "MR_no",
            "MR_dwt",
        ]
        clean_demolition["handy_no"] = (
            clean_demolition["handy_no"] - clean_demolition.MR_no
        )
        clean_demolition["handy_dwt"] = (
            clean_demolition["handy_dwt"] - clean_demolition.MR_dwt
        )
        # clean_demolition.date = clean_demolition.date.apply(lambda x: x.date())
        clean_demolition.date = pd.to_datetime(clean_demolition.date)
        clean_demolition["total_dwt"] = clean_demolition.total_dwt * 1000000

        clean_demolition_mbbl = (
            clean_demolition.set_index("date")[
                [x for x in clean_demolition.columns if x.find("dwt") > 0]
            ]
            * dwt_to_cbm_prod
            / 1000000
        )
        clean_demolition_mbbl = clean_demolition_mbbl * cbm_to_bbl
        clean_demolition_mbbl.columns = [
            x.replace("dwt", "mbbl") for x in clean_demolition_mbbl.columns
        ]
        clean_demolition_mbbl["state"] = "demolition"

        # clean_demolition_mbbl.date = pd.to_datetime(clean_demolition_mbbl.Date)
        clean_demolition_mbbl = clean_demolition_mbbl.fillna(0)
        clean_demolition_no = clean_demolition.set_index("date")[
            [x for x in clean_demolition.columns if x.find("no") > 0]
        ]
        clean_demolition_no["state"] = "demolition"

        return clean_demolition_mbbl, clean_demolition_no

    else:
        files = glob.glob(
            r"\\gvaps1\DATAROOT\data\SHARED\PALE\Shipping\Clarckson_data\crude_demolition\*.xlsx"
        )
        crude_demolition = pd.read_excel(files[0], skiprows=4, usecols="A:I")[1:-16]

        crude_demolition.columns = [
            "date",
            "VLCC_no",
            "VLCC_dwt",
            "suezmax_no",
            "suezmax_dwt",
            "aframax_no",
            "aframax_dwt",
            "panamax_no",
            "panamax_dwt",
        ]

        crude_demolition.date = pd.to_datetime(crude_demolition.date)
        crude_demolition["total_dwt"] = crude_demolition[
            [x for x in crude_demolition.columns if x.find("dwt") > 0]
        ].sum(axis=1)
        crude_demolition["total_no"] = crude_demolition[
            [x for x in crude_demolition.columns if x.find("no") > 0]
        ].sum(axis=1)

        files = glob.glob(
            r"\\gvaps1\DATAROOT\data\SHARED\PALE\Shipping\Clarckson_data\clean_demolition\*.xlsx"
        )
        clean_demolition_1 = pd.read_excel(files[0], skiprows=4)[1:-18]

        clean_demolition_1.columns = [
            "date",
            "suezmax_no",
            "suezmax_dwt",
            "aframax_no",
            "aframax_dwt",
            "panamax_no",
            "panamax_dwt",
            "handy_no",
            "handy_dwt",
            "total_no",
            "total_dwt",
            "MR_no",
            "MR_dwt",
        ]

        clean_demolition_1.date = pd.to_datetime(clean_demolition_1.date)
        clean_demolition_1["total_dwt"] = clean_demolition_1.total_dwt * 1000000

        clean_demolition_1["total_no"] = (
            clean_demolition_1["total_no"] - clean_demolition_1["handy_no"]
        )
        clean_demolition_1["total_dwt"] = (
            clean_demolition_1["total_dwt"] - clean_demolition_1["handy_dwt"]
        )

        clean_demolition_1 = clean_demolition_1[
            [
                "date",
                "suezmax_no",
                "suezmax_dwt",
                "aframax_no",
                "aframax_dwt",
                "panamax_no",
                "panamax_dwt",
                "total_no",
                "total_dwt",
            ]
        ]

        for el in (crude_demolition, clean_demolition_1):
            el.date = pd.to_datetime(el.date)
            el.set_index(el.date, inplace=True)
            el.drop(columns="date", inplace=True)

        crude_demolition = crude_demolition[clean_demolition_1.index[0] :]
        clean_demolition_1[["VLCC_no", "VLCC_dwt"]] = 0
        crude_demolition = crude_demolition - clean_demolition_1

        crude_demolition_mbbl = (
            crude_demolition[[x for x in crude_demolition.columns if x.find("dwt") > 0]]
            / 1000000
        )
        crude_demolition_mbbl = (
            crude_demolition_mbbl[
                [x for x in crude_demolition_mbbl.columns if x.find("dwt") > 0]
            ]
            * dwt_to_cbm_crude
        )
        crude_demolition_mbbl = crude_demolition_mbbl * cbm_to_bbl
        crude_demolition_mbbl.columns = [
            x.replace("dwt", "mbbl") for x in crude_demolition_mbbl.columns
        ]
        crude_demolition_mbbl = crude_demolition_mbbl.astype(float)
        crude_demolition_mbbl["state"] = "demolition"
        crude_demolition_mbbl = crude_demolition_mbbl.fillna(0)
        crude_demolition_no = crude_demolition[
            [x for x in crude_demolition.columns if x.find("no") > 0]
        ]

        return crude_demolition_mbbl, crude_demolition_no


# Individual tankers
def individual_tankers(clean=False):
    if clean == True:
        files = glob.glob(
            r"\\gvaps1\DATAROOT\data\SHARED\PALE\Shipping\Clarckson_data\clean_individual_tankers\*.xlsx"
        )
        dates = []
        l = []
        for f in files:
            match = re.search(r"(\d+-\d+-\d+)", f)
            dates.append(match.group(1))
            temp = pd.read_excel(f, skiprows=3).dropna(subset=["Name"])
            temp["snapshot_date"] = match.group(1)
            temp = temp[
                (temp["Type"].isin(["Products", "Chem & Oil"]))
                & (temp.Status.isin(["In Service", "Storage"]))
            ]
            temp["build_date"] = temp.apply(
                lambda x: dt.datetime(int(x["Built"]), int(x["Month"]), 1), axis=1
            )
            temp["type"] = (
                re.search(r"^[^_]*", f[f.find("tankers") + 8 :]).group(0).upper()
            )
            l.append(temp)
        clean_tankers = pd.concat(l, axis=0).reset_index(drop=True)
        clean_tankers["mbbl"] = (
            clean_tankers["Dwt"] * dwt_to_cbm_prod * cbm_to_bbl / 1000000
        )

        clean_tankers_mbbl = (
            clean_tankers.groupby(["build_date", "type"], as_index=False)
            .sum()[["build_date", "type", "mbbl"]]
            .pivot(columns="type", values=["mbbl"], index=["build_date"])
        )

        clean_tankers_no = (
            clean_tankers.groupby(["build_date", "type"], as_index=False)
            .count()
            .pivot(columns="type", values=["Size"], index=["build_date"])
        )

        clean_tankers_mbbl.rename(
            columns={
                "HANDY": "handy_mbbl",
                "LR1": "panamax_mbbl",
                "LR2": "aframax_mbbl",
                "MR": "MR_mbbl",
                "SUEZMAX": "suezmax_mbbl",
            },
            inplace=True,
        )

        clean_tankers_no.rename(
            columns={
                "HANDY": "handy_no",
                "LR1": "panamax_no",
                "LR2": "aframax_no",
                "MR": "MR_no",
                "SUEZMAX": "suezmax_no",
            },
            inplace=True,
        )

        clean_tankers_mbbl.columns = [x[1] for x in clean_tankers_mbbl.columns.ravel()]
        clean_tankers_mbbl["total_mbbl"] = clean_tankers_mbbl.sum(axis=1)
        clean_tankers_no.columns = [x[1] for x in clean_tankers_no.columns.ravel()]
        clean_tankers_no["total_no"] = clean_tankers_no.sum(axis=1)
        return clean_tankers_mbbl, clean_tankers_no

    else:
        files = glob.glob(
            r"L:\SHARED\PALE\Shipping\Clarckson_data\crude_individual_tankers\*.xlsx"
        )
        dates = []
        l = []
        for f in files:
            match = re.search(r"(\d+-\d+-\d+)", f)
            dates.append(match.group(1))
            temp = pd.read_excel(f, skiprows=3).dropna(subset=["Name"])
            temp["snapshot_date"] = match.group(1)
            # temp = temp[(temp['Type']=='Tanker') & (temp.Status.isin(['In Service', 'Storage']))]
            temp = temp[(temp["Type"] == "Tanker") & (temp.Status.isin(["In Service"]))]
            temp["build_date"] = temp.apply(
                lambda x: dt.datetime(int(x["Built"]), int(x["Month"]), 1), axis=1
            )
            temp["type"] = (
                re.search(r"^[^_]*", f[f.find("tankers") + 8 :]).group(0).upper()
            )
            l.append(temp)
        crude_tankers = pd.concat(l, axis=0).reset_index(drop=True)
        crude_tankers["mbbl"] = (
            crude_tankers["Dwt"] * dwt_to_cbm_crude * cbm_to_bbl / 1000000
        )

        crude_tankers_mbbl = (
            crude_tankers.groupby(["build_date", "type"], as_index=False)
            .sum()[["build_date", "type", "mbbl"]]
            .pivot(columns="type", values=["mbbl"], index=["build_date"])
        )

        crude_tankers_no = (
            crude_tankers.groupby(["build_date", "type"], as_index=False)
            .count()
            .pivot(columns="type", values=["Size"], index=["build_date"])
        )

        crude_tankers_mbbl.rename(
            columns={
                "VLCC": "VLCC_mbbl",
                "PANAMAX": "panamax_mbbl",
                "AFRAMAX": "aframax_mbbl",
                "HANDY": "handy_mbbl",
                "SUEZMAX": "suezmax_mbbl",
            },
            inplace=True,
        )

        crude_tankers_no.rename(
            columns={
                "VLCC": "VLCC_no",
                "PANAMAX": "panamax_no",
                "AFRAMAX": "aframax_no",
                "HANDY": "handy_no",
                "SUEZMAX": "suezmax_no",
            },
            inplace=True,
        )

        crude_tankers_mbbl.columns = [x[1] for x in crude_tankers_mbbl.columns.ravel()]
        crude_tankers_mbbl["total_mbbl"] = crude_tankers_mbbl.sum(axis=1)

        crude_tankers_no.columns = [x[1] for x in crude_tankers_no.columns.ravel()]
        crude_tankers_no["total_no"] = crude_tankers_no.sum(axis=1)

        return crude_tankers_mbbl, crude_tankers_no


def scenario_age(df, age=[14, 17, 18]):

    df.index.name = "build_date"
    scenario_age = pd.DataFrame(
        index=pd.date_range(start="2000-01-01", end="2030-12-31", freq="m"),
    )
    sc = age
    temp = df.reset_index().copy()
    # print(crude_tankers_mbbl)
    # print(temp)
    dic = {}
    for s in sc:
        dic[s] = {}

        for i in scenario_age.index:
            # print(i)
            y = i - temp.build_date
            temp["years"] = y.apply(lambda x: (float(x.days)) / 365).round(1)
            # temp.drop(columns='build_date', inplace=True)
            dic[s][i] = temp[temp.years > s].sum().round(1)

    # print(dic)
    for i in sc:
        dic[i] = (
            pd.DataFrame(dic[i])
            .T.drop(columns="years")
            .resample("M")
            .mean()
            .fillna(0)
            .reindex(index=pd.date_range(start=df.index[0], end="2030-12-31", freq="m"))
            .fillna(0)
        )
        # print(dic[i])
        try:
            dic[i].drop(columns="build_date", inplace=True)
        except:
            pass
        # dic_result_age_scenario[i] =  crude_fleet_mbbl.resample('M').mean().reindex(
        # index=pd.date_range(start=crude_tankers_mbbl.index[0], end='2030-12-31', freq='m'),method='ffill')
    return dic


def scenario_constant(df, orderbook, constant_rate):
    orderbook.fillna(0, inplace=True)
    scenario_mean = pd.DataFrame(
        index=pd.date_range(start=df.index[-1], end="2025-12-31", freq="m"),
        data=np.nan,
        columns=df.columns,
    )

    for el in scenario_mean.columns:
        scenario_mean[el] = constant_rate
    scenario_mean = orderbook.resample("M").mean().cumsum() - scenario_mean.cumsum()
    scenario_mean.iloc[0] = 0
    scenario_mean.drop(columns="state", inplace=True)
    old = df.drop(columns="state")
    scenario_mean = scenario_mean + old.iloc[-1]
    return scenario_mean

def layout_plotly(fig, title='Your title', template='plotly_white'):
        '''plotly layout'''
    
        fig.update_layout(
                        title={"text": "<b>{}<b>".format(title), "font": {"size": 14}, 'x':0.55},
                        template=template,
                        legend=dict(orientation="v", yanchor="auto", y=1, xanchor="left",
                                    x=0, font={'size':9}, bgcolor="rgba(235,233,233,0.5)"),
                        margin=dict(l=10, r=10, b=30, t=30, pad=4),
                    )
        fig.update_xaxes(
            gridcolor='rgb(184, 234, 253)'
            #nticks=12,
            )
        fig.update_yaxes(
            gridcolor='rgb(193, 252, 186)'
            #nticks=12,
            )
        return fig