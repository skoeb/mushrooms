import pandas as pd
import json
import requests

import config

def get_data(url):
    headers={
        'Content-Type':'application/json',
        'Accept': 'application/json',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'authToken': config.AUTH_TOKEN
    }

    response = requests.get(url, headers=headers)
    return response

def patch_data(url, data):
    headers={
        'Content-Type':'application/json',
        'Accept': 'application/json',
        'authToken': config.AUTH_TOKEN
    }

    response = requests.patch(url, data=json.dumps(data), headers=headers)
    return response

def parse_control_api(r):
    control_resp = r.json()['objects']
    control_dicts = {}
    for i in control_resp:
        d = i['device_type']
        k = i['sensor']
        data_type = i['data_type']
        value = i['value']

        if d not in control_dicts:
            control_dicts[d] = {}
        if k not in control_dicts[d]:
            control_dicts[d][k] = {}
        control_dicts[d][k][data_type] = value

    return control_dicts

def fetch_control():
    print('FETCHING CONTROL!')
    response = get_data(config.CONTROL_URL)
    control = parse_control_api(response)
    return control

init_control = fetch_control()