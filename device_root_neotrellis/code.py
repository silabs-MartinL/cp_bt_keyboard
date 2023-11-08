# rpico_rgb_keypad_obs v1.0.1
#
# SPDX-FileCopyrightText: 2023 Martin Looker
#
# SPDX-License-Identifier: MIT
#
# DESCRIPTION
#
# This code provides a controller for OBS studio acting as a USB keyboard
#
# Keys are as follows:
#
# Green:
#   11 scene keys, only one scene can be active at a time
# Cyan, Blue:
#   2 general keys
# Red, Yellow, Magenta:
#   3 toggle keys different key combos are sent when toggling on or off, so map these to start/stop
#   hotkeys for start/stop streaming etc
#
# HARDWARE
#
# https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html
# https://shop.pimoroni.com/products/pico-rgb-keypad-base
#
# LIBRARIES
#
# adafruit:
#   https://circuitpython.org/board/raspberry_pi_pico/
#   https://github.com/adafruit/Adafruit_DotStar
#   https://github.com/adafruit/Adafruit_CircuitPython_HID
#
# pimoroni:
#   https://github.com/pimoroni/pmk-circuitpython
#
# SOFTWARE
#
# Inspired by:
#   https://github.com/pimoroni/pmk-circuitpython/blob/main/examples/obs-studio-toggle-and-mutex.py

# Standard imports
import time
import board
import math

# CircuitPython library imports
# import usb_hid
#from adafruit_hid.keyboard import Keyboard
#from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode
import colorsys

# CircuitPython library hardware imports
# from pmk import PMK, number_to_xy, hsv_to_rgb                     # For Keybow 2040 and Pico RGB Keypad Base
# from pmk.platform.keybow2040 import Keybow2040 as Hardware        # For Keybow 2040
# from pmk.platform.rgbkeypadbase import RGBKeypadBase as Hardware  # For Pico RGB Keypad Base
from adafruit_neotrellis.neotrellis import NeoTrellis               # For Adafuit NeoTrellis also requires adafruit_seesaw and adafruit_bus_device

# When true keycodes are sent
KC_LIVE = False

# LED Hues
HUE_SPLIT = (1.0/24.0)
hue = {
    "red"     : (HUE_SPLIT *  0.0),
    "rry"     : (HUE_SPLIT *  1.0),
    "ry"      : (HUE_SPLIT *  2.0),
    "ryy"     : (HUE_SPLIT *  3.0),
    "yellow"  : (HUE_SPLIT *  4.0),
    "yyg"     : (HUE_SPLIT *  5.0),
    "yg"      : (HUE_SPLIT *  6.0),
    "ygg"     : (HUE_SPLIT *  7.0),
    "green"   : (HUE_SPLIT *  8.0),
    "ggc"     : (HUE_SPLIT *  9.0),
    "gc"      : (HUE_SPLIT * 10.0),
    "gcc"     : (HUE_SPLIT * 11.0),
    "cyan"    : (HUE_SPLIT * 12.0),
    "ccb"     : (HUE_SPLIT * 13.0),
    "cb"      : (HUE_SPLIT * 14.0),
    "cbb"     : (HUE_SPLIT * 15.0),
    "blue"    : (HUE_SPLIT * 16.0),
    "bbm"     : (HUE_SPLIT * 17.0),
    "bm"      : (HUE_SPLIT * 18.0),
    "bmm"     : (HUE_SPLIT * 19.0),
    "magenta" : (HUE_SPLIT * 20.0),
    "mmr"     : (HUE_SPLIT * 21.0),
    "mr"      : (HUE_SPLIT * 22.0),
    "mrr"     : (HUE_SPLIT * 23.0),
}

# Hue:
#   Set this for the pad color.
#
# Group:
#   Set this to group pads together to operate like radio buttons (good for
#   scene selection). You can have many separate groups of keys as set by the
#   string set for the group
#
# Keycodes On:
#   These are the keyboard codes to be sent for normal, grouped and toggle on
#   pads.
#
# Keycodes Off:
#   These are the keyboard codes to be sent for toggle off pads, setting this
#   makes a toggle button, good for start/stop streaming
#
# Note:
#   Pads configured as toggles will be removed from any groups
#
config = [
    {"hue": hue["red"], "group": "scene", "keycodes_on": [Keycode.F13],                  "keycodes_off": None                        }, # 0
    {"hue": hue["rry"], "group": "scene", "keycodes_on": [Keycode.F14],                  "keycodes_off": None                        }, # 1
    {"hue": hue["ry"], "group": "scene", "keycodes_on": [Keycode.F15],                  "keycodes_off": None                        }, # 2
    {"hue": hue["yellow"], "group": "scene", "keycodes_on": [Keycode.F16],                  "keycodes_off": None                        }, # 3
    {"hue": hue["yyg"], "group": "scene", "keycodes_on": [Keycode.F17],                  "keycodes_off": None                        }, # 4
    {"hue": hue["yg"], "group": "scene", "keycodes_on": [Keycode.F18],                  "keycodes_off": None                        }, # 5
    {"hue": hue["green"], "group": "scene", "keycodes_on": [Keycode.F19],                  "keycodes_off": None                        }, # 6
    {"hue": hue["ggc"], "group": "scene", "keycodes_on": [Keycode.F20],                  "keycodes_off": None                        }, # 7
    {"hue": hue["cyan"], "group": "scene", "keycodes_on": [Keycode.F21],                  "keycodes_off": None                        }, # 8
    {"hue": hue["ccb"], "group": "scene", "keycodes_on": [Keycode.F22],                  "keycodes_off": None                        }, # 9
    {"hue": hue["cb"], "group": "scene", "keycodes_on": [Keycode.F23],                  "keycodes_off": None                        }, # A
    {"hue": hue["blue"], "group": "scene", "keycodes_on": [Keycode.F24],                  "keycodes_off": None                        }, # B
    {"hue": hue["bbm"]   , "group": None,    "keycodes_on": [Keycode.SHIFT,   Keycode.F13], "keycodes_off": [Keycode.SHIFT, Keycode.F13]}, # C
    {"hue": hue["bm"]   , "group": None,    "keycodes_on": [Keycode.SHIFT,   Keycode.F14], "keycodes_off": [Keycode.SHIFT, Keycode.F14]}, # D
    {"hue": hue["magenta"]  , "group": None,    "keycodes_on": [Keycode.CONTROL, Keycode.F13], "keycodes_off": [Keycode.ALT,   Keycode.F13]}, # E
    {"hue": hue["mmr"]    , "group": None   , "keycodes_on": [Keycode.CONTROL, Keycode.F14], "keycodes_off": [Keycode.ALT,   Keycode.F14]}  # F
]

#config = [
#    {"hue": hue["yg"]     , "group": "scene", "keycodes_on": [Keycode.F13],                  "keycodes_off": None                      }, # 0
#    {"hue": hue["yellow"] , "group": "scene", "keycodes_on": [Keycode.F14],                  "keycodes_off": None                      }, # 1
#    {"hue": hue["yg"]     , "group": "scene", "keycodes_on": [Keycode.F15],                  "keycodes_off": None                      }, # 2
#    {"hue": hue["red"]    , "group": None   , "keycodes_on": [Keycode.CONTROL, Keycode.F13], "keycodes_off": [Keycode.ALT, Keycode.F13]}, # 3
#    {"hue": hue["gc"]     , "group": "scene", "keycodes_on": [Keycode.F16],                  "keycodes_off": None                      }, # 4
#    {"hue": hue["green"]  , "group": "scene", "keycodes_on": [Keycode.F17],                  "keycodes_off": None                      }, # 5
#    {"hue": hue["gc"]     , "group": "scene", "keycodes_on": [Keycode.F18],                  "keycodes_off": None                      }, # 6
#    {"hue": hue["rry"]    , "group": None   , "keycodes_on": [Keycode.CONTROL, Keycode.F14], "keycodes_off": [Keycode.ALT, Keycode.F14]}, # 7
#    {"hue": hue["cb"]     , "group": "scene", "keycodes_on": [Keycode.F19],                  "keycodes_off": None                      }, # 8
#    {"hue": hue["cyan"]   , "group": "scene", "keycodes_on": [Keycode.F20],                  "keycodes_off": None                      }, # 9
#    {"hue": hue["cb"]     , "group": "scene", "keycodes_on": [Keycode.F21],                  "keycodes_off": None                      }, # A
#    {"hue": hue["ry"]     , "group": None,    "keycodes_on": [Keycode.SHIFT, Keycode.F13]  , "keycodes_off": None                      }, # B
#    {"hue": hue["bm"]     , "group": "scene", "keycodes_on": [Keycode.F22],                  "keycodes_off": None                      }, # C
#    {"hue": hue["blue"]   , "group": "scene", "keycodes_on": [Keycode.F23],                  "keycodes_off": None                      }, # D
#    {"hue": hue["bm"]     , "group": "scene", "keycodes_on": [Keycode.F24],                  "keycodes_off": None                      }, # E
#    {"hue": hue["ryy"]    , "group": None   , "keycodes_on": [Keycode.CONTROL, Keycode.F16], "keycodes_off": [Keycode.ALT, Keycode.F16]}  # F
#]

# LED Values (brightness)
VAL_SPLIT = (1.0/32.0)
VAL_MIN   = (VAL_SPLIT *  0.0)
VAL_OFF   = (VAL_SPLIT *  2.0)
VAL_ON    = (VAL_SPLIT * 30.0)
VAL_MAX   = (VAL_SPLIT * 32.0)
VAL_STEP  = 0.02

# Set up the keyboard and layout
#keyboard = Keyboard(usb_hid.devices)
#layout = KeyboardLayoutUS(keyboard)

# Set up Keybow 2040 and Pico RGB Keypad Base hardware 
# keybow = PMK(Hardware())
# keys = keybow.keys

# Set up NeoTrellis
i2c_bus = board.I2C() 
trellis = NeoTrellis(i2c_bus)
trellis.brightness = 1.0

# Add runtime data to config
for i in range(16):
    # Defaults
    # Mode is toggle
    config[i]["mode"] = None
    # Set LED value to max
    config[i]["val"] = VAL_MAX
    # Not down
    config[i]["down"] = False
    # Not on
    config[i]["on"] = False
    # This is a toggle pad ?
    if config[i]["keycodes_off"] != None and len(config[i]["keycodes_off"]) and len(config[i]["keycodes_on"]):
        # Mode is toggle
        config[i]["mode"] = "toggle"
        # Can't be in a group
        config[i]["group"] = None
    # This is a grouped pad ?
    if config[i]["group"] != None and len(config[i]["keycodes_on"]):
        # Mode is group
        config[i]["mode"] = "group"
    # This is a key pad ?
    if config[i]["mode"] == None and len(config[i]["keycodes_on"]):
        # Mode is key
        config[i]["mode"] = "key"
    # This key has not got a mode ?
    if config[i]["mode"] == None:
        # Set LED value to min (not lit)
        config[i]["val"] = VAL_MIN

# HSV to RGB conversion from https://github.com/pimoroni/pmk-circuitpython/blob/main/lib/pmk/__init__.py
def hsv_to_rgb_float(h, s, v):
    # Convert an HSV (0.0-1.0) colour to RGB (0-255)
    if s == 0.0:
        rgb = [v, v, v]
    
    i = int(h * 6.0)

    f = (h*6.)-i; p,q,t = v*(1.-s), v*(1.-s*f), v*(1.-s*(1.-f)); i%=6
    
    if i == 0:
        rgb = [v, t, p]
    if i == 1:
        rgb = [q, v, p]
    if i == 2:
        rgb = [p, v, t]
    if i == 3:
        rgb = [p, q, v]
    if i == 4:
        rgb = [t, p, v]
    if i == 5:
        rgb = [v, p, q]

    rgb = tuple(int(c * 255) for c in rgb)

    return rgb

# HSV to RGB conversion from https://stackoverflow.com/questions/24152553/hsv-to-rgb-and-back-without-floating-point-math-in-python
def hsv_to_rgb_int(h, s, v):
    # Convert an H (0-359) SV (0-255) colour to RGB (0-255)
    print(f'hsv = {h} {s} {v}')
   # Check if the color is Grayscale
    if s == 0:
        r = v
        g = v
        b = v

    else:
        # Make hue 0-5
        region = h // 60;

        # Find remainder part, make it from 0-255
        remainder = h % 60; 

        # Intermediate values
        vs = v * s
        
        # Calculate temp vars, doing integer multiplication
        p = v - (vs // 255);
        q = v - (vs // (255 * remainder)) // 60
        t = v - (vs // (60 - remainder)) // 60

        # Assign temp vars based on color cone region
        if region == 0:
            r = v
            g = t
            b = p
        
        elif region == 1:
            r = q 
            g = v 
            b = p

        elif region == 2:
            r = p 
            g = v 
            b = t

        elif region == 3:
            r = p 
            g = q 
            b = v

        elif region == 4:
            r = t 
            g = p 
            b = v

        else: 
            r = v 
            g = p 
            b = q
        
    print(f'rgb = {r} {g} {b}')    
    rgb = tuple(r, g, b)
    
    return (r, g, b)

# Presses a list of keycodes
def press_kcs(kcs):
    print(f'keycode press {kcs} {KC_LIVE}')
    if KC_LIVE:
        if len(kcs) == 1:
            #keyboard.press(kcs[0])
            pass
        elif len(kcs) == 2:
            #keyboard.press(kcs[0], kcs[1])
            pass
        elif len(kcs) == 3:
            #keyboard.press(kcs[0], kcs[1], kcs[2])
            pass

# Releases a list of keycodes
def release_kcs(kcs):
    print(f'keycode release {kcs} {KC_LIVE}')
    if KC_LIVE:
        if len(kcs) == 1:
            #keyboard.release(kcs[0])
            pass
        elif len(kcs) == 2:
            #keyboard.release(kcs[0], kcs[1])
            pass
        elif len(kcs) == 3:
            #keyboard.release(kcs[0], kcs[1], kcs[2])
            pass

def press_handler(key_number):
    print(f'keypad press {key_number}')
    # Pad is now down
    config[key_number]["down"] = True
    # Normal pad ?
    if config[key_number]["mode"] == "key":
        # Press the on keycodes
        press_kcs(config[key_number]["keycodes_on"])
    # Toggle pad ?
    elif config[key_number]["mode"] == "toggle":
        # Toggle is currently on ?
        if config[key_number]["on"]:
            # Turn off
            config[key_number]["on"] = False
            # Press the off keycodes
            press_kcs(config[key_number]["keycodes_off"])
        # Toggle is currently off ?
        else:
            # Turn on
            config[key_number]["on"] = True
            # Press the on keycodes
            press_kcs(config[key_number]["keycodes_on"])
    # Grouped pad ?
    elif config[key_number]["mode"] == "group":
        # Turn on the pressed pad
        config[key_number]["on"] = True
        # Press the on keycodes
        press_kcs(config[key_number]["keycodes_on"])
        # Loop through pads
        for i in range(16):
            # Not the pad that has just been pressed ?
            if i != key_number:
                # This pad is in the same group as the pad that has just been pressed ?
                if config[i]["mode"] == "group" and config[i]["group"] == config[key_number]["group"]:
                    # The pad is on ?
                    if config[i]["on"]:
                        # Turn it off
                        config[i]["on"] = False
                        # Set val to minimum
                        config[i]["val"] = VAL_MIN

def release_handler(key_number):
    print(f'keypad release {key_number}')
    # Pad is not down
    config[key_number]["down"] = False
    # Normal pad ?
    if config[key_number]["mode"] == "key":
        # Release on keycodes
        release_kcs(config[key_number]["keycodes_on"])
    # Toggle pad ?
    elif config[key_number]["mode"] == "toggle":
        # Pad has been toggled on ?
        if config[key_number]["on"]:
            # Release on keycodes
            release_kcs(config[key_number]["keycodes_on"])
        # Pad has just been turned off ?
        else:
            # Release off keycodes
            release_kcs(config[key_number]["keycodes_off"])
    # Grouped pad
    elif config[key_number]["mode"] == "group":
        # Release on keycodes
        release_kcs(config[key_number]["keycodes_on"])

def key_handler(event):
    # Pressed when a rising edge is detected
    if event.edge == NeoTrellis.EDGE_RISING:
        press_handler(event.number)
    # Released when a falling edge is detected
    elif event.edge == NeoTrellis.EDGE_FALLING:
        release_handler(event.number)

# Trellis key configuration
for i in range(16):
    # activate rising edge events on all keys
    trellis.activate_key(i, NeoTrellis.EDGE_RISING)
    # activate falling edge events on all keys
    trellis.activate_key(i, NeoTrellis.EDGE_FALLING)
    # set all keys to trigger the blink callback
    trellis.callbacks[i] = key_handler
    
# Timing, the trellis can only be read every 17 milliseconds or so
TIME_TRELLIS = 0.02 
time_now = time.monotonic()
time_sync = time_now + TIME_TRELLIS

# Main loop
while True:
    # Note current time
    time_now = time.monotonic()
    print(f'{time_now}')
    # Time to sync trellis?
    if time_now >= time_sync:
        # Call the sync function to call any triggered callbacks
        trellis.sync()
        # Set time for next sync
        time_sync = time_now + TIME_TRELLIS
    # Loop through pads
    for i in range(16):
        # Start with LED off
        h = 0.0
        s = 0.0
        v = 0.0
        # No mode ?
        if config[i]["mode"] == None:
            # Turn off LED
            #keys[i].set_led(0, 0, 0)
            trellis.pixels[i] = (0, 0, 0)
        # Pad has a mode ?
        else:
            # Pad is down ?
            if config[i]["down"]:
                # Normal or grouped pad
                if config[i]["mode"] == "key" or config[i]["mode"] == "group":
                    # Go to full brightness
                    config[i]["val"] = v = VAL_MAX
                # Toggle pad?
                elif config[i]["mode"] == "toggle":
                    # Toggled on ?
                    if config[i]["on"]:
                        # Go to full brightness
                        config[i]["val"] = v = VAL_MAX
                    # Toggled off ?
                    else:
                        # Go to min brightness
                        config[i]["val"] = v = VAL_MIN
            # Pad is not down
            else:
                # Pad is on
                if config[i]["on"]:
                    # Set target on brightness
                    v = VAL_ON
                # Pad is off ?
                else:
                    # Set target off brightness
                    v = VAL_OFF
            # Target value above current value ?
            if v > config[i]["val"]:
                # Move towards target
                if v - config[i]["val"] > VAL_STEP:
                    config[i]["val"] += VAL_STEP
                else:
                    config[i]["val"] = v
            # Target value below current value
            elif v < config[i]["val"]:
                # Move towards target
                if config[i]["val"] - v > VAL_STEP:
                    config[i]["val"] -= VAL_STEP
                else:
                    config[i]["val"] = v
            # Pad has a hue ?
            if config[i]["hue"] is not None:
                # Set full saturation
                s = 1.0
                # Set hue
                h = config[i]["hue"]
            # Convert the hue to RGB values.
            #r, g, b = hsv_to_rgb(h, s, config[i]["val"])
 #           if i == 0:
 #                print(f'{h} {s} {config[i]["val"]} {r} {g} {b} rgb')
            # Finally set the LED
            #trellis.pixels[i] = hsv_to_rgb_float(h, s, config[i]["val"])
            #trellis.pixels[i] = hsv_to_rgb_int(int(359*h), int(255*s), int(255*config[i]["val"]))
            trellis.pixels[i] = colorsys.hsv_to_rgb(h, s, config[i]["val"])
