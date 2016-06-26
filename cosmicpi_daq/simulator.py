# -*- coding: utf-8 -*-
#
# This file is part of CosmicPi-DAQ.
# Copyright (C) 2016 CosmicPi.
#
# CosmicPi-DAQ is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# CosmicPi-DAQ is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CosmicPi-DAQ; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Simulate a CosmicPi USB device."""

import json
import random
import time

from .logging import logger


class USBSimulator:
    def __init__(self):
        logger.warn('Using simulation mode!')
        self.is_open = False
        self.event_number = 0

    def open(self):
        self.is_open = True

    def close(self):
        pass

    def enable(self):
        pass

    def disable(self):
        pass

    def write(self, data):
        pass

    def readline(self):
        """Return a line of JSON that looks like it came from the Arduino
         firmware.

        This function is currently brain-dead. It just returns a cosmic event
        with random ADC counts inside.
        """
        time.sleep(1)

        if random.choice([True, False]):
            return self.update_location()
        else:
            return self.generate_event()

    @staticmethod
    def update_location():
        lat = random.uniform(46.2110000, 46.2110999)
        lon = random.uniform(6.1145000, 6.1145999)
        alt = random.randrange(400, 410)
        return json.dumps({'location': {'latitude': lat, 'altitude': alt,
                                        'longitude': lon}})

    def generate_event(self):
        self.event_number += 1
        timestamp = time.time()
        adc = [[random.randint(0, 4096) for _ in range(8)],
               [random.randint(0, 4096) for _ in range(8)]]
        return json.dumps({'event': {'event_number': self.event_number,
                                     'timer_frequency': 0, 'ticks': 0,
                                     'timestamp': timestamp, 'adc': adc}})
