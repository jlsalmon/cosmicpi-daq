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

"""Data acquisition package for reading data from CosmicPi."""

import logging
import os
import socket
import threading

log = logging.getLogger(__name__)


class CommandHandler(object):
    """Command handler."""

    def __init__(self, detector, usb, options):
        self.detector = detector
        self.usb = usb
        self.options = options
        self.thread = threading.Thread(target=self.run, args=(), kwargs={})
        self.thread.daemon = True

    def start(self):
        """Start new thread."""
        self.thread.start()

    def run(self):
        """Listen on socket and interpret commands."""
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        try:
            os.remove("/tmp/cosmicpi.sock")
        except OSError:
            pass

        sock.bind("/tmp/cosmicpi.sock")
        sock.listen(1)
        log.info("Listening for commands on local socket")

        while True:
            conn, addr = sock.accept()

            cmd = conn.recv(1024)
            if not cmd:
                break

            log.info("Received command: %s" % cmd)

            try:
                if cmd == 'd':
                    if self.options.debug:
                        self.options.debug = False
                    else:
                        self.options.debug = True
                    response = "Debug:%s\n" % self.options.debug

                elif cmd == 'v':
                    if self.options.monitoring['vibration']:
                        self.options.monitoring['vibration'] = False
                    else:
                        self.options.monitoring['vibration'] = True
                    response = "Vibration:%s\n" % self.options.monitoring[
                        'vibration']

                elif cmd == 'w':
                    if self.options.monitoring['weather']:
                        self.options.monitoring['weather'] = False
                    else:
                        self.options.monitoring['weather'] = True
                    response = "WeatherStation:%s\n" % self.options.monitoring[
                        'weather']
                elif cmd == 's':
                    tim = self.detector.sensors.timing
                    sts = self.detector.sensors.status
                    loc = self.detector.sensors.location
                    acl = self.detector.sensors.accelerometer
                    mag = self.detector.sensors.magnetometer
                    bmp = self.detector.sensors.barometer
                    htu = self.detector.sensors.temperature
                    vib = self.detector.sensors.vibration

                    response = (
                        "ARDUINO STATUS\n"
                        "Status........: uptime:%s counter_frequency:%s"
                        " queue_size:%s missed_events:%s\n"
                        "HardwareStatus: temp_status:%s baro_status:%s"
                        " accel_status:%s mag_status:%s gps_status:%s\n"
                        "Location......: latitude:%s longitude:%s"
                        " altitude:%s\n"
                        "Accelerometer.: x:%s y:%s z:%s\n"
                        "Magnetometer..: x:%s y:%s z:%s\n"
                        "Barometer.....: temperature:%s pressure:%s"
                        " altitude:%s\n"
                        "Humidity......: temperature:%s humidity:%s\n"
                        "Vibration.....: direction:%s count:%s\n"
                        "MONITOR STATUS\n"
                        "USB device....: %s\n"
                        "Remote........: Ip:%s Port:%s UdpFlag:%s\n"
                        "Vibration.....: Sent:%d Flag:%s\n"
                        "WeatherStation: Flag:%s\n"
                        "Events........: Sent:%d LogFlag:%s\n"
                    ) % (
                        tim["uptime"], tim["counter_frequency"],
                        sts["queue_size"], sts["missed_events"],
                        sts["temp_status"], sts["baro_status"],
                        sts["accel_status"], sts["mag_status"],
                        sts["gps_status"],
                        loc["latitude"], loc["longitude"], loc["altitude"],
                        acl["x"], acl["y"], acl["z"],
                        mag["x"], mag["y"], mag["z"],
                        bmp["temperature"], bmp["pressure"], bmp["altitude"],
                        htu["temperature"], htu["humidity"],
                        vib["direction"], vib["count"],
                        self.options.usb['device'],
                        self.options.broker['host'],
                        self.options.broker['port'],
                        self.options.broker['enabled'],
                        self.detector.vbrts,
                        self.options.monitoring['vibration'],
                        self.options.monitoring['weather'],
                        self.detector.events, self.options.logging['enabled'],
                    )
                elif cmd == 'u':
                    if self.usb.enabled:
                        self.usb.disable()
                    else:
                        self.usb.enable()
                    response = (
                        "USB: %s" %
                        ('enabled' if self.usb.enabled else 'disabled'))

                elif cmd == 'n':
                    if self.options.broker['enabled']:
                        self.options.broker['enabled'] = False
                    else:
                        self.options.broker['enabled'] = True
                    response = ("Send:%s\n" % self.options.broker['enabled'])

                elif cmd == 'l':
                    if self.options.logging['enabled']:
                        self.options.logging['enabled'] = False
                    else:
                        self.options.logging['enabled'] = True
                    response = ("Log:%s\n" % self.options.logging['enabled'])

                elif cmd.startswith('arduino'):
                    response = ("%s" % cmd)
                    self.usb.write(cmd.upper())

                else:
                    response = ''

                conn.send(response)

            except Exception as e:
                msg = "Error processing client command: %s" % e
                log.warn(msg)
                conn.send(msg)
