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

"""Detector model."""

from __future__ import absolute_import

import json
import threading

import netifaces

from .event import Event
from .logging import logger as log


class Sensors(object):

    def __init__(self):
        self.temperature = {"temperature": "0.0", "humidity": "0.0"}
        self.barometer = {
            "temperature": "0.0",
            "pressure": "0.0",
            "altitude": "0.0"}
        self.vibration = {"direction": "0", "count": "0"}
        self.magnetometer = {"x": "0.0", "y": "0.0", "z": "0.0"}
        self.accelerometer = {"x": "0.0", "y": "0.0", "z": "0.0"}
        self.location = {
            "latitude": "0.0",
            "longitude": "0.0",
            "altitude": "0.0"}
        self.timing = {
            "uptime": "0",
            "counter_frequency": "0",
            "time_string": "0"}
        self.status = {
            "queue_size": "0",
            "missed_events": "0",
            "buffer_error": "0",
            "temp_status": "0",
            "baro_status": "0",
            "accel_status": "0",
            "mag_status": "0",
            "gps_status": "0"}

    def update(self, line):
        line = line.replace('\n', '')
        line = line.replace('\'', '"')

        try:
            sensor = json.loads(line)
        except:
            return  # Didn't understand, throw it away

        self.__dict__.update(sensor)
        return sensor


class Detector(object):

    def __init__(self, usb_handler, publisher, debug, events=None):
        self.events = set(events or ('vibration', 'temperature', 'event'))
        self.usb_handler = usb_handler
        self.publisher = publisher
        self.debug = debug

        self.sensors = Sensors()

        self.detector_id = self.get_detector_id()

        self.stopping = False

    @property
    def event(self):
        """Return new Event instance with current data."""
        return Event(self.detector_id, self.sensors)

    def __call__(self):
        """Handle incoming events."""
        while not self.stopping:
            line = self.usb_handler.readline()
            self.publisher.connection.process_data_events()

            sensor = self.sensors.update(line)
            if not sensor:
                continue

            event = self.event
            log.info('Event: {0}'.format(event))

            # Check if we should handle the event.
            # if set(event.keys()) & self.events:
            self.handle_event(event)

            if self.debug:
                log.debug(sensor)

    def stop(self):
        log.info("Stopping detector thread")
        self.stopping = True

    def handle_event(self, event):
        data = event.to_json()
        if self.publisher:
            self.publisher.send_event_pkt(data)
        if self.debug:
            log.debug(data)

    def get_detector_id(self):
        """Retrieve the unique identifier of this detector.

        Currently the MAC address of the first known network interface is used.
        """
        known_interfaces = ['eth0', 'wlan0', 'en1']

        for interface in known_interfaces:
            if interface in netifaces.interfaces():
                return netifaces.ifaddresses(
                    interface)[netifaces.AF_LINK][0]['addr']

        raise Exception("No detector ID could be determined")
