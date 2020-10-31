import config

import network
import machine
import time
import sys
import urequests
import json

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

def post_data(data):
    headers={'Content-Type':'application/json', 'Accept': 'application/json'}
    api_url = 'http://127.0.0.1:5000/api/sensor_readings'
    r = urequests.post(api_url, data=json.dumps(data), headers=headers)
    print(r.status_code)

def run():
    try:
        connect_wifi()
        led = machine.Pin(config.PIN_DICT['LED1'], machine.Pin.OUT)
        led2 = machine.Pin(config.PIN_DICT['LED2'], machine.Pin.OUT)
        switch = machine.Pin(config.PIN_DICT['D5'], machine.Pin.IN, machine.Pin.PULL_UP)

        count = 1
        while True:
            switch_status = switch.value()
            
            if switch.value() != switch_status:

                led.off()
                led2.off()

                data = {'rand':count}
                post_data(data)
                count += 1
                switch_status = switch.value()

                led.on()
                led2.on()

    except Exception as exc:
        sys.print_exception(exc)
        show_error()

