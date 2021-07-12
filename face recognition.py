#from pprint import pprint
import json
import cv2
import face_recognition
import sys,os
import time
import numpy as np
#from PIL import Image
#from io import BytesIO
from simple_salesforce import Salesforce, SalesforceLogin, SFType
import pickle

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

loginInfo = json.load(open(resource_path('login.json')))
username = loginInfo['username']
password = loginInfo['password']
security_token = loginInfo['security_token']
camera_index = loginInfo['camera']
domain = 'login'

session_id, instance = SalesforceLogin(username=username, password=password, security_token=security_token, domain=domain)
sf = Salesforce(instance=instance, session_id=session_id)

known_face_encodings = []
known_face_names = []
nameVSid = {}
aidVStid = {}

file = open(resource_path("knownFacesEncodings.npy"),"rb")
known_face_encodings = np.load(file)

with open (resource_path('knownFacesNames.txt'), 'rb') as fp:
    known_face_names = pickle.load(fp)

with open (resource_path('nameVSid.txt'), 'rb') as fp:
    nameVSid = pickle.load(fp)

with open (resource_path('aidVStid.txt'), 'rb') as fp:
    aidVStid = pickle.load(fp)

print('known_face_encodings::',known_face_encodings)
print('known_face_names::',known_face_names)
print('nameVSid::',nameVSid)
print('aidVStid::',aidVStid)

#video_capture = cv2.VideoCapture(int(camera_index))
video_capture = cv2.VideoCapture(0)
face_locations = []
face_encodings = []
face_names = []
process_this_frame = True
namelist = []
update_data = {}
while True:
    # Grab a single frame of video
    ret, frame = video_capture.read()

    # Resize frame of video to 1/4 size for faster face recognition processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
    rgb_small_frame = small_frame[:, :, ::-1]

    # Only process every other frame of video to save time
    if process_this_frame:
        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            # # If a match was found in known_face_encodings, just use the first one.
            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]
                print('result is :::',name)
                if(name in nameVSid.keys()):
                    update_data.clear()
                    update_data['Omo__FaceRecognized__c'] = True
                    accId = nameVSid[name]
                    print('accountId::',accId)
                    print('transId::',aidVStid[accId])
                    getattr(sf, "Omo__Transaction__c").update(aidVStid[accId],update_data)
                    #time.sleep(2)
                    #selfcheckin.update(aidVStid[accId], update_data)
                #os._exit(0)

            # Or instead, use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]

            face_names.append(name)

    process_this_frame = not process_this_frame


    # Display the results
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    # Display the resulting image
    cv2.imshow('Video', frame)

    # Hit 'q' on the keyboard to quit!
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release handle to the webcam
video_capture.release()
cv2.destroyAllWindows()