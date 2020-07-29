import logging,time,threading
Devices = []
class Module:
    def find(self,id=None,typ=None,Name=None):
        for m in self.Modules:
            if  ((id is None) or (m._id==id) or (id in m._id))\
            and ((typ is None) or (isinstance(m,typ)))\
            and ((Name is None) or ((m.Name is not None) and ((m.Name == Name) or (Name in m.Name)))):
                return m
            else:
                a = m.find(id,typ,Name)
                if a!=None:
                    return a
        return None
    def __init__(self, id, parent=None):
        self._id = id
        self.Modules = []
        self.Device = None
        self.Name =None
        self.Found = True
        if parent == None:
            parent = Devices
        if parent:
            parent.Modules.append(self)
        self.logger = logging.getLogger(type(self).__name__)
    def __str__(self):
        if self.Name is not None:
            ret = self.Name+' ('+str(self._id)+')'
        else:
            ret = str(self._id)
        return  ret
class Sensor(Module):
    def __str__(self):
        return Module.__str__(self)
class Actor(Module):
    def __str__(self):
        return Module.__str__(self)
class Interface(Sensor):
    def __init__(self, id, parent=None):
        Sensor.__init__(self,id,parent)
        self.Lock = threading.Lock()
    def __str__(self):
        return Module.__str__(self)
    def read(self,timeout=100):
        return None
    def write(self,prot):
        return False
class Video(Sensor):
    def __str__(self):
        return Module.__str__(self)
    def read(self):
        return None
class Camera(Video):pass
class Grabber(Video):pass
class ADC(Sensor):
    def Sample(self,Time):
        return False
class DAC(Actor):
    def Output(self,Samples):
        return False
class AudioADC(ADC):
    def SetInputVolume(self,Volume,channel = None):
        return False
    def SampleToWav(self,Filename,Time,SampleFormat='cd',Blocking=False):
        return False
    def StopSampling(self):
        return False
class AudioDAC(DAC):
    def SetOutputVolume(self,Volume,channel = None):
        return False
    def OutputFromWav(self,Filename):
        return False
class AnalogAudioIO(AudioDAC,AudioADC): pass
class VoltageSensor(ADC):
    def __init__(self, id,measurements=1, parent=None):
        self.measurements=measurements
        ADC.__init__(self,id,parent)
        self.Calibration = 0.0
    def Voltage(self):
        return -1
    def Sample(self):
        return self.Voltage()
    def __str__(self):
        ret = Sensor.__str__(self)+' Voltage:'+str(self.Voltage())+' V'
        return  ret
class CurrentSensor(Sensor):
    def __init__(self, id, parent=None,measurements=1):
        Sensor.__init__(self,id,parent)
        self.measurements=measurements
        self.Calibration = 0.0
    def Current(self):
        return -1
    def __str__(self):
        ret = Sensor.__str__(self)+' Current:'+str(self.Current())+' mA'
        return  ret
class ColorSensor(Sensor):
    def Color(self):
        return 0,0,0,-1 #RGBA
    def __str__(self):
        r,g,b,a = self.Color()
        ret = str(self._id)+' Color:'+str(r)+','+str(g)+','+str(b)+','+str(a)+','+' RGBA'
        return  ret
class MotorActor(Actor):
    def __init__(self, id, parent=None):
        Actor.__init__(self,id,parent)
    def Rotate(self,Grad,Direction): pass
class StepperMotorActor(MotorActor):
    def __init__(self, id, parent=None):
        Actor.__init__(self,id,parent)
    def Step(self,Steps,Direction): pass
class ServoActor(MotorActor):
    def __init__(self, id, parent=None):
        MotorActor.__init__(self,id,parent)
        self.ServoBasePosition = {}
        self.Names = {}
    def setName(self,port,Name):
        self.Names[Name] = port
    def getServo(self,port):
        if isinstance(port, str): 
            pin = self.Names[port]
        else:
            pin = port
        return pin
    def Power(self,servo,BasePosition=None,Velocity=65535,Period=14248,on=True):
        servo = self.getServo(servo)
        if BasePosition:
            self.ServoBasePosition[servo] = BasePosition
        return False
    def Position(self,Servo,Position,Relative=True):
        return False
    def ActualPosition(self,servo,Relative=True):
        return None
    def OutputVoltage(self,val):
        return False
    def DisableAll(self,Relative=False):
        for servo in self.Names:
            if abs(self.ActualPosition(servo,Relative))>100:
                self.Power(servo,on=True)
                self.Position(servo,0,Relative)
        There = False
        for servo in self.Names:
            while not There:
                There = True
                for servo in self.Names:
                    if abs(self.ActualPosition(servo,Relative))>100:
                        #print(servo,self.ActualPosition(servo,Relative))
                        There = False
                time.sleep(0.1)
        for servo in self.Names:
            self.Power(servo,on=False)
    def EnableAll(self,Relative=True):
        for servo in self.Names:
            if abs(self.ActualPosition(servo,Relative))>100:
                self.Power(servo,on=True)
                self.Position(servo,0,Relative)
        There = False
        for servo in self.Names:
            while not There:
                There = True
                for servo in self.Names:
                    if abs(self.ActualPosition(servo,Relative))>100:
                        #print(servo,self.ActualPosition(servo,Relative))
                        There = False
                time.sleep(0.1)
class GPIOActor(Actor):
    def __init__(self, id, parent=None):
        Actor.__init__(self,id,parent)
        self.Names = {}
    def setName(self,port,Name):
        self.Names[Name] = port
    def getPin(self,port):
        if isinstance(port, str): 
            pin = self.Names[port]
        else:
            pin = port
        return pin
    def setup(self,port,direction):
        if direction == 'in':
            pass
        if direction == 'out':
            pass
        if direction == 'tristate':
            pass
    def output(self,port,val):
        pass
    def input(self,port):
        return None
class Programmer(Module):
    """Generisches Programmiergert, holt DeviceSettings aus IC Bibliothek von plannedtests damit Unterklassen Controller Parameter Zentral zur Verfügung haben
    """
    def __init__(self, id, parent=None):
        Actor.__init__(self,id,parent)
        self.DeviceSettings = None
    def ConnectToCPU(self,Type,Speed):
        self.DeviceSettings = model.DeviceSettings(Type)
        if self.DeviceSettings is None:
            self.LastError = 'Unknown MCU/CPU'
        return False
    def Enable(self): return False
    def Disable(self): return False
    def LoadFile(self,Filename): pass
    def PatchSerial(self,Serial,Typ,Adress): pass
class ControllableProgrammer(Programmer): 
    """ Programmiergeräte Klasse, die die Möglichkeit hat Controller zu steuern (Boundary Scan, OpenOCD Register/oder eigene Firmware)
    """
    def SetPin(self,Port,Pin,Status):
        return False
    def ReadPin(self,Port,Pin):
        return False
    def CallFunction(self,Function,Parameters):
        return False
class BusController(Module): pass
class IPBusController(BusController):
    def SwitchBusOn(Port,On): pass
class ABBusController(BusController): pass
Devices = Module('/')
def EnsureDevice(typ,name=None,WaitTime=0):
    WaitTime += 0.1
    FirstSearch = True
    while WaitTime>0:
        dev = Devices.find(name,typ)
        if dev is not None: break
        dev = Devices.find(None,typ,name)
        if dev is not None: break
        typname = str(typ)
        typname = typname.replace('\'','')
        typname = typname.replace('>','')
        while typname.find('.')>-1:
            typname = typname[typname.find('.')+1:]
        if FirstSearch == True:
            if name is None:
                logging.warning("**STEP 999 waiting for device "+typname)
            else:
                logging.warning("**STEP 999 waiting for device "+name)
            FirstSearch = False
        time.sleep(0.1)
        WaitTime-=0.1
    if dev == None:
        if name is None:
            if FirstSearch == False:
                logging.warning("**ERROR "+typname+" not found")
        else:
            if FirstSearch == False:
                logging.error("**ERROR "+name+" not found")
        return False
    if FirstSearch == False:
        logging.warning("**STEPEND OK")
    return True
def showTree():
    try: 
        import pptree
        pptree.print_tree(Devices,"Modules")
    except: pass