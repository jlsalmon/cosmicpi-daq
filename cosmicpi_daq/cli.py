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

"""CosmicPi command line interface."""

import logging
import socket
import sys
import time

from blessings import Terminal
from cliff.app import App
from cliff.command import Command
from cliff.commandmanager import CommandManager

from .version import __version__


class SocketCommand(object):

    @staticmethod
    def send_and_receive(command):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        try:
            sock.connect("/tmp/cosmicpi.sock")
        except:
            print("Fatal: Couldn't connect, is the process running?")
            sys.exit(1)

        sock.send(command)
        response = sock.recv(1024)
        sock.close()
        return response


class UsbToggle(Command, SocketCommand):
    """Toggle the USB ebabled/disabled state."""

    def take_action(self, args):
        self.app.stdout.write(self.send_and_receive('u') + '\n')


class Arduino(Command, SocketCommand):
    """Send commands to the Arduino firmware."""

    def get_parser(self, prog_name):
        parser = super(Arduino, self).get_parser(prog_name)

        subparsers = parser.add_subparsers(
            dest='arduino_command',
            help='available arduino commands')

        subparsers.add_parser('HTUX', help='reset the HTH chip')
        subparsers.add_parser(
            'HTUD', help='HTU Temperature-Humidity display rate'
        ).add_argument(
            'value', type=int, help='display rate value to set')
        subparsers.add_parser(
            'BMPD', help='BMP Temperature-Altitude display rate'
        ).add_argument(
            'value', type=int, help='display rate value to set')
        subparsers.add_parser(
            'LOCD', help='Location latitude-longitude display rate'
        ).add_argument(
            'value', type=int, help='display rate value to set')
        subparsers.add_parser(
            'TIMD', help='Timing uptime-frequency-etm display rate'
        ).add_argument(
            'value', type=int, help='display rate value to set')
        subparsers.add_parser(
            'STSD', help='Status info display rate'
        ).add_argument(
            'value', type=int, help='display rate value to set')
        subparsers.add_parser(
            'EVQT', help='Event queue dump threshold'
        ).add_argument(
            'value', type=int, help='threshold value to set (1..32)')
        subparsers.add_parser(
            'ACLD', help='Accelerometer display rate'
        ).add_argument(
            'value', type=int, help='display rate value to set')
        subparsers.add_parser(
            'MAGD', help='Magnetometer display rate'
        ).add_argument(
            'value', type=int, help='display rate value to set')
        subparsers.add_parser(
            'ACLT', help='Accelerometer event trigger threshold'
        ).add_argument(
            'value', type=int, help='threshold value to set (0..127)')

        return parser

    def take_action(self, args):
        command = args.arduino_command + \
            (' ' + str(args.value) if hasattr(args, 'value') else '')
        self.app.stdout.write(
            self.send_and_receive(
                'arduino ' + command) + '\n')


class Status(Command, SocketCommand):
    """Show the current status of the detector."""

    def get_parser(self, prog_name):
        parser = super(Status, self).get_parser(prog_name)
        parser.add_argument('-m', '--monitor', action='store_true',
                            help='monitor the detector status continuously')
        return parser

    def take_action(self, args):
        if args.monitor:
            term = Terminal()

            while True:
                try:
                    status = self.get_status()
                    self.app.stdout.write(status)
                    self.app.stdout.write(term.move_y(
                        term.height - len(status.split('\n'))))
                    time.sleep(1)
                except KeyboardInterrupt:
                    self.app.stdout.write(term.move_y(term.height) + '\n')
                    return
        else:
            self.app.stdout.write(self.get_status() + '\n')

    def get_status(self):
        return self.send_and_receive('s')


class Cli(App):
    """Command Line Interface."""

    NAME = 'cosmicpi'
    log = logging.getLogger(__name__)

    def __init__(self):
        command = CommandManager('cosmicpi')
        super(Cli, self).__init__(
            description=__doc__,
            version=__version__,
            command_manager=command,
        )
        commands = {
            'status': Status,
            'usb_toggle': UsbToggle,
            'arduino': Arduino
        }
        for k, v in commands.iteritems():
            command.add_command(k, v)

    def initialize_app(self, argv):
        self.log.debug('initialize_app')

    def prepare_to_run_command(self, cmd):
        self.log.debug('prepare_to_run_command %s', cmd.__class__.__name__)

    def clean_up(self, cmd, result, err):
        self.log.debug('clean_up %s', cmd.__class__.__name__)
        if err:
            self.log.debug('got an error: %s', err)


def main(argv=sys.argv[1:]):
    cli = Cli()
    return cli.run(argv)
