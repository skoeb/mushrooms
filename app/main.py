import dht
import neopixel
import machine
from ntptime import settime
import sys

try:
    import utime as time
except Exception as e:
    print(e)
    import time

import config
import helper
import connection

def get_temperature_and_humidity():
    pin = machine.Pin(
        config.INPUT_PIN_DICT['dht11'],
        machine.Pin.IN,
        machine.Pin.PULL_UP)
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

    temperature = helper.celsius_to_fahrenheit(temperature)
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
            time.sleep(2)
            print('....retrying moisture measure')
    
    power_pin.off()

    calc_moisture_pct = lambda x: 100 - ((x - 400)/(1024-400) * 100) #TODO: add 180k resistor https://arduino.stackexchange.com/questions/71949/voltage-divider-and-nodemcu-inputs
    moisture_pct = calc_moisture_pct(moisture_reading)
    return {'moisture_reading':moisture_reading, 'moisture_pct':moisture_pct}

def _cycle_relay(pin, reading, status, low, high):
    r_pin = machine.Pin(pin, mode=machine.Pin.OUT)
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
    i_pin = machine.Pin(pin, mode=machine.Pin.OUT)
    minute = time.localtime()[4]
    print('pin: {}, {} ({} / {}))'.format(pin, minute, on_mins, off_mins))
    if minute < on_mins:
        print('....turning on inter pin {}'.format(pin))
        i_pin.on()
        return True
    else:
        print('....turning off inter pin {}'.format(pin))
        i_pin.off()
        return False

def set_neopixel(watts, r=1, g=1, b=1):
    n_pixels = 8
    amps_per_pixel = 0.06
    amps = n_pixels * amps_per_pixel
    voltage = 5
    max_watts = voltage * amps
    
    pct = watts / max_watts
    output = [r, g, b]
    output = [c * (255 * pct) for c in output]
    output = [int(round(c, 0)) for c in output]
    output = tuple(output)
    print("Setting Lights to {} at {}%".format(output, round(pct*100,1)))
    
    pin = machine.Pin(
        config.OUTPUT_PIN_DICT['neopixel'],
        machine.Pin.OUT)
    np = neopixel.NeoPixel(pin, n_pixels)
    for i in range(0, n_pixels):
        np[i] = output
    np.write()
    pin.off()

def cycle_relays(reading, control, status):
    for relay, values in control['relay'].items():
        dict_key = "{}_status".format(relay)
        pin = config.RELAY_PIN_DICT[relay]
        status[dict_key] = _cycle_relay(
                pin=pin,
                reading=reading[relay],
                status=status[dict_key],
                **values)
    return status
        
def cycle_intermittents(reading, control, status):
    for inter, values in control['inter'].items():
        dict_key = "{}_status".format(inter)
        pin = config.RELAY_PIN_DICT[inter]
        status[dict_key] = _cycle_intermittent(
                                pin=pin,
                                **values)
    return status

def initialize_status(control):
    status = {}
    status.update({"{}_status".format(r): False for r in control['relay']})
    status.update({"{}_status".format(i): False for i in control['inter']})
    return status

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

def run():
    helper.turn_off_pins()
    helper.connect_wifi()
    id = helper.get_device_id()
    settime()

    status = None

    while True:

        try:
            print('')
            print('starting loop')
            led = machine.Pin(config.PIN_DICT['LED2'], machine.Pin.OUT)
            led.off()

            minute = time.localtime()[4]
            if minute % 60 == 0:
                print('fetching time')
                settime()
                print('....current time: {}'.format(time.localtime()))

            print('fetching control')
            control_response = connection.get_data(config.CONTROL_URL)
            control = parse_control_api(control_response)
            print(control)
            if status is None:
                status = initialize_status(control)

            reading = {}
            reading.update(get_temperature_and_humidity())
            # reading.update(get_moisture())

            relay_status = cycle_relays(reading, control, status)
            inter_status = cycle_intermittents(reading, control, status)
            status.update(relay_status)
            status.update(inter_status)

            if inter_status['lights_status']:
                set_neopixel(1, 0.025, 0, 1)

            #TODO: move to seperate table
            reading.update(status)
            reading.update({'device_id': id})
            print(reading)
            connection.post_data(reading, url=config.SENSOR_URL)
            print('done.')
            led.on()

        except Exception as exc:
            sys.print_exception(exc)
            helper.show_error()

        print('sleeping for {} seconds'.format(config.INTERVAL))
        time.sleep(config.INTERVAL)

run()
