from basic import *
import RPi.GPIO as GPIO
import subprocess
print "Welcome to the FingerPrint Admin Reader Programm"
print "Press 1 to insert a new fingerprint "
print "Press 2 to delete all fingerprints"
print "Press 3 to know how many fingerprints have been enrolled"
IV=raw_input("Press 4 to verify if the FingerPrint is saved in the DataBase")#Input Value

sendCommand('Open')
time.sleep(1)
IDtemp=GetEnrollCount()
time.sleep(0.2)
IDtemp=GetEnrollCount()
print (IDtemp)
temp=IDtemp[0]
temp=str(temp)
ID=int(temp)
IV=int(IV)

if ID == 20 and IV ==1 :
	print " you don't have enough space to add more "

if IV==1 and ID <= 19:
	print "please put your finger on the reader when you see the Blue LED"
	print " and remove it when the LED is off"
	print "P.S you have to do this THREE times , so please be patient"
	time.sleep(2)
	Enrollultimate(ID)
	subprocess.call('x=`date` ; ./notifications.sh -t "New Try for enrollment $x" > log2.txt;',shell=True)

elif IV == 2:
	DeleteAll()
	print "Deletion is Done Successfully"
	IDtemp=GetEnrollCount()
	temp=IDtemp[0]
	temp=str(temp)
	ID=int(temp)
	print "The number of ID has been reset to " ,ID
	subprocess.call('x=`date` ; ./notifications.sh -t "All IDs Have been deleted $x" > log2.txt;',shell=True)


elif IV==3:
	print " you have ",ID , " IDs have been rolled"
	subprocess.call('x=`date` ; ./notifications.sh -t "Ask for how many IDs at  $x" > log2.txt;',shell=True)

elif IV==4:
	print "please put your finger on the reader when you see the Blue LED"
	print " and remove it when the LED is off"
	time.sleep(4)
	IDtemp=verify()
	temp=IDtemp[0]
	temp=str(temp)
	ID=int(temp)
	print ID
	if  ID >= 0 and ID <=19 :
		print "This FingerPrint is Enrolled with ID ",ID
		subprocess.call('x=`date`; ./notifications.sh -t "The Safe Has been Opened  at $x" > log2.txt;')
	else:
		print "This FingerPrint is not Enrolled"
		subprocess.call('x=`date`; ./notifications.sh -t "unverified finger print has been tried at $x" > log2.txt;',shell=True)
	sendCommand('CmosLed')
