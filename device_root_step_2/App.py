"""
*****************************************************************************
Copyright 2023 Silicon Laboratories Inc. www.silabs.com
*****************************************************************************
SPDX-License-Identifier: Zlib

The licensor of this software is Silicon Laboratories Inc.

This software is provided \'as-is\', without any express or implied
warranty. In no event will the authors be held liable for any damages
arising from the use of this software.

Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it
freely, subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not
   claim that you wrote the original software. If you use this software
   in a product, an acknowledgment in the product documentation would be
   appreciated but is not required.
2. Altered source versions must be plainly marked as such, and must not be
   misrepresented as being the original software.
3. This notice may not be removed or altered from any source distribution.

*****************************************************************************
# EXPERIMENTAL QUALITY
This code has not been formally tested and is provided as-is. It is not
suitable for production environments. In addition, this code will not be
maintained and there may be no bug maintenance planned for these resources.
Silicon Labs may update projects from time to time.
******************************************************************************
"""
# Standard Imports
import time
import board
# Library Imports
from adafruit_neotrellis.neotrellis import NeoTrellis

# Constants
TIME_SYNC = 0.02 # NeoTrellis sync, buttons can only be read every 17ms, allow a bit longer

# Application class
class App():

    # Initialisation
    def __init__(self) -> None:
        # Open I2C
        self.i2c = board.I2C()
        # Create NeoTrellis class
        self.trellis = NeoTrellis(self.i2c)
        # Set the brightness value (0 to 1.0)
        self.trellis.brightness = 0.5
        # Set all keys to blue and activate events
        for i in range(16):
            # Set LED to blue
            self.trellis.pixels[i] = (0, 0, 255)
            # Activate rising edge events on all keys
            self.trellis.activate_key(i, NeoTrellis.EDGE_RISING)
            # Activate falling edge events on all keys
            self.trellis.activate_key(i, NeoTrellis.EDGE_FALLING)
            # Set all keys to trigger the blink callback
            self.trellis.callbacks[i] = self.key
            # Briefly sleep
            time.sleep(0.05)
        # Turn off all keys
        for i in range(16):
            # Set LED to off
            self.trellis.pixels[i] = (0, 0, 15)
            # Briefly sleep
            time.sleep(0.05) 
        # Note current time
        now = time.monotonic()
        # Set sync time (20ms)
        self.time_sync = now + TIME_SYNC

    # Key event handler
    def key(self, event):
        # turn the LED on when a rising edge is detected
        if event.edge == NeoTrellis.EDGE_RISING:
            self.trellis.pixels[event.number] = (0, 0, 255)
        # turn the LED off when a falling edge is detected
        elif event.edge == NeoTrellis.EDGE_FALLING:
            self.trellis.pixels[event.number] = (0, 0, 15) 

    # Main function - called repeatedly do not block
    def main(self):
        # Note current time
        now = time.monotonic()
        # Time to sync trellis?
        if now >= self.time_sync:
            # Call the sync function to call any triggered callbacks
            self.trellis.sync()
            # Set time for next sync
            self.time_sync = now + TIME_SYNC

# Application class END