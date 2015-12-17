#bin/bash python
import numpy
import cv2
import serial
import time

cv2.namedWindow('', cv2.WINDOW_NORMAL)

class Region:

    def __init__(self, config_string):
        """
        takes a string, like "name x y radius"
        """
        name, x1, x2, y1, y2 = config_string.split()

        print "Importing Region: " + name
        self.name = name
        self.x = (int(x1), int(x2))
        self.y = (int(y1), int(y2))

    def detect(self, mask):
        """
        returns true if motion is detected
        in specific region of mask
        """
        return numpy.any(self.slice(mask))

    def slice(self, frame):
        return frame[self.y[0]:self.y[1],self.x[0]:self.x[1]]

def draw(frame, mask):
    for r in regions:
        frame[r.y[0]:r.y[1],r.x[0]:r.x[1]] = r.slice(mask)
        cv2.putText(frame, r.name, (r.x[0], r.y[1] - 5),cv2.FONT_HERSHEY_SIMPLEX, .4, 255)
    return frame

ser = serial.Serial('/dev/cu.usbmodem1411', 9600, timeout=0)

REWARD_READY = False

left_combo = 0
right_combo = 0
left_last_detected = 0
right_last_detected = 0

def l():
   global REWARD_READY
   if not REWARD_READY:
       return

   global left_last_detected
   global left_combo
   global right_combo

   left_last_detected = time.time()
   
   if (right_combo > 0):
      right_combo -= 1
   else:
      right_combo =0

   if(left_combo > 0):
      ser.write("feed_left %s\n"%str(left_combo + 1))
      
   else:
      ser.write("feed_left 2\n")

   REWARD_READY = False

def r():
   global REWARD_READY
   if not REWARD_READY:
       return

   global left_combo
   global right_combo
   global right_last_detected

   right_last_detected = time.time()

   if (left_combo > 0):
      left_combo -= 1
   else:
      left_combo = 0

   right_combo += 1

   if(right_combo > 0):
      ser.write("feed_right %s\n"%str(right_combo))
      
   else:
      ser.write("feed_right 1\n")

   REWARD_READY = False


def c():
    
    global REWARD_READY
    REWARD_READY = True



def tl():

    global left_combo
    global left_last_detected
 
    ser.write('\n')

    if left_last_detected == 0:
        return

    if(time.time() - left_last_detected > left_combo):
       left_combo += 1
       left_last_detected = 0

    print left_combo

def tr():

    global right_combo
    global right_last_detected
 
    ser.write('\n')

    if right_last_detected == 0:
        return

    if(time.time() - right_last_detected > right_combo):
       right_combo += 1
       right_last_detected = 0

    print right_combo

#callback functions
callback = {"left": l, "right": r,"center": c,"topleft": tl, "topright": tr}

#list of regions
regions = []

#serial port
#ser = serial.Serial('/dev/tty.usbserial', 9600)

if __name__ == "__main__":

    #get read config
    with open("config", 'r') as f:
        #make list of Region objects from config file
        regions = [Region(l) for l in f.readlines()]

    cap = cv2.VideoCapture(1)
    fgbg = cv2.BackgroundSubtractorMOG()

    #warm up the camera
    for i in xrange(60):
        ret, frame = cap.read()


    while(True):
        
	try:
		# Capture frame-by-frame
		ret, frame = cap.read()

		#greyscale version of image
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

		#bg subtract from blured greyscale
		fgmask = fgbg.apply(cv2.blur(gray, (20,20)))

		#check each region for movement
		for r in regions:
		    if r.detect(fgmask):

			#execute callback function
			callback[r.name]()

			#notify serial port
			#ser.write(r.name)
			#long poll, I.E. wait for response
			#ser.readline()

		#draw overlays
		draw(gray, fgmask)

		# Display the resulting frame
		cv2.imshow('', gray)
		if cv2.waitKey(1) & 0xFF == ord('q'):
		    break
        except:
            pass
    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()
