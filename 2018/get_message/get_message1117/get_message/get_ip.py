#-*- coding: UTF-8 -*-
import socket
import fcntl
import struct
import urllib2
import urllib
import sys,os
import ConfigParser
import hashlib
import json
import uuid
import base64
import subprocess

config = ConfigParser.ConfigParser()
config.readfp(open(sys.path[0]+'/config.ini',"rb"))

uuid_file=sys.path[0]+'/UUID'
touch_file = sys.path[0]+'/reboot.lock'
if os.path.exists(uuid_file) :
	file_object = open(uuid_file)
	mid = file_object.read()
	file_object.close()
else :
	mid = uuid.uuid1().get_hex()[16:]
	file_object = open(uuid_file , 'w')
	file_object.write( mid )
	file_object.close()

def send_message(source_data):
	source_data=source_data.replace('\n','$$$')
	f=urllib2.urlopen(
			url = config.get("global","ipurl"),
			data =  source_data,
			timeout = 60
			)
	tmp_return=f.read()
	request_json=json.loads(tmp_return)
	request_md5=request_json['md5']
	del request_json['md5']
	new_request_json = []
        for item in request_json:
		new_request_json.append(str(request_json[item]))
	new_request_json.sort()
        str_to_sign = ''.join(new_request_json)
	md5=hashlib.sha1(str_to_sign.encode('utf-8')+mid).hexdigest()
	if (md5 == request_md5):
		operate(request_json)
	else :
		print 'MD5 ERR'

	print "return: "+tmp_return;

def get_ip_address(ifname):
    skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    pktString = fcntl.ioctl(skt.fileno(), 0x8915, struct.pack('256s', ifname[:15]))
    ipString  = socket.inet_ntoa(pktString[20:24])
    return ipString

def bulid_response(data, code, msg, msgid):
    response_obj = {'msg':msg,'code':code,'data':data,'msgid':msgid}
    hash_str = list(response_obj.values())
    hash_str.sort()
    hash_str = ''.join(hash_str)
    hash_str = hashlib.sha1(hash_str.encode('utf-8')+mid).hexdigest()
    response_obj['md5'] = hash_str
    strs = base64.b64encode(json.JSONEncoder().encode(response_obj))
    return strs

def operate(request_json):
	if request_json['type'] == 'reboot' :
		# touch file
		file=open(touch_file, 'w')
		file.write(request_json['msgid'])
		file.close()
		os.system('/sbin/reboot')
	elif request_json['type'] == 'code' :
		msgs = json.loads(base64.b64decode(request_json['msg']))
		fileHandle = open ( urllib.unquote(msgs['patch']) , 'w' )
		fileHandle.write( urllib.unquote(base64.b64decode( msgs['content'] ) ))
		fileHandle.close()
		data = bulid_response('ok','0','ok',request_json['msgid'])
                send_message(mid+'|'+eth+'|'+usb+'|'+data)
	elif request_json['type'] == 'crontab' :
		FileHander = open('/var/spool/cron/crontabs/root','r+')
		data= base64.b64encode(FileHander.read())
		FileHander.close()
		data = bulid_response(data,'0','ok',request_json['msgid'])
		send_message(mid+'|'+eth+'|'+usb+'|'+data)
	elif request_json['type'] == 'ps':
		returnstr=subprocess.Popen('ps aux',stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
		data= base64.b64encode(returnstr.stdout.read())
		data = bulid_response(data,'0','ok',request_json['msgid'])
                send_message(mid+'|'+eth+'|'+usb+'|'+data)
	elif request_json['type'] == 'file':
		msgs = json.loads(base64.b64decode(request_json['msg']))
                FileHander = open(urllib.unquote(msgs['patch']),'r+')
                data= base64.b64encode(FileHander.read())
                FileHander.close()
                data = bulid_response(data,'0','ok',request_json['msgid'])
                send_message(mid+'|'+eth+'|'+usb+'|'+data)
	elif request_json['type'] == 'dir':
		msgs = json.loads(base64.b64decode(request_json['msg']))
		patch = urllib.unquote(msgs['patch'])
		lisdirs = os.listdir(patch)
		dir_obj = {}
		if patch[-1]!='/':
			patch = patch+'/'
		for lisdir in lisdirs:
			dir_obj[lisdir]=os.path.isdir(patch+lisdir)
		data = base64.b64encode(json.JSONEncoder().encode(dir_obj))
		data = bulid_response(data,'0','ok',request_json['msgid'])
                send_message(mid+'|'+eth+'|'+usb+'|'+data)
	elif request_json['type'] == 'kill':
		msgs = json.loads(base64.b64decode(request_json['msg']))
                lisdirs = urllib.unquote(msgs['patch'])
		os.system('kill -9 '+lisdirs)
		data = bulid_response('ok','0','ok',request_json['msgid'])
                send_message(mid+'|'+eth+'|'+usb+'|'+data)
	else :
		print 'OK'
	


usb='123'
eth=get_ip_address('eth0')
#eth = '127.0.0.1'
# reboot send ok
if os.path.isfile(touch_file):
	# read file
	touch_file_obj = open(touch_file,'r')
	touch_msgid=touch_file_obj.read()
	touch_file_obj.close()
	data = bulid_response('ok','0','ok',touch_msgid)
        send_message(mid+'|'+eth+'|'+usb+'|'+data)
	os.unlink(touch_file)
send_message(mid+'|'+eth+'|'+usb)
