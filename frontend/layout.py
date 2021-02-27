import dash
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html

import resources
from resources import fetch_control
import layout



html_obj = html.Div(
    [
        html.H1('Mushroom Control Panel'),

        html.Div([

            html.Div([
                html.H4('Temperature:'),
                dcc.RangeSlider(
                    id='temp-slider',
                    min=min(60, fetch_control()['relay']['temperature']['low']), 
                    max=max(90, fetch_control()['relay']['temperature']['high']),
                    step=1,
                    value=[
                        fetch_control()['relay']['temperature']['low'],
                        fetch_control()['relay']['temperature']['high'],
                    ],
                    marks = {i: f"{i} °F" for i in range(60, 91, 5)},
                    allowCross=False,
                    persistence=False,
                    persistence_type='local',
                )
            ],
            style={'padding': 20}, 
            ),

            html.Div([
                html.H4('Humidity:'),
                dcc.RangeSlider(
                    id='humidity-slider',
                    min=min(40, fetch_control()['relay']['humidity']['low']), 
                    max=max(100, fetch_control()['relay']['humidity']['high']),
                    step=1,
                    value=[
                        fetch_control()['relay']['humidity']['low'],
                        fetch_control()['relay']['humidity']['high'],
                    ],
                    marks = {i: f"{i}%" for i in range(40, 101, 10)},
                    allowCross=False,
                    persistence=False,
                    persistence_type='local',
                )
            ],
            style={'padding': 20}, 
            ),

            html.Div([
                html.H4('Fan:'),
                dcc.Slider(
                    id='fan-slider',
                    min=0, 
                    max=60,
                    step=1,
                    value=fetch_control()['inter']['fan']['on_mins'],
                    marks = {i: f"{i} m" for i in range(0, 61, 10)},
                    persistence=False,
                    persistence_type='local',
                )
            ])
        ],
        style={'padding': 20}, 
        ),

        # html.Div(id='current-control-text'),
        # dcc.Interval(
        #     id='current-control-object',
        #     interval=15*1000,
        #     n_intervals=0
        # ),

dcc.Store(id='updated-control'),

],
className='ten columns offset-by-one'
)