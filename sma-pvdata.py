#!/usr/bin/env python3
# coding=utf-8
import importlib
import signal
import sys
import json
import time
import traceback

from configparser import ConfigParser

# clean exit
def abortprogram(signal,frame):
    # Housekeeping -> nothing to cleanup
    print('STRG + C = end program')
    sys.exit(0)

# abort-signal
signal.signal(signal.SIGINT, abortprogram)


#read configuration
parser = ConfigParser()
#default values
smaserials = ""
parser.read(['./smaemd/config','config'])
try:
    smaemserials=parser.get('SMA-EM', 'serials')
    ipbind=parser.get('DAEMON', 'ipbind')
    pvdata = importlib.import_module('features.pvdata')
    pvconfig = dict(parser.items('FEATURE-pvdata'))
except:
    print('Cannot find config /etc/smaemd/config... using defaults')

try:
    
    emparts = {}
    pvdata.run(emparts,pvconfig)

    from features.pvdata import pv_data


    print ("pv_data")
    if pv_data is not None:
        for inv in pv_data:
            pvserial = inv.get("serial")
            payload = json.dumps(inv)
            print("pvdata %s %s:%s" % (
                pvserial,
                format(time.strftime("%H:%M:%S",
                                      time.localtime(time.time()))),
                payload))

except Exception as e:
    print("sma-pvdata: Error publishing")
    print(traceback.format_exc())
    pass
