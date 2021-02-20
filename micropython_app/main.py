import config

import dht
import network
import machine
from ntptime import settime
import utime
import sys
import urequests
import json

settime()

def deepsleep():
    print('Going into deepsleep for:', config.INTERVAL)
    rtc = machine.RTC()
    rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
    rtc.alarm(rtc.ALARM0, config.INTERVAL * 1000)
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
            utime.sleep(1)
    print('Network config:', sta_if.ifconfig())


def show_error():
    led = machine.Pin(config.PIN_DICT['LED1'], machine.Pin.OUT)
    led2 = machine.Pin(config.PIN_DICT['LED2'], machine.Pin.OUT)
    for i in range(3):
        led.on()
        led2.off()
        utime.sleep(1)
        led.off()
        led2.on()
        utime.sleep(1)
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
                utime.sleep(sleep_time)
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
            utime.sleep(2)
            print('....retrying temperature and humidity measure')

    temperature = dht11.temperature()
    humidity = dht11.humidity()

    if temperature == 0:
        temperature = 999
    if humidity == 0:
        humidity = 999
    return {'temperature': temperature, 'humidity': humidity}

def get_moisture():
    power_pin = machine.Pin(config.PIN_DICT['D2'], mode=machine.Pin.OUT)
    power_pin.on()
    utime.sleep(2)

    sensor = machine.ADC(0)

    retry = 0
    while retry < 3:
        try:
            moisture_reading = sensor.read()
            break
        except Exception:
            retry +=1
            utime.sleep(2)
            print('....retrying moisture measure')
    
    power_pin.off()

    calc_moisture_pct = lambda x: 100 - ((x - 400)/(1024-400) * 100) #TODO: add 180k resistor https://arduino.stackexchange.com/questions/71949/voltage-divider-and-nodemcu-inputs
    moisture_pct = calc_moisture_pct(moisture_reading)
    return {'moisture_reading':moisture_reading, 'moisture_pct':moisture_pct}

def _cycle_relay(pin, reading, status, low, high):
    r_pin = machine.Pin(config.PIN_DICT[pin], mode=machine.Pin.OUT)
    print('pin: {}, reading: {}, ({} {} / {})'.format(pin, reading, status, low, high))
    # if currently on, but not yet at upper thresh -> ON
    if status & (reading < high):
        print('....keeping on relay pin {}'.format(pin))
        r_pin.on()
        return True # on

    # if below lower thresh -> ON
    elif reading <= low:
        print('....turning on relay pin {}'.format(pin))
        r_pin.on()
        return True
    
    # if in stable range and off -> OFF
    else:
        print('....turning off relay pin {}'.format(pin))
        r_pin.off()
        return False

def _cycle_intermittent(pin, on_mins, off_mins):
    i_pin = machine.Pin(config.PIN_DICT[pin], mode=machine.Pin.OUT)
    minute = utime.localtime()[4]
    print('pin: {}, {} ({} / {}))'.format(pin, minute, on_mins, off_mins))
    if minute < on_mins:
        print('....turning on inter pin {}'.format(pin))
        i_pin.on()
        return True
    else:
        print('....turning off inter pin {}'.format(pin))
        i_pin.off()
        return False

def cycle_relays(data, p_status):
    status_dict = {}
    for relay, values in config.RELAYS.items():
        dict_key = "{}_status".format(relay)
        status_dict[dict_key] = _cycle_relay(
            reading=data[relay], status=p_status[dict_key], **values)
    
    led2 = machine.Pin(config.PIN_DICT['LED2'], machine.Pin.OUT)
    if any(status_dict.values()):
        led2.off()
    else:
        led2.on()
    return status_dict
        
def cycle_intermittents(data, p_status):
    status_dict = {}
    for inter, values in config.INTERMITTENTS.items():
        dict_key = "{}_status".format(inter)
        status_dict[dict_key] = _cycle_intermittent(
            **values
        )
    return status_dict

def turn_off_pins():
    all_outputs = {}
    all_outputs.update(config.RELAYS)
    all_outputs.update(config.INTERMITTENTS)
    for k,v in all_outputs.items():
        pin = machine.Pin(config.PIN_DICT[v['pin']])
        pin.on()


def run():
    turn_off_pins()
    connect_wifi()
    relay_status = {"{}_status".format(r): False for r in config.RELAYS.keys()}
    inter_status = {"{}_status".format(i): False for i in config.INTERMITTENTS.keys()}

    while True:

        try:
            print('starting loop')
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
        print('sleeping for {} seconds'.format(config.INTERVAL))
        utime.sleep(config.INTERVAL)

run()