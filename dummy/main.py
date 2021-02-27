import machine
import neopixel
import time


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
    
    pin = machine.Pin(2)
    np = neopixel.NeoPixel(pin, n_pixels)
    for i in range(0, n_pixels):
        np[i] = output
    np.write()
