try:
    import time as time
    import urequests as requests
except Exception as e:
    print(e)
    import time
    import requests

import json

import config

class RequestRetry():
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 0.375 #should take ~1 minute to run through 10 retries
    STATUS_WHITELIST = [200, 201]

    def _check_ok(self, r):
        if r.status_code in self.STATUS_WHITELIST:
            return True
        else:
            return False

    def _with_retry(self, url, func, **kwargs):
        sleep_time = 0; attempt = 1; complete = False
        while (not complete) & (attempt < self.MAX_RETRIES):
            try:
                time.sleep(sleep_time)
                r = func(url, **kwargs)
                complete = self._check_ok(r)
                sleep_time = 2 ** (attempt * self.BACKOFF_FACTOR)
            except Exception as e:
                pass
        
        if self._check_ok(r):
            print('Successful Request:', r.status_code)
            return r
        else:
            raise Exception(r.status_code)
            return None

    def post(self, url, data=None, headers=None):
        func = requests.post
        self._with_retry(url=url, func=func, data=data, headers=headers)
    
    def get(self, url, data=None, headers=None):
        func = requests.get
        r = self._with_retry(url=url, func=func, data=data, headers=headers)
        return r

def post_data(data, url):
    headers={'Content-Type':'application/json', 'Accept': 'application/json', 'authToken':config.AUTH_TOKEN}
    Session = RequestRetry()
    r = Session.post(url, data=json.dumps(data), headers=headers)

def get_data(url):
    headers={'Content-Type':'application/json', 'Accept': 'application/json', 'authToken':config.AUTH_TOKEN}
    Session = RequestRetry()
    r = Session.get(url, headers=headers)
    return r

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