"""
    Get inverter pv values via modbus

    2018-12-28 Tommi2Day
    2020-09-22 Tommi2Day fixes empty data exeptions
    2021-01-02 sellth added support for multiple inverters

    Configuration:
    pip3 install pymodbus

    [FEATURE-pvdata]

    # How frequently to send updates over (defaults to 20 sec)
    min_update=20
    #debug output
    debug=0

    #inverter connection
    inv_host = <inverter ip>
    inv_port = 502
    inv_modbus_id = 3
    inv_manufacturer = SMA
    #['address', 'type', 'format', 'description', 'unit', 'value']
    registers = [
        ['30057', 'U32', 'RAW', 'serial', ''],
        ['30201','U32','ENUM','Status',''],
        ['30051','U32','ENUM','DeviceClass',''],
        ['30053','U32','ENUM','DeviceID',''],
        ['40631', 'STR32', 'UTF8', 'Device Name', ''],
        ['30775', 'S32', 'FIX0', 'AC Power', 'W'],
        ['30813', 'S32', 'FIX0', 'AC apparent power', 'VA'],
        ['30977', 'S32', 'FIX3', 'AC current', 'A'],
        ['30783', 'S32', 'FIX2', 'AC voltage', 'V'],
        ['30803', 'U32', 'FIX2', 'grid frequency', 'Hz'],
        ['30773', 'S32', 'FIX0', 'DC power', 'W'],
        ['30771', 'S32', 'FIX2', 'DC input voltage', 'V'],
        ['30777', 'S32', 'FIX0', 'Power L1', 'W'],
        ['30779', 'S32', 'FIX0', 'Power L2', 'W'],
        ['30781', 'S32', 'FIX0', 'Power L3', 'W'],
        ['30953', 'S32', 'FIX1', u'device temperature', u'\xb0C'],
        ['30517', 'U64', 'FIX3', 'daily yield', 'kWh'],
        ['30513', 'U64', 'FIX3', 'total yield', 'kWh'],
        ['30521', 'U64', 'FIX0', 'operation time', 's'],
        ['30525', 'U64', 'FIX0', 'feed-in time', 's'],
        ['30975', 'S32', 'FIX2', 'intermediate voltage', 'V'],
        ['30225', 'S32', 'FIX0', 'Isolation resistance', u'\u03a9'],
        ['30581', 'U32', 'FIX0', u'energy from grid', 'Wh'],
        ['30583', 'U32', 'FIX0', u'energy to grid', 'Wh'],
        ['30865', 'S32', 'FIX0', 'Power from grid', 'W'],
        ['30867', 'S32', 'FIX0', 'Power to grid', 'W']
    ]
"""

import time
from features.smamodbus import get_device_class
from features.smamodbus import get_device_id
from features.smamodbus import get_pv_data
from libs.Sun import Sun

pv_last_update = 0
pv_debug = 0
pv_data = []

inv_status = {}

def run(emparts, config):
    global pv_debug
    global pv_last_update
    global pv_data

    pv_debug = int(config.get('debug', 0))

    if (pv_debug > 1):
        print("pv: data run")

    # Only update every X seconds
    if time.time() < pv_last_update + int(config.get('min_update', 20)):
        if (pv_debug > 1):
            print("pv: data skipping")
        return


    pv_last_update = time.time()

    # check if it is already dark
    # in that case we don't need to query inverter
    sun = Sun()

    # Default: Mittelpunkt Deutschlands
    lat = float(config.get('latitude','51.163361'))
    long = float(config.get('longitude','10.447683'))
    coords = {
        'latitude' : lat,
        'longitude' : long
         }
    
    isDark = sun.isDark(coords)

    if (pv_debug > 1):
        print(f"isDark: {isDark}")

    registers = eval(config.get('registers'))

    pv_data = []
    for inv in eval(config.get('inverters')):
        host, port, modbusid, manufacturer = inv

        # if it is dark we only need to check for batterycharge.
        # If battery is empty we only need to check again after sunrise
        if isDark:

            status = None
            for k, v in inv_status.items():
              if k == f"{host}:{port}:{modbusid}":
                status = v
                break

            if (not status is None and (not status['hasBattery'] or status['BatteryCharge'] <= 0)):
                #create new status
                new_status = {}
                for k, v in status.items():
                    match k:
                        case 'Status':
                            new_status[k] = 'Off'
                        case 'BatteryState':
                            new_status[k] = 'NA'
                        case ('AC Power' |
                            'AC_Power_Apparent' |
                            'AC_Current' |
                            'AC_Voltage_L1' |
                            'AC_Voltage_L2' |
                            'AC_Voltage_L3' |
                            'AC_Power_L1' |
                            'AC_Power_L2' |
                            'AC_Power_L3' |
                            'Grid_Frequency' |
                            'DC_Input1_Power' |
                            'DC_Input1_Voltage' |
                            'DC_Input1_Current' |
                            'DC_Input2_Power' |
                            'DC_Input2_Voltage' |
                            'DC_Input2_Current' |
                            'Device_Temperature' |
                            'Intermediate_Circuit_Voltage' |
                            'BatteryAmp' |
                            'BatteryVolt' |
                            'BatteryChargingVolt' |
                            'BatteryTemp' |
                            'AC apparent power' |
                            'Power L1' |
                            'Power L2' |
                            'Power L3'):
                            new_status[k] = 0
                        case _:
                            new_status[k] = v

                if (pv_debug > 1):
                    print(f"using nulled previous state: {new_status}")
                inv_status[f"{host}:{port}:{modbusid}"] = new_status
                pv_data.append(new_status)
                continue

        if (pv_debug > 1):
            print("starting device request")

        mdata = None
        hasBattery = False

        device_id = get_device_id(host, int(port))
        if device_id is None:
            if (pv_debug > 0):
                print("Error getting device_id")
            continue

        device_class = get_device_class(host, int(port), int(modbusid))
        if device_class is None:
            if (pv_debug > 0):
                print("Error getting device_class")
            continue

        if device_class == "Solar Inverter" or device_class == 'Hybrid Inverter':
            relevant_registers = eval(config.get('registers'))
            if device_class == 'Hybrid Inverter' or device_id['susyid'] == 292:
                hasBattery = True
                hybrid_registers = eval(config.get('registers_hybrid'))
                relevant_registers.extend(hybrid_registers)
            mdata = get_pv_data(host, int(port), int(modbusid), relevant_registers)
            pv_data.append(mdata)
        elif device_class == "Battery Inverter":
            hasBattery = True
            relevant_registers = eval(config.get('registers_batt'))
            mdata = get_pv_data(host, int(port), int(modbusid), relevant_registers)
            pv_data.append(mdata)
        else:
            if (pv_debug > 1):
                print("pv: unknown device class; skipping")
            pass

        if not mdata is None:
            inv_status[f"{host}:{port}:{modbusid}"] = mdata
            inv_status[f"{host}:{port}:{modbusid}"]['hasBattery'] = hasBattery

    # query
    if pv_data is None:
        if pv_debug > 0:
            print("PV: no data")
        return

    timestamp = time.time()
    for i in pv_data:
        i['timestamp'] = timestamp
        if pv_debug > 0:
            print("PV:" + format(i))


def stopping(emparts, config):
    pass


def on_publish(client, userdata, result):
    pass


def config(config):
    global pv_debug
    pv_debug = int(config.get('debug', 0))
    print('pvdata: feature enabled')
