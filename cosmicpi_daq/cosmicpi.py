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

"""Talk to the CosmicPi Arduino DUE accross the serial USB link.

This program has the following functions ...

1) Build event messages and send them to a server or local port

  Events are any combination of Vibration, Weather and CosmicRays Hence the
  Arduino can behave as a weather station, as a vibration/Siesmic monitor and
  as a cosmic ray detector.  There is a gyroscope available but I don't use it

2) Perform diagnostics and monitoring of the Arduino via commands

3) Log events to the log file

It is important to keep the Python dictionary objects synchronised with the
Arduino firmware otherwise this monitor will not understand the data being sent
to it.
"""

from __future__ import absolute_import, print_function

import argparse
import logging.config
import os
import sys
import time
import traceback
import threading

import click

from .command_handler import CommandHandler
from .config import arg, load_config, print_config
from .detector import Detector
from .logging import logger
from .event_publisher import EventPublisher
from .usb_handler import USBHandler
from .simulator import USBSimulator


@click.group()
@click.option('-c', '--config', type=click.File())
@click.option('--debug/--no-debug', default=False)
@click.pass_context
def cli(ctx, config, debug):
    """CosmicPi acquisition process."""
    # Merge the default config with the configuration file
    ctx.obj = {}
    if config:
        ctx.obj.update({
            key.upper(): value for key, value in load_config(config)
        })

    ctx.obj['DEBUG'] = debug

@cli.command()
@click.option('--command-socket', type=click.Path(),
              default='cosmicpi-daq.sock')
@click.pass_context
def status(ctx, command_socket):
    """Display the status of the CosmicPi detector."""
    if command_socket:
        # try to connect
        pass


@cli.command()
@click.option('--broker', help='AMQP broker URI',
              default='amqp://test:test@cosmicpi-alpha.gotdns.ch:8080')
@click.option('--publish/--no-publish', default=True)
@click.option('-u', '--usb', help='USB device name')
@click.option('--vibration/--no-vibration', default=True)
@click.option('--weather/--no-weather', default=True)
@click.option('--cosmics/--no-cosmics', default=True)
@click.option('--command-socket', type=click.Path(),
              default='cosmicpi-daq.sock')  # FIXME add PID as extension
@click.pass_context
def start(ctx, broker, publish, usb, vibration, weather, cosmics, command_socket):
    """Start the acquisition process."""
    debug = ctx.obj.get('DEBUG', False)
    events = set()
    if weather:
        events.add('temperature')
    if vibration:
        events.add('vibration')
    if cosmics:
        events.add('event')

    try:
        publisher = EventPublisher(broker)
    except Exception:
        logger.error('cosmicpi: could not connect to broker "{0}"'.format(
            broker
        ))
        click.exit(1)

    try:

        # FIXME: add explicit simulator option
        # If the USB device is not defined, we switch to simulation mode
        usb_handler = USBHandler(usb, 9600, 60) if usb else USBSimulator()
        usb_handler.open()

    except Exception:
        logger.error('cosmicpi: could not connect to USB "{0}"'.format(
            usb
        ))
        click.exit(1)

    detector = Detector(usb_handler, publisher, debug, events=events)
    handlers = (
        detector,
        CommandHandler(detector, usb_handler, command_socket),
    )
    try:
        threads = [threading.Thread(target=target) for target in handlers]
        for thread in threads:
            thread.daemon = True
            thread.start()

        while True:
            time.sleep(1)

    except Exception:
        logger.exception('cosmicpi: unexpected exception')
    finally:
        detector.stop()
        threads[0].join()
        # FIXME gracefully quit command handler
        # for index, thread in enumerate(threads):
        #     handlers[index].stop()
        #     thread.join()
        time.sleep(1)
        usb_handler.close()
        publisher.close()
