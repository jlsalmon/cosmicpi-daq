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

"""Test CLI execution."""

import os
import signal
import subprocess
import sys
import time


def test_run():
    cmd = 'cosmicpi start'
    app = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                           preexec_fn=os.setsid, shell=True)
    time.sleep(5)

    cmd = 'cosmicpi status'
    output = subprocess.check_output(cmd, shell=True)
    assert 'OK' in str(output)

    os.killpg(app.pid, signal.SIGTERM)
