import socket   #for sockets
import sys  #for exit
import struct
import time
import datetime
import re
import os, errno
import argparse
import serial

parser = argparse.ArgumentParser(description='Take Data from DAPHNE board')
parser.add_argument('filename', nargs='?',
                    help='the filename to write to in the DATA/{DATE} directory.')
parser.add_argument('--daphne_port', action='store', default="5000",
                    help='path to daphne board', type=int)
parser.add_argument('--daphne_addr', action='store', default="192.168.124.81",
                    help='path to daphne board')
parser.add_argument('-f', action='store_true',
                    help='use the relative path, not DATA/{DATE}')
parser.add_argument('--overwrite', action='store_true',
                    help='allow overwriting filename')
parser.add_argument('--command', 
                    help='run command on board, then take data')
parser.add_argument('--command_stop', action='store_true',
                    help='run command on board, then stop')
parser.add_argument('--spill_length', action='store',
                    help='sets the spill length. HEX')

args = parser.parse_args()
#print args
s = serial.Serial('/dev/ttyUSB0', 480600)


if args.spill_length != None:
	s.write("wr 308 " + args.spill_length + "\r")
	print s.read(1024)
	time.sleep(.5)
	s.write("rd 308 \r")
	print s.read(1024)
	time.sleep(2)

if args.command != None:
	s.write(args.command + "\r")
	print s.read(4096)
if args.command_stop:
	print "Command Finished. Exiting."
	exit(0)
ts = time.time()
date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')

if args.f == False:
	rel_path = "DAPHNE/DATA/{}/{}.bin".format(date, args.filename)
	filepath = os.path.expanduser("~/" + rel_path)
	directory = os.path.dirname(filepath)
	try:
	    os.makedirs(directory)
	except OSError as e:
	    if e.errno != errno.EEXIST:
		raise
else:
	filepath = args.filename
if os.path.isfile(filepath) and not args.overwrite:
	print "File Already exists. Exiting. use --overwrite to ignore"
	exit(1)


file = open(filepath,"w") 

st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
file.write(str(ts))
file.write('\n')
RD_LEN = 1024

#print "filepath: " + filepath

print "Take Data (wr 303 300)"
s.write('wr 303 300\r')
s.read(1024)
if args.spill_length:
	print "Wait "+str(args.spill_length)+" S"
	time.sleep(float(args.spill_length))
else:
	print "Wait 2 S"
	time.sleep(2)
s.write('rd 67\r')
time.sleep(.25)
print "READ 67: ", re.search(r'[0-9A-F]+', s.read(1024)).group()
count = 0
while True:
	print "Checking if spill done"
	s.write('rd 303\r')
	time.sleep(.1)
	rd303 = re.search(r'[0-9A-F]+', s.read(1024)).group() 
	print "Spill Reg value:", rd303
	time.sleep(.1)
	s.write('rd 67\r')
	if rd303 == "0000":
		print "Spill Done. 67: ", re.search(r'[0-9A-F]+', s.read(1024)).group()
		break
	count += 1
	print "Spill Not Done. 67: ", re.search(r'[0-9A-F]+', s.read(1024)).group(), " count is:", count
	time.sleep(1)
s.settimeout(1)
try:
	s.read(1024)
except:
	print "Ready"
s.write('rdb\r\n')
#s.read(1024)
for i in range(10000):
	try:
		buf = s.read(RD_LEN)
	except socket.timeout:
		print "Readout Attempts: ", i-1
		break
	file.write(buf)

s.close()
 
print "filepath: " + rel_path