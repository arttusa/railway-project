National Rail Open Data Python Example
======================================

This repository contains an Python 3 example of how to use the Darwin v16
messages from the National Rail Open Data platform, located at the following URL:

* https://opendata.nationalrail.co.uk/

To use this service, you will need to sign up for a free account and subscribe
to the 'Darwin' feed.

Configuration
-------------

Edit `opendata-nationalrail-client.py` and set the `USERNAME`, `PASSWORD`,
`HOSTNAME` and `HOSTPORT` variables to the values shown in 'Username', 'Password', 
'Messaging host' and 'STOMP Port' on the 'My Feeds' page.

Leave `CLIENT_ID` set to socket.getfqdn() - this will use the hostname of your
client for the durable subscription.  You may need to change this to something
else if you want to fail over the subscription to a different client.  In this
case, you could use your username.

The `HEARTBEAT_INTERVAL_MS` is set by default to 15 seconds (15,000ms) - this
should be sufficient for almost every application.  Don't change it unless you
have a good reason to do so.

`RECONNECT_DELAY_SECS` will enforce a 15-second delay before exiting.  This will
let you run the client in a loop, such as through a shell script, and protect
against you accidentally degrading the service for everyone by reconnecting far
too frequently. 

Finally, install the required dependencies by running `pip install "stomp.py<5" pyxb`.
 
Generating classes
------------------

The messages are produced in XML format, and a good way to consume them is by
using generated classes with [PyXB](https://pypi.org/project/PyXB/). 

`pyxbgen --schema-root=ppv16 --module PPv16 rttiPPTSchema_v16.xsd`

Running the code
----------------

The `opendata-nationalrail-client.py` script will show the raw message body and
print the timestamp from the parsed XML through the classes generated by
[PyXB](https://pypi.org/project/PyXB/). 

Support
-------

For support and questions with using Darwin, please use the forum at the
following URL:
 
 * https://groups.google.com/group/openraildata-talk
