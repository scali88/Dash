# -*- coding: utf-8 -*-
"""
Created on Tue Mar  9 11:26:18 2021

@author: pale
"""
import pickle
import pandas as pd
import datetime as dt
import pyodbc

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVR
from sklearn.model_selection import GridSearchCV
from sklearn import metrics
from sklearn.linear_model import SGDRegressor
from sklearn import linear_model
import statsmodels.api as sm

import glob
import sys

sys.path.append(r"L:\SHARED\PALE\my_python_modules\my_functions")
from my_functions_old import My_date, get_prices

# loading the models:


def import_jbc_models():

    p = r"\\gvaps1\DATAROOT\data\SHARED\PALE\Shipping\S&D\flow_model\JBC_kpler\Crude\\"
    flows = ["AG-Asia", "AG-Europe", "AG-US", "Latam-Asia", "WAF-Asia", "Small_flows"]
    paths = [p + x + "_VLCC_flow_model.sav" for x in flows]
    dic_models = dict(zip(flows, [pickle.load(open(x, "rb")) for x in paths]))

    dic_models["kpler_flow_reg"] = pickle.load(
        open(
            r"\\gvaps1\DATAROOT\data\SHARED\PALE\Shipping\S&D\flow_model\Kpler_flows\kpler_flows_VLCC_regression.sav",
            "rb",
        )
    )
    return dic_models


def get_fwd_curve_from_db(index_name, date="last"):
    """get forward curve for a specific route on a specific date"""

    conn = pyodbc.connect("Driver={SQL Server};"
        "Server=GVASQL19Lis;"
        "Database = Fundamentals;"
        "Trusted_Connection=yes")


    if date != "last":
        try:
            sql = """SELECT * FROM Fundamentals.dbo.[Shipping Prices] 
        WHERE index_name='{}' 
        AND date='{}' AND source='Litasco' """.format(
                index_name, date
            )
            df = pd.read_sql(sql, conn)
        except:
            return print("error with requested index or date")
    else:
        try:
            sql = """SELECT * FROM Fundamentals.dbo.[Shipping Prices] 
            WHERE index_name='{}' AND source='Litasco'
            AND date=(SELECT MAX(date) FROM Fundamentals.dbo.[Shipping Prices] 
            WHERE index_name='{}') """.format(
                index_name, index_name
            )
            df = pd.read_sql(sql, conn)
        except:
            return print("error with requested index or date")
    df = df[~df.index_type.isin(["cash", "M0"])]
    months = [x for x in df.index_type.unique() if x.find('M')>-1]
    df = df[df.index_type.isin(months)]
    return df



def prices_and_curve(
    date="last", index_name="TD3_eiger-TCE", index_type=["M1"], offset_2020=False
):

    if offset_2020 == True:
        td3_m1_gen = get_prices(index_name=index_name, index_type=index_type)[
            :"2019-01-01"
        ]
        td3_m1_gen["month"] = td3_m1_gen.index.month
        td3_m1_gen = td3_m1_gen.groupby("month").mean()
        td3_m1_gen.index = pd.date_range(start="2020-01-01", periods=12, freq="M")
        td3_m1_gen = td3_m1_gen[:"2020-07-01"]
        temp = get_prices(index_name=index_name, index_type=index_type).copy()
        temp = temp.resample("M").mean()
        temp.loc["2020-01-01":"2020-07-01", index_name] = td3_m1_gen[index_name]
        td3 = temp
    else:
        td3 = get_prices(index_name=index_name, index_type=index_type)
        td3 = td3.resample("M").mean()
    td3.columns = [index_name]
    # print(td3.index[-1]+dt.timedelta(days=33))
    # td3 = pd.DataFrame(index=pd.date_range(start=td3.index[0], end=td3.index[-1], freq='M'),
    #                 data = td3.TD3_eiger.values, columns=['TD3_eiger'])
    curves = get_fwd_curve_from_db(index_name, date=date)
    curves = curves[curves.index_type != "M1"]
    curves = curves.sort_values(by="settlement_date")
    fut = pd.DataFrame(
        index=pd.date_range(
            start=td3.index[-1] + dt.timedelta(days=10), periods=len(curves), freq="M"
        ),
        data=curves.value.values,
        columns=[index_name],
    )
    td3_m1_fut = pd.concat([td3, fut], axis=0).round(3)
    return td3_m1_fut


def get_fwd_dates(index_name="TD3_eiger-TCE"):
    """return the list of the fwd dates available"""

    conn = pyodbc.connect("Driver={SQL Server};"
                        "Server=GVASQL19Lis;"
                        "Database = Fundamentals;"
                        "Trusted_Connection=yes"
                    )

    sql = """SELECT [date] FROM Fundamentals.dbo.[Shipping Prices] 
    WHERE index_name='{}' 
    AND source='Litasco'
    AND index_type='M1' """.format(
        index_name
    )
    df = pd.read_sql(sql, conn)
    return df


def ols_cu_price(df, end="2021-02-28", index_name="TD3_eiger-TCE"):
    X = df.dropna().cu[:end]
    y = df.dropna()[index_name][:end]
    # X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.15, random_state = random_state)

    X_ = sm.add_constant(X)  # adding a constant

    model = sm.OLS(y, X_).fit()
    predictions_past = model.predict(X_)
    r2 = metrics.r2_score(df.dropna()[index_name][:end], predictions_past)

    X_ = sm.add_constant(df.dropna().cu)
    predictions = model.predict(X_)

    return predictions, r2


def get_scenaris():
    files = glob.glob(r"\\gvaps1\DATAROOT\data\SHARED\PALE\Dash\loaded_scenari\*.csv")
    dic = {}
    for f in files:
        name = f[f.rfind("\\") + 1 : f.rfind(".")]
        dic[name] = pd.read_csv(f, usecols=list(range(13)))
    return dic
