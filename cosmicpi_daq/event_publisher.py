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

"""Publish event via AMQP."""

import json

import pika


class EventPublisher(object):
    """Publish events."""

    def __init__(self, broker):
        """Create new connection and channel."""
        self.connection = pika.BlockingConnection(
            pika.URLParameters(broker)
        )
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='events', type='fanout')

    def send_event_pkt(self, pkt):
        """Publish an event."""
        properties = pika.BasicProperties(content_type='application/json')
        self.channel.basic_publish(
            exchange='events',
            routing_key='',
            body=json.dumps(pkt),
            properties=properties,
        )

    def close(self):
        """Close AMQP connection."""
        self.connection.close()
