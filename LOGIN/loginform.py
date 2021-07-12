from tkinter import *
from simple_salesforce import Salesforce, SalesforceLogin, SFType, format_soql
import face_recognition
import pandas as pd
import numpy as np
import os,sys
import pickle

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

###login method for login and fetching images###
def loginAndFetch(uname,pwd,stoken,hotelIsMultiproperty):
    username = uname
    password = pwd
    security_token = stoken
    domain = 'login'

    session_id, instance = SalesforceLogin(username=username, password=password, security_token=security_token, domain=domain)
    sf = Salesforce(instance=instance, session_id=session_id)

    #################
    hotelIsMultiproperty=True
    hotelRecTypes = []
    currentUserHotel = ''
    accountList = []
    aidVStid = {}

    session_id, instance = SalesforceLogin(username=username, password=password, security_token=security_token, domain=domain)
    sf = Salesforce(instance=instance, session_id=session_id)

    # fetching currentUserHotel
    usern=[]
    usern.append(username)
    querySOQL_currentUser = """select id, Omo__Hotel__c  from user where username IN('{0}') LIMIT 1""".format("','".join(usern))
    response = sf.query(querySOQL_currentUser)
    lstRecords = response.get('records')
    nextRecordsUrl = response.get('nextRecordsUrl')
    #print('response::::',response)
    while not response.get('done'):
        response = sf.query_more(nextRecordsUrl, identifier_is_url=True)
        lstRecords.extend(response.get('records'))
        nextRecordsUrl = response.get('nextRecordsUrl')

    df_records = pd.DataFrame(lstRecords)
    for row in df_records.iterrows():
        currentUserHotel = row[1]['Omo__Hotel__c']
        break

    # fetching hotel and transaction_recType and systemdate
    if(hotelIsMultiproperty):
        querySOQL_hotel = """Select name,Omo__system_date__c,Omo__transaction_rectype__c from Omo__Hotel__c where Omo__Valid__c=True"""
    else:
        querySOQL_hotel = """Select name,Omo__system_date__c,Omo__transaction_rectype__c from Omo__Hotel__c"""

    response = sf.query(querySOQL_hotel)
    lstRecords = response.get('records')
    nextRecordsUrl = response.get('nextRecordsUrl')
    #print('response::::',response)
    while not response.get('done'):
        response = sf.query_more(nextRecordsUrl, identifier_is_url=True)
        lstRecords.extend(response.get('records'))
        nextRecordsUrl = response.get('nextRecordsUrl')

    df_records = pd.DataFrame(lstRecords)
    #print('::::',df_records)
    for row in df_records.iterrows():
        if(currentUserHotel == row[1]['Name']):
            sDate = row[1]['Omo__System_Date__c']
        if(row[1]['Omo__Transaction_Rectype__c'] != None):
            hotelRecTypes.append(row[1]['Omo__Transaction_Rectype__c'])

    #print('Cuurentuserhotel::',currentUserHotel)
    #print('sysDate::',sDate)
    #print('hotelRecTypes::',hotelRecTypes)

    # fetch account ids by querying on transaction to get todays checkin only


    response = sf.query(format_soql("SELECT Id,Omo__guest__c from Omo__Transaction__c where (Omo__Reservation_Type__c='Reservation' or Omo__Reservation_Type__c='Dayuse') AND Omo__Cancel__c =False AND Omo__status__c='Not Arrive' AND Omo__guest__r.Omo__id__c!=3 AND Omo__Arrival_Date__c = {:literal} AND recordtype.name IN {hotRecType}",sDate, hotRecType = hotelRecTypes))

    #print('transaction query response::',response)
    lstRecords = response.get('records')
    nextRecordsUrl = response.get('nextRecordsUrl')
    #print('response::::',response)
    while not response.get('done'):
        response = sf.query_more(nextRecordsUrl, identifier_is_url=True)
        lstRecords.extend(response.get('records'))
        nextRecordsUrl = response.get('nextRecordsUrl')

    df_records = pd.DataFrame(lstRecords)
    #print('::::',df_records)
    for row in df_records.iterrows():
        accountList.append(row[1]['Omo__Guest__c'])
        aidVStid[row[1]['Omo__Guest__c']] = row[1]['Id']

    print('accounList::::',accountList)
    if(len(aidVStid)>0):
        with open(resource_path('aidVStid.txt'), 'wb') as fp:
            pickle.dump(aidVStid, fp) 
    #################

    # query records method
    response = sf.query(format_soql("SELECT Id, Name, ParentId, Body From Attachment WHERE ParentId IN {accList}",accList=accountList))
    lstRecords = response.get('records')
    nextRecordsUrl = response.get('nextRecordsUrl')
    print('response::::',response)
    while not response.get('done'):
        response = sf.query_more(nextRecordsUrl, identifier_is_url=True)
        lstRecords.extend(response.get('records'))
        nextRecordsUrl = response.get('nextRecordsUrl')

    df_records = pd.DataFrame(lstRecords)
    """
    Download files
    """
    instance_name = sf.sf_instance
    folder_path = '.\Attachments Download'
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)
    known_face_encodings = []
    known_face_names = []
    nameVSid = {}
    for row in df_records.iterrows():
        record_id = row[1]['ParentId']
        file_name = row[1]['Name']
        attachment_url = row[1]['Body']
        if (('.jpg' in file_name or '.png' in file_name) and ('/' not in file_name and '\\' not in file_name and ':' not in file_name and '?' not in file_name and '<' not in file_name and '>' not in file_name and '*' not in file_name and '"' not in file_name and '|' not in file_name)):
            print(':::::',file_name)
            if not os.path.exists(os.path.join(folder_path, record_id)):
                os.mkdir(os.path.join(folder_path, record_id))       
                
            request = sf.session.get('https://{0}{1}'.format(instance_name, attachment_url), headers=sf.headers)
            
            with open(os.path.join(folder_path, record_id, file_name), 'wb') as f:
                f.write(request.content)
                #--------------------------

                my_photo = face_recognition.load_image_file(os.path.abspath(folder_path+"\\"+record_id+"\\"+file_name))
                my_face_encoding = face_recognition.face_encodings(my_photo)[0]

                known_face_encodings.append(my_face_encoding)
                file_new_name = file_name.replace('.jpg', '')
                file_new_name = file_new_name.replace('.png', '')
                print('file_new_name:::'+file_new_name)
                known_face_names.append(file_new_name)
                nameVSid[file_new_name] = record_id
                #--------------------------
                #f.close()
    if(len(known_face_encodings)>0):  
        file = open(resource_path("knownFacesEncodings.npy"),"wb")
        #for element in known_face_encodings:
        np.save(file,known_face_encodings)  
        file.close()

        with open(resource_path('knownFacesNames.txt'), 'wb') as fp:
            pickle.dump(known_face_names, fp)   
        
        with open(resource_path('nameVSid.txt'), 'wb') as fp:
            pickle.dump(nameVSid, fp)   

    print('known_face_encodings::',known_face_encodings)
    print('known_face_names::',known_face_names)
###login method ends###

###save_info method to fetch info from user for credentials###
def save_info():
    usernameVar = un_entry.get()
    passwordVar = p_entry.get()
    securityTokenVar = st_entry.get()
    cameraVar = cam.get()
    checkbxVar = ck.get()
    checkbxVar2 = mp.get()

    print(usernameVar)
    print(passwordVar)
    print(securityTokenVar)
    print(checkbxVar)
    print(checkbxVar2)

    file = open(resource_path("login.json"),"w")
    file.write("{ \"username\" : \""+usernameVar+"\", \"password\": \""+passwordVar+"\", \"security_token\" : \""+securityTokenVar+"\", \"camera\" : \""+cameraVar+"\" }")
    file.close()
    #cam.set("0")
    if checkbxVar == 1:
        loginAndFetch(usernameVar,passwordVar,securityTokenVar,checkbxVar2)

###save_info method ends###

options = [
    "0",
    "1",
    "2",
    "3",
    "4",
]

app = Tk()
app.geometry("500x500")
app.title("Login Information")
heading = Label(text="Salesforce Org Information", bg="lightblue", fg ="black", font="10", width="500", height="3")
heading.pack()

username = Label(text="Username :")
password = Label(text="Password :")
security_Token = Label(text="Security Token :")
camera = Label(text="Camera :")

username.place(x=100,y=120)
password.place(x=100,y=160)
security_Token.place(x=100,y=200)
camera.place(x=100,y=240)

uname = StringVar()
pas = StringVar()
secTok = StringVar()
cam = StringVar()
cam.set( "0" )
ck = IntVar()
mp = IntVar()

un_entry = Entry(textvariable=uname, width="30")
p_entry = Entry(textvariable=pas, show="*", width="30")
st_entry = Entry(textvariable=secTok, show="*", width="30")

drop = OptionMenu( app , cam , *options )
drop.pack()

checkbx = Checkbutton(app, text='Import images for todays checkin',variable=ck, onvalue=1, offvalue=0)
checkbx.pack()

checkbx2 = Checkbutton(app, text='Is this a Multiproperty?',variable=mp, onvalue=1, offvalue=0)
checkbx2.pack()

un_entry.place(x=230, y=120)
p_entry.place(x=230, y=160)
st_entry.place(x=230, y=200)
drop.place(x=230,y=240)
checkbx.place(x=100,y=280)
checkbx2.place(x=100,y=320)

button = Button(app, text="Submit", command=save_info,width="30", height="2", bg="lightblue")
button.place(x=150,y=360)

mainloop()