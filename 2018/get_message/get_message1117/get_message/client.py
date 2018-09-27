#-*- coding: UTF-8 -*-
import sys,os,socket,time
uuid_file = sys.path[0]+'/UUID'
touch_file = sys.path[0]+'/pant.lock'
if os.path.exists(uuid_file) :
        file_object = open(uuid_file)
        mid = file_object.read()
        file_object.close()
else :
        mid = uuid.uuid1().get_hex()[16:]
        file_object = open(uuid_file , 'w')
        file_object.write( mid )
        file_object.close()
def touch(fname, times=None):
	with open(fname, 'a'):
		os.utime(fname, times)
#to sock
while True:
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect(('121.41.115.44', 23712))
	sock.send(mid)
	touch(touch_file)
	buf = sock.recv(3)
	sock.close()
	if buf == '1':
		os.system('/usr/bin/python /root/get_message/get_ip.py')
	time.sleep(1)
