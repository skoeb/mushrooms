from micropython_demo.config import INTERMITTENTS
import config

import dht
import network
import machine
import time
from datetime import datetime
import sys
import urequests
import json

def deepsleep():
    print('Going into deepsleep for:', config.LOG_INTERVAL)
    rtc = machine.RTC()
    rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
    rtc.alarm(rtc.ALARM0, config.LOG_INTERVAL * 1000)
    machine.deepsleep()

def is_debug():
    debug = machine.Pin(config.PIN_DICT[config.DEBUG_PIN], machine.Pin.IN, machine.Pin.PULL_UP)
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

def get_temperature_and_humidity():
    sensor_pin = machine.Pin(config.PIN_DICT['D7'], machine.Pin.IN, machine.Pin.PULL_UP)
    dht11 = dht.DHT11(sensor_pin)
    
    retry = 0
    while retry < 3:
        try:
            dht11.measure()
            break
        except Exception:
            retry +=1
            time.sleep(2)
            print('....retrying temperature and humidity measure')

    temperature = dht11.temperature()
    humidity = dht11.humidity()
    return {'temperature': temperature, 'humidity': humidity}

def get_moisture():
    power_pin = machine.Pin(config.PIN_DICT['D2'], mode=machine.Pin.OUT)
    power_pin.on()
    time.sleep(2)

    sensor = machine.ADC(0)

    retry = 0
    while retry < 3:
        try:
            moisture_reading = sensor.read()
            break
        except Exception:
            retry +=1
            print('....retrying moisture measure')
    
    power_pin.off()

    calc_moisture_pct = lambda x: 100 - ((x - 400)/(1024-400) * 100) #TODO: add 180k resistor https://arduino.stackexchange.com/questions/71949/voltage-divider-and-nodemcu-inputs
    moisture_pct = calc_moisture_pct(moisture_reading)
    return {'moisture_reading':moisture_reading, 'moisture_pct':moisture_pct}

def _cycle_relay(pin, reading, status, low, high):
    r_pin = machine.Pin(config.PIN_DICT[pin], mode=machine.Pin.OUT)
    
    # if currently on, but not yet at upper thresh -> ON
    if status & (reading < high):
        r_pin.on()
        return True # on

    # if below lower thresh -> ON
    elif reading <= low:
        r_pin.on()
        return True
    
    # if in stable range and off -> OFF
    else:
        r_pin.off()
        return False

def _cycle_intermittent(pin, on_mins, off_mins):
    i_pin = machine.Pin(config.PIN_DICT[pin], mode=machine.Pin.OUT)
    minute = datetime.now().minute
    if minute < on_mins:
        i_pin.on()
        return True
    elif minute >= on_mins:
        i_pin.off()
        return False

def cycle_relays(data, p_status):
    status_dict = {}
    for relay, values in config.RELAYS.items():
        status_dict[f"{relay}_status"] = _cycle_relay(
            reading=data[relay], status=p_status[f"{relay}_status"], **values)
    
    led2 = machine.Pin(config.PIN_DICT['LED2'], machine.Pin.OUT)
    if any(status_dict.values()):
        led2.off()
    else:
        led2.on()
    return status_dict
        
def cycle_intermittents(data, p_status):
    status_dict = {}
    for inter, values in config.INTERMITTENTS.items():
        status_dict[f"{inter}_status"] = _cycle_intermittent(
            **values
        )
    return status_dict

def run():

    connect_wifi()
    relay_status = {f"{relay}_status": False for relay in config.RELAYS.keys()}
    inter_status = {f"{inter}_status": False for inter in config.INTERMITTENTS.keys()}

    while True:

        try:
            led = machine.Pin(config.PIN_DICT['LED1'], machine.Pin.OUT)
            led.off()

            data = {}
            data.update(get_temperature_and_humidity())
            # data.update(get_moisture())

            relay_status = cycle_relays(data, relay_status)
            inter_status = cycle_intermittents(data, inter_status)
            data.update(relay_status)
            data.update(inter_status)

            print(data)
            post_data(data)
            led.on()

        except Exception as exc:
            sys.print_exception(exc)
            show_error()
        
        time.sleep(60)

run()