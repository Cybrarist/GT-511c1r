
import os 
import serial
import struct
import time


save= False
fingerprint=1;
timeout=1
comm_struct = lambda: '<BBHIH'
data_struct = lambda x: '<BBH' + str(x) + 's'
checksum_struct = lambda: '<H'
	
responses = {
    'Ack':  0x30,
    'Nack': 0x31,
    0x30:   'Ack',
    0x31:   'Nack'
}
errors = {
    0x1001: 'NACK_TIMEOUT',                 # (Obsolete) Capture timeout
    0x1002: 'NACK_INVALID_BAUDRATE',        # (Obsolete) Invalid serial baud rate
    0x1003: 'NACK_INVALID_POS',             # The specified ID is not in range[0,199]
    0x1004: 'NACK_IS_NOT_USED',             # The specified ID is not used
    0x1005: 'NACK_IS_ALREADY_USED',         # The specified ID is already in use
    0x1006: 'NACK_COMM_ERR',                # Communication error
    0x1007: 'NACK_VERIFY_FAILED',           # 1:1 Verification Failure
    0x1008: 'NACK_IDENTIFY_FAILED',         # 1:N Identification Failure
    0x1009: 'NACK_DB_IS_FULL',              # The database is full
    0x100A: 'NACK_DB_IS_EMPTY',             # The database is empty
    0x100B: 'NACK_TURN_ERR',                # (Obsolete) Invalid order of the enrollment
                                            #    (EnrollStart->Enroll1->Enroll2->Enroll3)
    0x100C: 'NACK_BAD_FINGER',              # Fingerprint is too bad
    0x100D: 'NACK_ENROLL_FAILED',           # Enrollment Failure
    0x100E: 'NACK_IS_NOT_SUPPORTED',        # The command is not supported
    0x100F: 'NACK_DEV_ERR',                 # Device error: probably Crypto-Chip is faulty (Wrong checksum ~Z)
    0x1010: 'NACK_CAPTURE_CANCELED',        # (Obsolete) Capturing was canceled
    0x1011: 'NACK_INVALID_PARAM',           # Invalid parameter
    0x1012: 'NACK_FINGER_IS_NOT_PRESSED',   # Finger is not pressed
}

ser=serial.Serial(
port = '/dev/ttyAMA0',
baudrate = 9600,
timeout=1,
parity=serial.PARITY_NONE,
stopbits=serial.STOPBITS_ONE,
bytesize=serial.EIGHTBITS
)

def getResponse(datauwant=False,ispressed=False):
	responsedata=bytearray(12)
	responsedata=ser.readline()
	return decode_command_packet(bytearray(responsedata),datauwant,ispressed)

packets = {
    'Command1':  0x55,
    'Command2':  0xAA,
    'Data1':     0x5A,
    'Data2':     0xA5,
    '\x55\xAA':  'C',
    '\x5A\xA5':  'D'
}

"""all the commands """
commands = {
    'Open':             0x01,   # Initialization
    'Close':            0x02,   # Termination
    'UsbInternalCheck': 0x03,   # Check if the connected USB device is valid
    'ChangeBaudrate':   0x04,   # Change UART baud rate
    'SetIAPMode':       0x05,   # Enter IAP Mode. In this mode, FW Upgrade is available
    'CmosLed':          0x12,   # Control CMOS LED
    'GetEnrollCount':   0x20,   # Get enrolled fingerprint count
    'CheckEnrolled':    0x21,   # Check whether the specified ID is already enrolled
    'EnrollStart':      0x22,   # Start an enrollment
    'Enroll1':          0x23,   # Make 1st template for an enrollment
    'Enroll2':          0x24,   # Make 2nd template for an enrollment
    'Enroll3':          0x25,   # Make 3rd template for an enrollment. 
                                #    Merge three templates into one template,
                                #    save merged template to the database 
    'IsPressFinger':    0x26,   # Check if a finger is placed on the sensor
    'DeleteID':         0x40,   # Delete the fingerprint with the specified ID
    'DeleteAll':        0x41,   # Delete all fingerprints from the database
    'Verify':           0x50,   # 1:1 Verification of the capture fingerprint image with the specified ID
    'Identify':         0x51,   # 1:N Identification of the capture fingerprint image with the database
    'VerifyTemplate':   0x52,   # 1:1 Verification of a fingerprint template with the specified ID
    'IdentifyTemplate': 0x53,   # 1:N Identification of a fingerprint template with the database
    'CaptureFinger':    0x60,   # Capture a fingerprint image(256x256) from the sensor
    'MakeTemplate':     0x61,   # Make template for transmission
    'GetImage':         0x62,   # Download the captured fingerprint image (256x256)
    'GetRawImage':      0x63,   # Capture & Download raw fingerprint image (32'\x240)
    'GetTemplate':      0x70,   # Download the template of the specified ID 
    'SetTemplate':      0x71,   # Upload the template of the specified ID
    'GetDatabaseStart': 0x72,   # Start database download, obsolete
    'GetDatabaseEnd':   0x73,   # End database download, obsolete
    'UpgradeFirmware':  0x80,   # Not supported
    'UpgradeISOCDImage':0x81,   # Not supported
    'Ack':              0x30,   # Acknowledge
    'Nack':             0x31    # Non-acknowledge
}

def encode_command_packet(
        command = None,
        parameter = 0,
        device_id = 1):
    
    command = commands[command]
    packet = bytearray(struct.pack(comm_struct(), 
        packets['Command1'],    # Start code 1
        packets['Command2'],    # Start code 2
        device_id,              # Device ID
        parameter,              # Parameter
        command                 # Command
    ))
    checksum = sum(packet)
    packet += bytearray(struct.pack(checksum_struct(), checksum))
    return packet


def encode_data_packet(
	data = None,
	data_len = 0,
	device_id = 1):
    
	packet = bytearray(struct.pack(data_struct(data_len), 
		packets['Data1'],    # Start code 1
		packets['Data2'],    # Start code 2
		device_id,           # Device ID
		data                 # Data to be sent
	))
	checksum = sum(packet)
	packet += bytearray(struct.pack(checksum_struct(), checksum))
	return packet
    
 
def sendCommand(command, parameter = 0x00):
	if type(parameter) == bool:
			parameter = parameter*1
	packet = encode_command_packet(command, parameter, device_id = 0x01)
	if (len(packet) == ser.write(packet)):
		return True
	else:
		return False

def decode_command_packet(packet,datauwant,ispressed):
	response = {
		'Header1': None,
		'Header2': None,
		'DeviceID': None,
		'ACK': None,
		'Parameter': None,
		'Checksum': None,
		'Response':None,
		'packet4':None,
		'packet5':None,
		'packet6':None,
		'packet7':None,
		'packet3':None
	}
	checksum=packet[-2:]    
	if packet == '': # Nothing to decode
		response['ACK'] = False
		return response
	
    # Check if it is a data packet:
	if packet[0] == packets['Data1'] and packet[1] == packets['Data2']:
		return decode_data_packet(packet)
    # Strip the checksum and get the values out
	if len(packet[-2:])<2:
		raise Exception("Received packet doesn't have a checksum! Check your connection!")
#calcualte the check sum and comapre it 
	response['Header1'] = packet[0] 
	response['Header2']= packet[1]
	response['DeviceID'] = packet[2]
	response['ACK'] =packet[4] != 0x31  # Not NACK, might be command
	response['packet3']=packet[3]
	response['packet4']=packet[4]
	response['packet5']=packet[5]
	response['packet6']=packet[6]
	response['packet7']=packet[7]
	response['packet8']=packet[8]
	 # response['Parameter'] = packet[3] if response['ACK'] else errors[packet[3]]
	response['Parameter'] = errors[packet[3]] if (not response['ACK'] and packet[3] in errors) else packet[3]
	temp1=str(response['packet4'])
	temp2=str(response['packet5'])
	temp3=int(temp1)
	temp4=int(temp2)
	if datauwant:	
		if temp3==8 and temp4==16:
			return -1
		elif ispressed:
			return response['packet4']+response['packet5']+response['packet6']+response['packet7']
		else:
			return response['packet4']
	else :
		return response



def decode_data_packet(packet):
	response = {
		'Header1': None,
		'Header2': None,
		'DeviceID': None,
		'ACK': None,
		'Parameter': None,
		'Checksum': None,
		'Response':None,
		'packet4':None,
		'packet5':None,
		'packet6':None,
		'packet7':None,
		'Data': None      
		}
	if packet == '':
		response['ACK'] = False
		return response
    # Check if it is a command packet:
	if packet[0] == packets['Command1'] and packet[1] == packets['Command2']:
		return decode_command_packet(packet)
    
    # Strip the checksum and get the values out
	if len(packet[-2:]) < 2:
		raise Exception("Received packet doesn't have a checksum! Check your connection!")
   # checksum = sum(struct.unpack(checksum_struct(), packet[-2:])) # Last two bytes are checksum
	packet = packet[:-2]
    # Data sum might be larger than the checksum field:
	chk = sum(packet)
	chk &= 0xffff
   # response['Checksum'] = chk == checksum # True if checksum is correct
    
	data_len = len(packet) - 4 # Exclude the header (2) and device ID (2)
		
	response['Header1'] = packet[0]
	response['Header2'] = packet[1]
	response['DeviceID'] = packet[2]
	response['Data'] = packet[3]
	# print packet
	return response
    

def GetEnrollCount():
        if sendCommand('GetEnrollCount'):
            return [getResponse(True), None]
        else:
            raise RuntimeError("Couldn't send packet")

def startenrolling(ID):
        if sendCommand('EnrollStart', ID):
            return [getResponse(), None]
        else:
            raise RuntimeError("Couldn't send packet")
            
def CaptureFinger( best_image = False):
        # For enrollment use 'best_image = True'
        # For identification use 'best_image = False'
        if best_image:
            ser.timeout = 10
        if sendCommand('CaptureFinger', best_image):
            ser.timeout = timeout
            return [getResponse(), None]
        else:
            raise RuntimeError("Couldn't send packet")
                 
def Enroll1():
        if sendCommand('Enroll1'):
            return [getResponse(), None]
        else:
            raise RuntimeError("Couldn't send packet")
  
  
def Enroll2():
        if sendCommand('Enroll2'):
            return [getResponse(), None]
        else:
            raise RuntimeError("Couldn't send packet")      


def Enroll3():
        if sendCommand('Enroll3'):
            response = getResponse()
        else:
            raise RuntimeError("Couldn't send packet")
        data = None
        if save:
            data = getData(498)
        return [response, data]
           
def getData(data_len):
        # Data length is different for every command
        response = ser.readline() # Header(2) + ID(2) + data + checksum(2)
        # return response
        return decode_data_packet(bytearray(response))      
 
# def GetImage( dim = (240, 216)):
        # # The documentation is ambiguous:
        # # Dimensions could be 202x258 or 256x256
        # to_read = dim[0]*dim[1]

        # if sendCommand('GetImage'):
            # response = getResponse()
        # else:
            # raise RuntimeError("Couldn't send packet")
        # data = None
        # if response['ACK']:
            # sertimeout = None # This is dangerous!
            # data = getData(dim[0]*dim[1])
            # ser.timeout = timeout
            # data['Data'] = (data['Data'], dim)
        # return [response, data]   
        
# def GetRawImage(dim = (160, 120)):
        # if sendCommand('GetRawImage'):
            # response = getResponse()
        # else:
            # raise RuntimeError("Couldn't send packet")
        # data = None
        # if response['ACK']:
            # ser.timeout = None # This is dangerous!
            # data = getData(dim[0]*dim[1])
            # ser.timeout = timeout
            # # Add dimensions to the data
            # data['Data'] = (data['Data'], dim)
        # return [response, data]


def Identify(datauwant=True):
        if sendCommand('Identify'):
            return [getResponse(datauwant), None]
        else:
            raise RuntimeError("Couldn't send packet")    

def DeleteAll():
        if sendCommand('DeleteAll'):
            return [getResponse(), None]
        else:
            raise RuntimeError("Couldn't send packet")  

def Enrollultimate(IDchange):
	checktemp=GetEnrollCount()
	checktemp1=checktemp[0]
	checktemp1=str(checktemp1)
	check=int(checktemp1)
	print ("check is ",check)
	startenrolling(IDchange)
	time.sleep(1)
	sendCommand('CmosLed',1)
	time.sleep(1)
	"""Is_pressed()
	while Is_pressed()!= 0:
		print("not pressed 1")"""
	CaptureFinger(True)
	time.sleep(1)
	Enroll1()
	time.sleep(1)
	sendCommand('CmosLed')
	time.sleep(3)
	sendCommand('CmosLed',1)
	time.sleep(1)
	"""Is_pressed()
	while Is_pressed()!= 0:
		print("not pressed 2")"""
	CaptureFinger(True)
	time.sleep(1)
	Enroll2()
	time.sleep(1)
	sendCommand('CmosLed')
	time.sleep(3)
	sendCommand('CmosLed',1)
	time.sleep(1)
	
	CaptureFinger(True)
	time.sleep(1)
	Enroll3()
	time.sleep(1)
	sendCommand('CmosLed')
	print "Enrollment Done Please Enter you FingerPrint to Verify that it has been enrolled Successfully"
	time.sleep(3)
	successtemp=verify()
	print(successtemp)
	success1=successtemp[0]
	success1=str(success1)
	success=int(success1)
	print " success is ",success
	if success>-1 and success <20:
		#"""and success == check:"""
		print "Enrolled Successfully"
	else:
		print "Enrolled Has NOT been Successful"
		print "Please Try again"
		if success <= check-1:
			print" Do NOT enter a Pre-registered Fingerprint"
		else:
			DeleteID(success)
		
	
	
def verify():
	sendCommand('CmosLed',1)
	time.sleep(1)
	CaptureFinger(True)
	time.sleep(2)
	temp=Identify()
	time.sleep(1)
	sendCommand('CmosLed')
	return temp

def DeleteID(ID):
        if sendCommand('DeleteID', ID):
            return [getResponse(), None]
        else:
            raise RuntimeError("Couldn't send packet")
            
def Is_pressed():
        if sendCommand('IsPressFinger'):
			x=[getResponse(True,True),None];
			print(x)
			tempx=str(x[0])
			return int(tempx)
        else:
            raise RuntimeError("Couldn't send packet")
sendCommand('Open')
time.sleep(2)




