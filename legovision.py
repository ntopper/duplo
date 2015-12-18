#/bin/bash python
import argparse
import numpy
import cv2
import serial
import time

parser = argparse.ArgumentParser()
parser.add_argument('-ll', dest="ll_side", default="left")
parser.add_argument('-delay', dest="base_delay", default=1)
parser.add_argument('-reward', dest="base_reward", default=2)

args = parser.parse_args()

ll_side = args.ll_side
if ll_side == "right": ss_side = "left"
else: ss_side = "right"

base_delay = args.base_delay
base_reward = args.base_reward

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
        cv2.rectangle(frame,
                (r.x[0],r.y[0]),
                (r.x[1],r.y[1]),
                (0, 255 * r.slice(mask).any(),0),
                3
        )

        cv2.putText(frame,
                r.name,
                (r.x[0] + 10, r.y[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                .4,
                (0,255,0)
        )

    return frame

ser = serial.Serial('/dev/ttyACM0', 9600, timeout=0)

REWARD_READY = False
ll_adder = 0

countdown_end = 0
countdown_pending = False
def ll():
        global REWARD_READY
        global countdown_pending
        global ll_adder
        global countdown_end

        if not REWARD_READY:
                return
        REWARD_READY = False
        countdown_pending = True
        print "LL triggered"
        delay = base_delay + ll_adder
        ser.write("feed_%s "%(ll) + str(delay))

        countdown_end = time.time() + delay

def ss():
        global REWARD_READY
        global countdown_pending
        global ll_adder
        global countdown_end

        if not REWARD_READY:
                return

        REWARD_READY = False
        countdown_pending = True

        print "SS triggered"
        ll_adder = max(0, ll_adder - 1)
        ser.write("feed_%s "%(ss) + str(base_delay))
        countdown_end = time.time() + base_delay

def c():
        global REWARD_READY

        if not REWARD_READY:
                print "new run"
                print "next ll delay: %s seconds"%(str(base_delay + ll_adder))

        REWARD_READY = True

def ll_end():
        global ll_adder
        global countdown_pending

        if not countdown_pending:
            return
        countdown_pending = False

        ser.write('\n')
        if time.time() > countdown_end:
                ll_adder += 1
                print "ll reward successfull"
        else:
            print "ll reward interupted"
        print "next ll delay: %s seconds"%(str(base_delay + ll_adder))

def ss_end():

        global ll_adder
        global countdown_pending

        if not countdown_pending:
                return
        countdown_pending = False

        ser.write('\n')
        if time.time() > countdown_end:
                ll_adder = max(0, ll_adder - 1)
                print "ss reward successfull"
        else:
            print "ss reward interupted"
        print "next ll delay: %s seconds"%(str(base_delay + ll_adder))

#callback functions
callback = {ll_side: ll,
        ss_side: ss,
        "center": c,
        "top"+ll_side: ll_end,
        "top"+ss_side: ss_end
        }

#list of regions
regions = []

if __name__ == "__main__":

    #get read config
    with open("config", 'r') as f:
        #make list of Region objects from config file
        regions = [Region(l) for l in f.readlines()]

    cap = cv2.VideoCapture(0)
    fgbg = cv2.BackgroundSubtractorMOG()

    #warm up the camera
    for i in xrange(60):
        ret, frame = cap.read()

    while(True):

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

            #draw overlays
            draw(frame, fgmask)

            # Display the resulting frame
            cv2.imshow('', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()
