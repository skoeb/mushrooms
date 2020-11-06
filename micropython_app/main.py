import config

import dht
import network
import machine
import time
import sys
import urequests
import json

def is_debug():
    debug = machine.Pin(config.PIN_DICT['D5'], machine.Pin.IN, machine.Pin.PULL_UP)
    if debug.value() == 0:
        print('Debug mode detected.')
        return True
    return False

def connect_wifi():
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('Connecting to WiFi...')
        sta_if.active(True)
        sta_if.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        while not sta_if.isconnected():
            time.sleep(1)
    print('Network config:', sta_if.ifconfig())

def show_error():
    led = machine.Pin(config.PIN_DICT['LED1'], machine.Pin.OUT)
    led2 = machine.Pin(config.PIN_DICT['LED2'], machine.Pin.OUT)
    for i in range(3):
        led.on()
        led2.off()
        time.sleep(1)
        led.off()
        led2.on()
        time.sleep(1)
    led.on()
    led2.on()

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
        else:
            raise Exception(r.status_code)

    def post(self, url, data=None, headers=None):
        func = urequests.post
        self._with_retry(url=url, func=func, data=data, headers=headers)
    
    def get(self, url, data=None, headers=None):
        func = urequests.get
        self._with_retry(url=url, func=func, data=data, headers=headers)


def post_data(data):
    headers={'Content-Type':'application/json', 'Accept': 'application/json', 'authToken':config.AUTH_TOKEN}
    Session = RequestRetry()
    r = Session.post(config.API_URL, data=json.dumps(data), headers=headers)


def run():
    led = machine.Pin(config.PIN_DICT['LED1'], machine.Pin.OUT)
    led2 = machine.Pin(config.PIN_DICT['LED2'], machine.Pin.OUT)
    switch = machine.Pin(config.PIN_DICT['D5'], machine.Pin.IN, machine.Pin.PULL_UP)
    sensor_pin = machine.Pin(config.PIN_DICT['D2'], machine.Pin.IN, machine.Pin.PULL_UP)
    sensor = dht.DHT11(sensor_pin)
    connect_wifi()
    time.sleep(5)

    count = 1
    switch_status = switch.value()

    while True:

        try:
            led.off()
            led2.off()
            
            sensor.measure()
            temp = sensor.temperature()
            humidity = sensor.humidity()
            data = {'temperature':temp, 'humidity':humidity}
            print(data)
            post_data(data)

            led.on()
            led2.on()
            time.sleep(10)


        except Exception as exc:
            sys.print_exception(exc)
            show_error()

run()