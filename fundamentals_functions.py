

import plotly.express as px
from itertools import cycle
import pandas as pd
import datetime as dt
import pyodbc
import sys
import plotly.graph_objects as go


sys.path.append(r"L:\SHARED\PALE\my_python_modules\my_functions")
from my_functions_old import My_date, get_prices



class Graph:
    
    def __init__(self):
        self.palette = cycle(px.colors.sequential.Rainbow)
        
        
    '''Class to make redundant graph quickly'''
    
    def cumulative_graph(self, df_plot, column_to_plot,
                         periods_to_plot=[],
                        periods_not_to_plot=[], colors=[],
                         plot_all_traces=False,
                         measures_to_show = ['mean','median','quantile_75', 'quantile_25'],
                         legend_measures = 'Since X',
                         x_axis_title='',
                         y_axis_title = '',
                         graph_title='Your title',
                         grouper='%Y-%m',
                        palette_measures={}):
        
        ''' index needs to be datetime'''
        df_plot = df_plot.copy()
        df_plot['grouper'] = df_plot.index.strftime(grouper)
        df_plot = df_plot[df_plot.index<My_date().datetime]
        dic = {}
        dic_months_plot = {}
        
        
            
        
        for n, g in df_plot.groupby('grouper'):
            temp=g.copy()
            temp = temp.groupby(df_plot.index.name).sum()
            temp['cum_sum'] = temp[column_to_plot].cumsum()
            if grouper=='%Y-%m':
                last = pd.date_range(start=n+'-01', periods=1, freq='M')[0]
            elif grouper=='%Y-%W':
                last = pd.date_range(start=temp.index.min(), periods=1, freq='W')[0]
            else:
                return print('choose %Y-%m or %Y-%W as grouper')
           
            temp = temp.reindex(pd.date_range(start=temp.index.min(), end=last, freq='D')).fillna(method='ffill')
            temp['days'] = (last - pd.to_datetime(temp.index)).days
            temp = temp[temp.index<My_date().datetime]
            if plot_all_traces == True:
                dic[n] = temp
                dic_months_plot[n] = temp
            else:
                if n != df_plot.index.max().strftime(grouper) and n not in periods_not_to_plot:
                    dic[n]=temp
                if n in periods_to_plot:
                    dic_months_plot[n] = temp

        maxx, minn = pd.concat(dic.values()).groupby('days').cum_sum.max(), pd.concat(dic.values()).groupby('days').cum_sum.min()
        dic_measures = dict(
            mean = pd.concat(dic.values()).groupby('days').cum_sum.mean(),
            quantile_75 = pd.concat(dic.values()).groupby('days').cum_sum.quantile(0.75),
            quantile_25 = pd.concat(dic.values()).groupby('days').cum_sum.quantile(0.25),
            median = pd.concat(dic.values()).groupby('days').cum_sum.quantile(0.50))

        fig = go.Figure()    
        fig.add_trace(
                go.Scatter(x=maxx.index,
                          y=maxx,
                        line_color="lightgray",
                          name='Max',
                           mode='lines',
                          connectgaps=True))
        fig.add_trace(
                go.Scatter(x=minn.index,
                          y=minn,
                         fill="tonexty",  # fill area between trace0 and trace1
                            mode=None,
                            line_color="lightgray",
                          name='Min',
                          connectgaps=True))
        if len(palette_measures.keys())==0:
            palette_measures = {'mean':'blue', 'quantile_25':'green',
                           'quantile_75':'green', 'median':'green'}
        else:
            pass
        
        for el in measures_to_show:
            
            fig.add_trace(
                    go.Scatter(x=dic_measures[el].index,
                              y=dic_measures[el],

                                mode='lines',
                               line = {'dash':'dash'},
                                line_color=palette_measures[el],
                              name = el+' '+legend_measures,
                              connectgaps=True))
        
        
        if plot_all_traces == False:
            if colors == []:
                colors = cycle(['purple', 'black', 'red'])
            else:
                colors = cycle(colors)
                
            for k, v in dic_months_plot.items():
                fig.add_trace(
                    go.Scatter(x=v.days,
                          y=v['cum_sum'],
                          name=k,
                               mode='lines',
                          line=dict(color=next(colors)),
                          connectgaps=True))
        else:
            colors = self.palette
            for k, v in dic_months_plot.items():
                fig.add_trace(
                    go.Scatter(x=v.days,
                          y=v['cum_sum'],
                          name=k,
                               mode='lines',
                          line=dict(color=next(colors)),
                          connectgaps=True))
                
        
        
        fig.update_layout(
            title={"text": "<b>{}<b>".format(graph_title),
                        "font": {"size": 14},
                        "x": 0.50},
                         margin=dict(l=0, r=0, b=0, t=30, pad=0),
            template="plotly_white",
            width=900,
            height=500,
             legend=dict(
                orientation="v",
                yanchor="auto",
                y=1,
                xanchor="left",
                x=0.01,
                font={"size": 11},
                bgcolor="rgba(235,233,233,0.5)",
                    ),)
        fig.update_xaxes(autorange="reversed",
                         gridcolor="rgb(193, 252, 186)",
                        title='{}'.format(x_axis_title))
        fig.update_yaxes(gridcolor="rgb(184, 234, 253)",
                        title='{}'.format(y_axis_title))
        return fig




class WeeklyReport:
    
    def __init__(self):
        self.conn = pyodbc.connect("Driver={SQL Server};"
                        "Server=GVASQL19Lis;"
                        "Database = Fundamentals;"
                        "Trusted_Connection=yes"
                    )
        self.vessel_types = ['VLCC', 'Suezmax', 'Aframax']
          
    def get_loadings_data_crude(self, vessel_type=['VLCC'], zones_origin=[]):
        '''get the data from KPLER_OIL_TRADES_V1 daily loadings'''
        
        vessel_type = WeeklyReport().sql_format(vessel_type)
        
        if len(zones_origin) >0:
            zones_origin = WeeklyReport().sql_format(zones_origin)
            sql = '''
            SELECT Count( DISTINCT [IMO (vessel)] ), [Upload Datetime] snapshot, CAST([Start (origin)] AS DATE) date
            FROM Fundamentals.dbo.KPLER_OIL_TRADES_V1
            WHERE [Vessel type] IN ({})
            AND [Trade status] = 'loading'
            AND DATEPART(HOUR,[Upload Datetime]) = 18
            AND [Upload Datetime] > '2020-01-01'
            AND [Scrape Type] = 'Hourly Scrape'
            AND ( [Country (origin)] IN ({}) OR [Zone Origin] IN ({}) OR [Zone Origin] IN ({}) 
            OR [Installation origin] IN ({}) OR [Subcontinent (origin)] IN ({}))
            GROUP BY [Upload Datetime], CAST([Start (origin)] AS DATE)
            '''.format(vessel_type,
                      zones_origin,
                      zones_origin,
                      zones_origin,
                      zones_origin,
                      zones_origin)
        else:         
            sql = '''
                SELECT Count( DISTINCT [IMO (vessel)] ), [Upload Datetime] snapshot, CAST([Start (origin)] AS DATE) date
                FROM Fundamentals.dbo.KPLER_OIL_TRADES_V1
                WHERE [Vessel type] IN ({})
                AND [Trade status] = 'loading'
                AND DATEPART(HOUR,[Upload Datetime]) =18
                AND [Upload Datetime] > '2020-01-01'
                AND [Scrape Type] = 'Hourly Scrape'
                GROUP BY [Upload Datetime], CAST([Start (origin)] AS DATE)
                '''.format(vessel_type)
            
        df = pd.read_sql(sql, self.conn)
        df.columns = ['imo', 'snap', 'date']
        df.date = pd.to_datetime(df.date)
        df.set_index('date', drop=True, inplace=True)
        return df

    def get_loadings_AG_VLCC_litasco(self, date_from='2021-01-01'):
        '''return the vlcc loaded in the specific polygons'''
        sql = ''' SELECT * FROM Fundamentals.dbo.vessels_position_dash WHERE vessel_type='VLCC' and family='Dirty' and date>'{}' 
        '''.format(date_from)
        df = pd.read_sql(sql, self.conn)

        df.date = pd.to_datetime(df.date)
        liste_df = []
        for n, g in df.groupby('IMO'):
            temp = g.sort_values(by='date', ascending=True)
            days=[]
            i=0
            etat = temp.state1.tolist()[0]
            for el in temp.state1:
                if el == etat:
                    i+=1
                    days.append(i)
                else:
                    etat=el 
                    i=1
                    days.append(i) 

            temp['cumsum'] = days

            liste_df.append(temp)
            del temp

        dff = pd.concat(liste_df)
        loading = dff[(dff.state1=='loaded') & (dff['cumsum']==1) &
                      (dff.polygons.isin(['AG','Red Sea']))].groupby('date').IMO.count()[dff.date.min()+dt.timedelta(days=1):]
        return pd.DataFrame({'loading':loading})
    
    def get_fixtures(self, vessel_type=['VLCC']):
        '''return the fixtures graphs'''
        
        vessel_type = WeeklyReport().sql_format(vessel_type)
        sql="""SELECT  * FROM Fundamentals.dbo.Shipping_Fixtures_SignalOcean WHERE vessel_class IN ({})

            """.format(vessel_type)
        df_fixtures= pd.read_sql(sql, self.conn)
        df_fixtures = df_fixtures[~df_fixtures.duplicated(subset=['fixtures_id'])]
        return df_fixtures
        
   
    @staticmethod
    def get_zones(zone):
        return My_Kpler().zones_client.search(zone)

    @staticmethod
    def sql_format(l):
        s = str(["{}".format(x) for x in l]).replace("[", "").replace("]", "")
        return s
    

    def get_loadings_data_cpp(self, vessel_type=['VLCC'], zones_origin=[]):
            '''get the data from KPLER_CPP_TRADES_V1 daily loadings'''

            vessel_type = WeeklyReport().sql_format(vessel_type)

            if len(zones_origin) >0:
                zones_origin = WeeklyReport().sql_format(zones_origin)
                sql = '''
                SELECT Count( DISTINCT [IMO (vessel)] ), [Upload Datetime] snapshot, CAST([Start (origin)] AS DATE) date
                FROM Fundamentals.dbo.KPLER_OIL_TRADES_V1
                WHERE [Vessel type] IN ({})
                AND [Trade status] = 'loading'
                AND DATEPART(HOUR,[Upload Datetime]) = 18
                AND [Upload Datetime] > '2020-01-01'
                AND [Scrape Type] = 'Hourly Scrape'
                AND ( [Country (origin)] IN ({}) OR [Zone Origin] IN ({}) OR [Zone Origin] IN ({}) 
                OR [Installation origin] IN ({}) OR [Subcontinent (origin)] IN ({}))
                GROUP BY [Upload Datetime], CAST([Start (origin)] AS DATE)
                '''.format(vessel_type,
                          zones_origin,
                          zones_origin,
                          zones_origin,
                          zones_origin,
                          zones_origin)
            else:         
                sql = '''
                    SELECT Count( DISTINCT [IMO (vessel)] ), [Upload Datetime] snapshot, CAST([Start (origin)] AS DATE) date
                    FROM Fundamentals.dbo.KPLER_OIL_TRADES_V1
                    WHERE [Vessel type] IN ({})
                    AND [Trade status] = 'loading'
                    AND DATEPART(HOUR,[Upload Datetime]) =18
                    AND [Upload Datetime] > '2020-01-01'
                    AND [Scrape Type] = 'Hourly Scrape'
                    GROUP BY [Upload Datetime], CAST([Start (origin)] AS DATE)
                    '''.format(vessel_type)

            df = pd.read_sql(sql, self.conn)
            df.columns = ['imo', 'snap', 'date']
            df.date = pd.to_datetime(df.date)
            df.set_index('date', drop=True, inplace=True)
            return df
    

    def get_loadings_data_crude_kb(self, vessel_type=['VLCC'], zones_origin=[]):
        '''get the data from KPLER_OIL_TRADES_V1 daily loadings'''

        vessel_type = WeeklyReport().sql_format(vessel_type)

        if len(zones_origin) >0:
            zones_origin = WeeklyReport().sql_format(zones_origin)
            sql = '''
            SELECT SUM([Volume (kb)]), [Upload Datetime] snapshot, CAST([Start (origin)] AS DATE) date
            FROM Fundamentals.dbo.KPLER_OIL_TRADES_V1
            WHERE [Vessel type] IN ({})
            AND [Trade status] = 'loading'
            AND DATEPART(HOUR,[Upload Datetime]) = 18
            AND [Upload Datetime] > '2020-01-01'
            AND [Scrape Type] = 'Hourly Scrape'
            AND ( [Country (origin)] IN ({}) OR [Zone Origin] IN ({}) OR [Zone Origin] IN ({}) 
            OR [Installation origin] IN ({}) OR [Subcontinent (origin)] IN ({}))
            GROUP BY [Upload Datetime], CAST([Start (origin)] AS DATE)
            '''.format(vessel_type,
                      zones_origin,
                      zones_origin,
                      zones_origin,
                      zones_origin,
                      zones_origin)
        else:         
            sql = '''
                SELECT SUM([Volume (kb)]), [Upload Datetime] snapshot, CAST([Start (origin)] AS DATE) date
                FROM Fundamentals.dbo.KPLER_OIL_TRADES_V1
                WHERE [Vessel type] IN ({})
                AND [Trade status] = 'loading'
                AND DATEPART(HOUR,[Upload Datetime]) =18
                AND [Upload Datetime] > '2020-01-01'
                AND [Scrape Type] = 'Hourly Scrape'
                GROUP BY [Upload Datetime], CAST([Start (origin)] AS DATE)
                '''.format(vessel_type)

        df = pd.read_sql(sql, self.conn)
        df.columns = ['kb', 'snap', 'date']
        df.date = pd.to_datetime(df.date)
        df.set_index('date', drop=True, inplace=True)
        return df