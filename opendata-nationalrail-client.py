#
# National Rail Open Data client demonstrator
# Copyright (C)2019 OpenTrainTimes Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import stomp
import zlib
import io
import time
import socket
import xml.etree.ElementTree as ET
import config
import mongo_handler
from pymongo import MongoClient



try:
    import PPv16
except ModuleNotFoundError:
    print("Please configure the client following steps in README.md!")
    
USERNAME = config.DARWIN_USERNAME
PASSWORD = config.DARWIN_PASSWORD    
HOSTNAME = 'darwin-dist-44ae45.nationalrail.co.uk'
HOSTPORT = 61613
# Always prefixed by /topic/ (it's not a queue, it's a topic)
TOPIC = '/topic/darwin.pushport-v16'

CLIENT_ID = socket.getfqdn()
HEARTBEAT_INTERVAL_MS = 15000
RECONNECT_DELAY_SECS = 15

if USERNAME == '':
    raise Exception("Please configure your username and password in opendata-nationalrail-client.py!")





def connect_and_subscribe(connection):

    if stomp.__version__[0] < 5:
        connection.start()

    connect_header = {'client-id': USERNAME + '-' + CLIENT_ID}
    subscribe_header = {'activemq.subscriptionName': CLIENT_ID}

    connection.connect(username=USERNAME,
                       passcode=PASSWORD,
                       wait=True,
                       headers=connect_header)

    connection.subscribe(destination=TOPIC,
                         id='1',
                         ack='auto',
                         headers=subscribe_header)


class StompClient(stomp.ConnectionListener):

    def on_heartbeat(self):
        print('Received a heartbeat')

    def on_heartbeat_timeout(self):
        print('ERROR: Heartbeat timeout')

    def on_error(self, headers, message):
        print('ERROR: %s' % message)

    def on_disconnected(self):
        print('Disconnected waiting %s seconds before exiting' % RECONNECT_DELAY_SECS)
        time.sleep(RECONNECT_DELAY_SECS)
        exit(-1)

    def on_connecting(self, host_and_port):
        print('Connecting to ' + host_and_port[0])






    def on_message(self, headers, message):
        try:
            #print('\n----\nGot a message!')

            msg = zlib.decompress(message, zlib.MAX_WBITS | 32)
            #print('\n\t* Decompressed message: %s' % msg)

            #obj = PPv16.CreateFromDocument(msg)

            #print('\n\t* Received a Push Port message from %s' % obj.ts)

            tree = ET.fromstring(msg)
            # let's use as an example New Mills Central tpl="NWMILSC"

            stationTPL = 'LVRPLSH'
            
            for child in tree:
                for info in child:
                    if info.tag.endswith('TS'): # handle TS message
                    
                        for ts_info in info:

                            if ts_info.tag.endswith('Location') and ts_info.attrib['tpl'] == stationTPL:
                                train = {}
                                train['tpl'] = stationTPL
                                train['rid'] = info.attrib['rid']
                                #print('---------------------')
                                if ts_info.tag.endswith('LateReason'):
                                    train['late_reason_code'] = ts_info.text
                                for ts_specific in ts_info:
                                    if ts_specific.tag.endswith('arr'): # Handle arrivals
                                        try:
                                            train['pta'] = ts_info.attrib['pta']
                                            train['et'] = ts_specific.attrib['et']
                                            train['new_pta'] = ts_specific.attrib['et']
                                        except:
                                            pass # skip error when train is departuring and there is no arrival field
                                    if ts_specific.tag.endswith('dep'): # Handle departures
                                        try:
                                            train['ptd'] = ts_info.attrib['ptd']
                                            train['et'] = ts_specific.attrib['et']
                                            train['new_ptd'] = ts_specific.attrib['et']
                                        except:
                                            pass # skip error when train is arriving and there is no departure field
                                    if ts_specific.tag.endswith('pass'):
                                        print("Passing", ts_specific.attrib)
                                    if ts_specific.tag.endswith('plat'):
                                        try:
                                            train['platform'] = ts_specific.text
                                        except Exception:
                                            pass # skip platform error when there is no platform info
                                if 'new_pta' in train:
                                    mongo_handler.handle_arrival_update(train)
                                if 'new_ptd' in train:
                                    mongo_handler.handle_departure_update(train)
                                
                                break
            
        except Exception as e:
            print("\n\tError: %s\n--------\n" % str(e))


conn = stomp.Connection12([(HOSTNAME, HOSTPORT)],
                          auto_decode=False,
                          heartbeats=(HEARTBEAT_INTERVAL_MS, HEARTBEAT_INTERVAL_MS))

conn.set_listener('', StompClient())
connect_and_subscribe(conn)

while True:
    time.sleep(1)

conn.disconnect()
