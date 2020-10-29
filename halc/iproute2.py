from . import hal
import threading
try:
    from pyroute2 import IW
    from pyroute2 import IPRoute
    ip = IPRoute()
    #to be able to scan for networks python executable must have cap_net_admin flag
    #sudo setcap cap_net_admin,cap_net_raw+ep /usr/bin/python3.8
    iw = IW()
except:pass
class IPRoute2Interface(hal.NetworkInterface):pass
class IPRoute2WifiInterface(hal.NetworkWifiInterface):pass
class Enumerate(threading.Thread): 
    def run(self):
        global ip,iw
        try:
            while threading.main_thread().isAlive():
                for dev in hal.Devices.Modules:
                    if isinstance(dev,hal.IPInterface):
                        dev.Found = False

        except: pass