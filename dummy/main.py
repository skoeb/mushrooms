import machine
from machine import Pin
import dht
import json

try:
    import utime as time
except Exception as e:
    print(e)
    import time

from adafruit_sgp30 import Adafruit_SGP30
import config

def get_temperature_and_humidity():
    pin = Pin(
            config.INPUT_PIN_DICT['dht11'],
            Pin.IN,
            Pin.PULL_UP)
    dht11 = dht.DHT11(pin)

    retry = 0
    while retry < 3:
        try:
            dht11.measure()
            break
        except Exception:
            retry +=1
            time.sleep(3)
            print('....retrying temperature and humidity measure')

    temperature = dht11.temperature()
    humidity = dht11.humidity()
    pin.off()

    if temperature == 0:
        temperature = 999
    if humidity == 0:
        humidity = 999
    return {'temperature': temperature, 'humidity': humidity}

def write_sgp30_baseline(sgp30):
    disk_baseline = read_sgp30_baseline(sgp30)
    cur_baseline = sgp30.get_iaq_baseline()
    print('....comparing disk baseline {}, to current {}'.format(
                                            disk_baseline, cur_baseline))
    if disk_baseline != cur_baseline:
        print('....writing new baseline to .json')
        with open('sgp30_baseline.json', 'w') as handle:
            json.dump(cur_baseline, handle)

def read_sgp30_baseline(sgp30):
    try:
        with open('sgp30_baseline.json', 'r') as handle:
            baseline = json.load(handle)
    except OSError:
        baseline = [0, 0]
    return baseline

def initialize_sgp30():
    scl = Pin(config.INPUT_PIN_DICT['sgp30_scl'])
    sda = Pin(config.INPUT_PIN_DICT['sgp30_sda'])
    i2c = machine.I2C(scl=scl, sda=sda)
    sgp30 = Adafruit_SGP30(i2c)
    sgp30.iaq_init()
    iaq_baseline = read_sgp30_baseline(sgp30)
    if iaq_baseline != [0, 0]:    
        sgp30.set_iaq_baseline(*iaq_baseline)
    print('....initialized sgp30, baseline: {}'.format(iaq_baseline))
    return sgp30

def get_co2(reading, sgp30):
    sgp30.set_iaq_rel_humidity(
        rh=reading['humidity'],
        temp=reading['temperature']
    )
    co2eq, tvoc = sgp30.iaq_measure()
    return {'co2eq': co2eq, 'tvoc': tvoc}

r = {}
sgp30 = initialize_sgp30()
while True:
    r.update(get_temperature_and_humidity())
    r.update(get_co2(r, sgp30))
    print(r)

    minute = time.localtime()[4]
    if minute % 60 == 0:

    time.sleep(60)