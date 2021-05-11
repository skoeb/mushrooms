WIFI_SSID = 'speed_of_light'
WIFI_PASSWORD = '299792458'

INTERVAL = 15 * 1

HOST = '192.168.0.176'
SENSOR_URL = 'http://{}:5000/api/sensor_readings'.format(HOST)
CONTROL_URL = 'http://{}:5000/api/control'.format(HOST)
AUTH_TOKEN = 'sam'

PIN_DICT = {
    'TX':1, #O, boot fails if pulled low
    'RX':3, #I, high at boot
    'D0':16,
    'D1':5, #I/O
    'D2':4, #I/O 
    'D3':0, #O, boot fails if pulled low
    'D4':2, #O, boot fails if pulled low
    'D5':14, #I/O
    'D6':12, #I/O
    'D7':13, #I/O
    'D8':15, #O, boot fails if pulled high
    'SD2':9,
    'SD3':10,
    'LED1':2, #SHARED WITH D4
    'LED2':16, #SHARED WITH D0
    'AO':17
}

DEBUG_PIN = 'SD2'

RELAY_PIN_DICT = {
    'humidity': PIN_DICT['D5'],
    'co2eq': PIN_DICT['D6'],  # fan
    'temperature': PIN_DICT['D7'],
    'lights': PIN_DICT['D8'],
}

INPUT_PIN_DICT = {
    'dht11': PIN_DICT['D2'],
    'sgp30_scl': PIN_DICT['D1'],
    'sgp30_sda': PIN_DICT['D2']
}

OUTPUT_PIN_DICT = {
    'neopixel': PIN_DICT['D2'] 
}
