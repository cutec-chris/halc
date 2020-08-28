from . import hal
try: import cv2
except: print('cv2 must be installed to use this module !')
import atexit,time,json,threading,numpy as np,os,logging,pyudev,usb.core
class OpenCVCamera(hal.Camera):
    def __init__(self, port=-1, parent=None,Name=None,VID=0x05a3,PID=0x9520):
        if port == -1:
            hal.Sensor.__init__(self,'default',parent)
        else:
            hal.Sensor.__init__(self,str(port),parent)
        self.Port = port
        self.cap = None
        self.Params = None
        self.Name = Name
        self.VID=VID
        self.PID=PID
    def reset(self):
        if self.cap != None:
            self.cap.release()
            self.cap = None
        dev = usb.core.finddev(idVendor=self.VID, idProduct=self.PID)
        if dev:
            self.logger.debug("restting usb device...")
            dev.reset()
    def decodeParams(self):
        def json_numpy_obj_hook(dct):
            if isinstance(dct, dict) and '__ndarray__' in dct:
                data = base64.b64decode(dct['__ndarray__'])
                return np.frombuffer(data, dct['dtype']).reshape(dct['shape'])
            return dct
        def loads(*args, **kwargs):
            kwargs.setdefault('object_hook', json_numpy_obj_hook)    
            return json.loads(*args, **kwargs)
        return loads(self.Params)
    def capture(self,dev,CloseCapture = False):
        if self.cap == None:
            self.init_capture()
        for i in range(5): #read 5 images from linux v2l fifo to get an actual image
            ret, img = self.cap.read()
        if ret == False:
            ret, img = self.cap.read()
            self.logger.debug("capture failed, trying to recapture")
        if ret:
            self.h,  self.w = img.shape[:2]
            cv2.resize(img,(1024,768))
        else:
            self.logger.debug("capture failed, trying to re-initialize")
            self.cap.release()
            self.cap = None
            self.init_capture()
            ret, img = self.cap.read()
            self.h,  self.w = img.shape[:2]
            cv2.resize(img,(1024,768))
        if ret == False:
            self.logger.debug("capture failed !")
            return False
        else:
            if CloseCapture == True:
                self.cap.release()
        if self.logger.getEffectiveLevel() == logging.DEBUG:
            cv2.imwrite('__cap_.png', img)
        if self.Params is not None:
            Params = self.decodeParams()
            matrix = np.array(Params['matrix'])
            dist = np.array(Params['dist_coeff'])
            h,  w = img.shape[:2]
            newcameramtx, roi=cv2.getOptimalNewCameraMatrix(matrix,dist,(self.w,self.h),0,(w,h))
            img = cv2.undistort(img,newcameramtx, dist, None, matrix)
            self.logger.debug(roi)
            if self.logger.getEffectiveLevel() == logging.DEBUG:
                cv2.imwrite('__cap_undisort.png', img)
        return img
    def init_capture(self,cam = -1):
        if self.cap == None:
            self.logger.debug("no Capture there, creating an new")
            try:
                self.cap = cv2.VideoCapture(cam, cv2.CAP_V4L2)
            except:
                self.cap = None
            ret, img = self.cap.read()
        else:
            if not self.cap.isOpened():
                self.logger.debug("Cap is not opened, opening...")
                self.cap.open(cam)
            if not self.cap.isOpened():
                self.logger.debug("Cap is not opened, re-crating...")
                self.cap.release()
                self.cap = None
                self.cap = cv2.VideoCapture(cam, cv2.CAP_V4L2)
            ret, img = self.cap.read()
            if ret == False:
                self.logger.debug("Capturing failed, releasing...")
                self.reset()
    def unload(self):
        if self.cap != None:
            self.cap.release()
            self.cap = None
    def read(self,CloseCapture = False):
        return self.capture(self.Device,CloseCapture = CloseCapture)
class opencvEnumerate(threading.Thread): 
    def __init__(self): 
        threading.Thread.__init__(self) 
    def exists(self,path):
        try:
            os.stat(path)
        except OSError:
            return False
        return True
    def run(self):
        context = pyudev.Context()
        while threading.main_thread().isAlive():
            for dev in hal.Devices.Modules:
                if isinstance(dev,OpenCVCamera):
                    dev.Found = False
            for i in range(0,25):
                try:
                    dev = pyudev.Devices.from_device_file(context, '/dev/video'+str(i))
                    if dev is not None:
                        adev = hal.Devices.find('/dev/video'+str(i),hal.Video)
                        if adev == None:
                            if dev.get('ID_USB_DRIVER') == 'uvcvideo' and dev.get('ID_MODEL').lower()!='stk1160':
                                cap = cv2.VideoCapture('/dev/video'+str(i))
                                if cap is not None:
                                    ret = cap.open(i)
                                    if ret==True:
                                        cam = OpenCVCamera('/dev/video'+str(i),Name=dev.get('ID_MODEL'))
                                    else:
                                        break
                        else:
                            adev.Found = True
                except:
                    pass
            for dev in hal.Devices.Modules:
                if isinstance(dev,OpenCVCamera):
                    if dev.Found == False:
                        del(dev)
            time.sleep(7)
Cameras = []
@atexit.register
def unloadmodule():
    for dev in hal.Devices.Modules:
        if isinstance(dev,OpenCVCamera):
            del(dev)
def silent_error_handler(status, func_name, err_msg, file_name, line, userdata):
    pass
cv2.redirectError(silent_error_handler)
enumerate = opencvEnumerate() 
enumerate.start()