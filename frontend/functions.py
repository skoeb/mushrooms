import dash
from dash.dependencies import Output, Input, State
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html
import plotly.io as pio
import pandas as pd
import requests

import resources
from resources import init_control
import layout
import config

pio.templates.default = 'seaborn'

app = dash.Dash(__name__)
app.title = 'Mushroom'
app.layout = layout.html_obj

import logging
log = logging.getLogger()
    

@app.callback(
    Output('updated-control', 'data'),
    [
        Input('temp-slider', 'value'),
        Input('humidity-slider', 'value'),
        Input('fan-slider', 'value')
    ]
)
def update_control(t_values, h_values, f_value):
    response = resources.get_data(config.CONTROL_URL)
    control = response.json()['objects']
    df_orig = pd.DataFrame(control)
    df_new = df_orig.copy()

    t_mask = (df_new['sensor'] == 'temperature')
    df_new.loc[t_mask & (df_new['data_type'] == 'low'), 'value'] = t_values[0]
    df_new.loc[t_mask & (df_new['data_type'] == 'high'), 'value'] = t_values[1]

    h_mask = (df_new['sensor'] == 'humidity')
    df_new.loc[h_mask & (df_new['data_type'] == 'low'), 'value'] = h_values[0]
    df_new.loc[h_mask & (df_new['data_type'] == 'high'), 'value'] = h_values[1]

    f_mask = (df_new['sensor'] == 'fan')
    df_new.loc[f_mask & (df_new['data_type'] == 'on_mins'), 'value'] = f_value
    df_new.loc[f_mask & (df_new['data_type'] == 'off_mins'), 'value'] = 60 - f_value

    changes = (df_orig != df_new).any(1)
    to_patch = df_new[changes]
    for _, row in to_patch.iterrows():
        url = config.CONTROL_URL + '/' + str(row['id'])
        data = row.to_dict()
        response = resources.patch_data(url, data)
        log.info(response)
    print(df_new)
    return df_new.to_json()

    




