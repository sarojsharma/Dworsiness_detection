from scipy.spatial import distance as dist  #to compute euclidean distance
from imutils.video import VideoStream
from imutils import face_utlis
from threading import Thread  #we can play our alarm in a separate thread from the main thread to ensure our script doesn’t pause execution while the alarm sounds.
import numpy as np
import playsound
import argparse
import imutils
import time
import dlib
import cv2


def alarm(path):
    playsound.playsound(path)
    

def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])

    C = dist.euclidean(eye[0], eye[3])

    EAR = (A + B) / (2.0 * C)

    return EAR


#construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--shape-predictor", required=True, help="path to facial landmark predictor")
ap.add_argument("-a", "--alarm", type=str, default="", help="path alarm .WAV file")
ap.add_argument("-w", "--webcam", type=int, default=0, help="index of webcame on system")
args = vars(ap.parse_args())

EYE_THRESH = 0.3
EYE_CONSEC_FRAMES = 48

COUNTER = 0
ALARM_ON = False

print("[INFO] loading facial landmark prdictor...")
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(args["shape_predictor"])

(lstart,lend) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rstart,rend) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

print("[INFO] starting video stream thread...")
vs = VideoStream(src=args["webcam"]).start()
time.sleep(1.0)

while True:
    frame = vs.read()
    frame = imutils.resize(frame, width=450)
    gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    rects = detector(gray, 0)

    for rect in rects:
        shape = predictor(gray,rect)
        shape = face_utils.shape_to_np(shape)

        lefteye = shape[lstart:lend]
        righteye = shape[rstart:rend]
        leftEAR = eye_aspect_ratio(lefteye)
        rightEAR = eye_aspect_ratio(righteye)

        ear = (leftEAR + rightEAR) / 2.0

        lefteyehull = cv2.convexHull(lefteye)
        righteyehull = cv2.convexHull(righteye)
        cv2.drawContours(frame, [lefteyehull], -1, (0, 255, 0), 1)
        cv2.drawContours(frame, [righteyehull], -1, (0, 255, 0), 1)

        if ear < EYE_THRESH:
            COUNTER += 1

            if COUNTER >= EYE_CONSEC_FRAMES:

                if not ALARM_ON:
                    ALARM_ON =True

                    if args["alarm"] != "":
                        t = Thread(target=sound_alarm,args=(args["alarm"],))
                        t.deamon = True
                        t.start()

                cv2.putText(frame, "DROWSINESS ALERT!",(10, 30),cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                

        else:
            COUNTER = 0
            ALARM_ON = FALSE

        cv2.putText(frame, "EAR: {:.2F}".format(ear), (300, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("FRAME", frame)
    key = cv2.waitkey(1) & 0xFF

    if key == ord("q"):
        break

cv2.destroyAllWindows()
vs.stop()

