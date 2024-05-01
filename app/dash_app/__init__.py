import dash
from dash import html, dcc, callback, Input, Output
from flask_login.utils import login_required, current_user
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import dash_app.influx_query_manager as query_manager
import logging as log
import numpy as np
import math
from sklearn.metrics import mean_absolute_percentage_error
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error
from sklearn.metrics import explained_variance_score
from sklearn.metrics import mean_squared_log_error
import os
import holidays
th_holidays = holidays.TH()

dirname = os.path.dirname(os.path.dirname(__file__))  # Go up one directory from 'dash_app'
user_data_path = os.path.join(dirname, 'web_service/databases/user_data/')

dash_app = None

fig_none = go.Figure()
fig_none.add_trace(go.Scatter(
x=[0, 1, 2, 3, 4, 5, 6, 7, 8],
y=[0, 4, 5, 1, 2, 3, 2, 4, 2],
mode="lines+markers+text",
text=["","","","", "No Data","","", "",""],
textfont_size=40,
))
fig_none.update_layout(
    paper_bgcolor='rgba(0,0,0,0)'    
)

metric_list_none = [
    html.Li("RMSE: 0.00", style={'margin-right': '10px'}),
    html.Li("MAE: 0.00", style={'margin-right': '10px'}),
    html.Li("MAPE: 0.0%", style={'margin-right': '10px'}),
    html.Li("EV: 0.00", style={'margin-right': '10px'}),
    html.Li("RMSLE: 0.00", style={'margin-right': '10px'})
]

default_layout = go.Layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),  
                           margin=dict(t=60),
                            xaxis=dict(title='Time'),
                            yaxis=dict(title='Power consumption (kWh)'),
                            paper_bgcolor='rgba(0,0,0,0)', 
                            uirevision="Don't change")

def if_work_day(date): 
    if ((date in th_holidays) or (date.weekday()>=5)):
        return 0
    else: return 1

def generate_prediciton_fig(df):
    traces = [go.Scatter(x=df.index, y=df['Total Load'], mode='lines', name='Total Load', line=dict(width=2.5))]
    if 'Prediction' in df.columns:
        traces.append(go.Scatter(x=df.index, y=df['Prediction'], mode='lines', name='Prediction', line=dict(width=3, dash='dash')))
    fig = go.Figure(data=traces, layout=default_layout)
    df['If Work Day'] = df.index.map(if_work_day)*np.nanmax(df.values)
    fig.add_trace(go.Scatter(x=df.index, y=df['If Work Day'],
                         fill = 'tozeroy', fillcolor = 'rgba(99, 110, 250, 0.15)',
                         line_shape = 'hvh', line_color = 'rgba(0,0,0,0)',
                         showlegend = False, 
                         hoverinfo=None
                        ))
    return fig

def generate_fig(df):
    fig = px.line(df)
    df['If Work Day'] = df.index.map(if_work_day)*np.nanmax(df.values)
    fig.add_trace(go.Scatter(x=df.index, y=df['If Work Day'],
                         fill = 'tozeroy', fillcolor = 'rgba(99, 110, 250, 0.15)',
                         line_shape = 'hvh', line_color = 'rgba(0,0,0,0)',
                         showlegend = False, 
                         hoverinfo=None
                        ))
    fig.layout = default_layout
    return fig

def get_prediction_stats(actual, prediction):    
    return {'RMSE': math.sqrt(mean_squared_error(actual, prediction)),
            'MAE':  mean_absolute_error(actual, prediction),
            'MAPE': mean_absolute_percentage_error(actual, prediction),
            'EV': explained_variance_score(actual, prediction),
            'RMSLE': math.sqrt(mean_squared_log_error(actual, prediction))}

@callback(Output('total_load_pred', 'figure'), 
          Output('model_metrics', 'children'), 
          Output('model_status', 'children'),
          Output('total_load', 'figure'), 
          Output('by_zone', 'figure'),
          Output('by_type', 'figure'),
          [Input('graph-update', 'n_intervals'),
           Input('time-period-dropdown', 'value')])
def update_total_load(n, query_period):
    user_id = current_user.id
    df = query_manager.get_last_by_period(period=query_period, client_id=f'client-{user_id}')
    if df.empty == False:
        df = query_manager.clean_up_influx_df(df)
        df = query_manager.split_columns_multiindex(df)
        total_load_df = pd.DataFrame(df.sum(axis=1), columns=['Total Load'])
        total_by_zone_df = df.groupby(level=1, axis = 1).sum()
        total_by_type_df = df.groupby(level=2, axis = 1).sum()
        
        total_load_pred_df = total_load_df.resample('D').sum().iloc[1:,:]
        
        metric_list = metric_list_none
        cur_user_pred_path = os.path.join(user_data_path, f'user_{user_id}/user_predictions.csv')
        try:
            pred_df = pd.read_csv(cur_user_pred_path, ).set_index('Date')
        except FileNotFoundError:
            pass
        else:
            pred_df.index = pd.to_datetime(pred_df.index, format='%Y-%m-%d').tz_localize(None)
            pred_df = pred_df.loc[total_load_pred_df.index[0]:, :]
            total_load_pred_df = pd.concat([total_load_pred_df, pred_df], axis=1)
            
            act_pred_intersection_df = total_load_pred_df.dropna().iloc[:-1, :]
            metric_list = metric_list_none
            if act_pred_intersection_df.shape[0] > 5:
                prediction_stats = get_prediction_stats(act_pred_intersection_df['Total Load'], 
                                                        act_pred_intersection_df['Prediction'])
                metric_list = [
                    html.Li(f"RMSE: {prediction_stats['RMSE']:.2f}", style={'margin-right': '10px'}),
                    html.Li(f"MAE: {prediction_stats['MAE']:.2f}", style={'margin-right': '10px'}),
                    html.Li(f"MAPE: {prediction_stats['MAPE']*100:.1f}%", style={'margin-right': '10px'}),
                    html.Li(f"EV: {prediction_stats['EV']:.2f}", style={'margin-right': '10px'}),
                    html.Li(f"RMSLE: {prediction_stats['RMSLE']:.2f}", style={'margin-right': '10px'})
                ]
        
        return generate_prediciton_fig(total_load_pred_df), \
                metric_list, \
                f'Model Status: {current_user.model_info.model_train_status}', \
                generate_fig(total_load_df), \
                generate_fig(total_by_zone_df), \
                generate_fig(total_by_type_df)
    else: return fig_none, metric_list_none, f'Model Status: {current_user.model_info.model_train_status}', fig_none, fig_none, fig_none


def create_dash_application(flask_app):
    global dash_app
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    dash_app = dash.Dash(server=flask_app, name="Dashboard", url_base_pathname="/dash/", external_stylesheets=external_stylesheets)
    dash_app.layout = html.Div(
        children=[
                dcc.Dropdown(
                id='time-period-dropdown',
                options=[
                    {'label': '2 Weeks', 'value': '2w'},
                    {'label': '1 Month', 'value': '1mo'},
                    {'label': '2 Months', 'value': '2mo'},
                    {'label': '4 Months', 'value': '4mo'},
                    {'label': 'Half a year', 'value': '6mo'},
                    {'label': 'One year', 'value': '12mo'},
                ],
                value='2m'
            ),
            html.H4('Daily Total Load Prediction'),
            html.Div(id='total_load_pred-text'),
            dcc.Graph(
                id="total_load_pred",
                figure = fig_none
            ),
            html.H5('Model Metrics'),
            html.Ul(metric_list_none, 
                    style={'list-style-type': 'none', 'display': 'flex', 'padding': '0', 'margin': '0', 'overflow-x': 'auto'}, 
                    id='model_metrics'),
            html.P('Model Status: ', id='model_status'),
            html.Hr(),
            html.H4('Total Load'),
            html.Div(id='total_load-text'),
            dcc.Graph(
                id="total_load",
                figure = fig_none
            ),
            html.H4('Load by Zone'),
            html.Div(id='by_zone-text'),
            dcc.Graph(
                id="by_zone",
                figure = fig_none
            ),
            html.H4('Load by Type'),
            html.Div(id='by_type-text'),
            dcc.Graph(
                id="by_type",
                figure = fig_none
            ),
            dcc.Interval(
                id = 'graph-update',
                interval = 5000,
                n_intervals = 0
            ),
        ],
        style={'padding': '60px'}
    )

    for view_function in dash_app.server.view_functions:
        if view_function.startswith(dash_app.config.url_base_pathname):
            dash_app.server.view_functions[view_function] = login_required(
                dash_app.server.view_functions[view_function]
            )

    return dash_app