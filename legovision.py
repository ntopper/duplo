#/bin/bash python
import argparse
import numpy
import cv2
import serial
import time

def timestr():
    return time.strftime("%m_%d-%H-%M-%S")

# outfile names
now = timestr()
logfile = now + "-log.txt"
vidfile = now + ".avi"

def log(s):
    print s
    with open(logfile, 'a+') as f:
        f.write(timestr() + ": " + s + '\n')

parser = argparse.ArgumentParser()
parser.add_argument('-ll', dest="ll_side", default="left")
parser.add_argument('-ss_delay', dest="ss_delay", default=1)
parser.add_argument('-ll_delay', dest="ll_delay", default=1)
parser.add_argument('-ll_reward', dest="ll_reward", default=2)
parser.add_argument('-ss_reward', dest="ss_reward", default=1)
parser.add_argument('-port', dest="port", default="COM1")
parser.add_argument('-bleep_mode', dest="mode", default="0")

args = parser.parse_args()

ll_side = args.ll_side
if ll_side == "right":
    ss_side = "left"
else:
    ss_side = "right"

ss_delay = int(args.ss_delay)
ll_delay = int(args.ll_delay)
ll_reward = args.ll_reward
ss_reward = args.ss_reward

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
        return frame[self.y[0]:self.y[1], self.x[0]:self.x[1]]


def draw(frame, mask):

    # region overlays
    for r in regions:
        cv2.rectangle(frame,
                      (r.x[0], r.y[0]),
                      (r.x[1], r.y[1]),
                      (0, 255 * r.slice(mask).any(), 0),
                      3
                      )

        cv2.putText(frame,
                    r.name,
                    (r.x[0] + 10, r.y[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    .4,
                    (0, 255, 0)
                    )

    # data overlay
    cv2.putText(frame, "Total Completed Loops SS: %s" % (counter_ss), (5, 10),
                cv2.FONT_HERSHEY_SIMPLEX, .3, (0, 255, 0))
    cv2.putText(frame, "Total Completed Loops ll: %s" % (counter_ll), (5, 20),
                cv2.FONT_HERSHEY_SIMPLEX, .3, (0, 255, 0))
    cv2.putText(frame, "Total Pellets Dispensed: %s" % (pellet_count), (5, 30),
                cv2.FONT_HERSHEY_SIMPLEX, .3, (0, 255, 0))

    return frame

ser = serial.Serial(args.port, 9600, timeout=0)

REWARD_READY = False
ll_adder = 0

countdown_end = 0
countdown_pending = False

counter_ss = 0
counter_ll = 0
pellet_count = 0

ser.write("set_mode %s" % args.mode)

def ll():
    global REWARD_READY
    global countdown_pending
    global ll_adder
    global countdown_end

    if not REWARD_READY:
        return
    REWARD_READY = False
    countdown_pending = True
    log("LL triggered")
    delay = ll_delay + ll_adder

    command = "feed_%s %s %s\n" % (ll_side, str(delay), str(ll_reward))
    log("sending: %s" % (command))
    ser.write(command)

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

    log("SS triggered")

    command = "feed_%s %s %s\n" % (ss_side, str(ss_delay), str(ss_reward))
    log("sending: %s" % (command))
    ser.write(command)

    countdown_end = time.time() + ss_delay


def c():
    global REWARD_READY

    if not REWARD_READY:
        log("new run")
        log("next ll delay: %s seconds" % (str(ll_delay + ll_adder)))

    REWARD_READY = True


def ll_end():
    global ll_adder
    global countdown_pending
    global counter_ll
    global pellet_count

    REWARD_READY = False

    if not countdown_pending:
        return
    countdown_pending = False

    ser.write('\n')
    if time.time() > countdown_end:
        ll_adder += 1
        pellet_count += int(ll_reward)

        log("ll reward successfull")
        counter_ll += 1
        log("Completed Loops LL: %s" % (counter_ll))
        log("Pellets Dispensed: %s" % (pellet_count))
    else:
        log("ll reward interupted")
    log("next ll delay: %s seconds" % (str(ll_delay + ll_adder)))


def ss_end():
    global ll_adder
    global countdown_pending
    global counter_ss
    global pellet_count

    REWARD_READY = False

    if not countdown_pending:
        return
    countdown_pending = False

    ser.write('\n')
    if time.time() > countdown_end:

        #ll_delay + ll_adder is always > 1
        ll_adder = max(-(ll_delay - 1), ll_adder - 1)
        pellet_count += int(ss_reward)

        log("ss reward successfull")
        counter_ss += 1
        log("Completed Loops SS: %s" % (counter_ss))
        log("Pellets Dispensed: %s" % (pellet_count))
    else:
        log("ss reward interupted")
    log("next ll delay: %s seconds" % (str(ll_delay + ll_adder)))

# callback functions
callback = {ll_side: ll,
            ss_side: ss,
            "center": c,
            "top" + ll_side: ll_end,
            "top" + ss_side: ss_end
            }

# list of regions
regions = []

if __name__ == "__main__":

    # Define the codec and create VideoWriter object
    fourcc = -1

    # get read config
    with open("config", 'r') as f:
        # make list of Region objects from config file
        regions = [Region(l) for l in f.readlines()]

    cap = cv2.VideoCapture(0)
    fgbg = cv2.BackgroundSubtractorMOG2()

    # warm up the camera
    for i in xrange(60):
        ret, frame = cap.read()

    while(True):

        try:
            # Capture frame-by-frame
            ret, frame = cap.read()

            if not ret:
                break

            # greyscale version of image
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # bg subtract from blured greyscale
            fgmask = fgbg.apply(cv2.blur(gray, (20, 20)))

            # check each region for movement
            for r in regions:
                if r.detect(fgmask):

                    # execute callback function
                    callback[r.name]()

            # draw overlays
            draw(frame, fgmask)

            # save this frame
            out.write(frame)

            # Display the resulting frame
            cv2.imshow('', frame)

            # trial ends at 200 pellets dispensed
            if cv2.waitKey(30) & 0xFF == ord('q') or pellet_count >= 200:
                break

        except Exception, e:
            log(e)

    log("Total Completed Loops SS: %s" % (counter_ss))
    log("Total Completed Loops LL: %s" % (counter_ss))
    log("Total Pellets Dispensed: %s" % (pellet_count))

    # When everything done, release erthing
    cap.release()
    out.release()
    cv2.destroyAllWindows()
