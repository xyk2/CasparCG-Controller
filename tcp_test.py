#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import time

TCP_IP = '192.168.0.14'
TCP_PORT = 5250
BUFFER_SIZE = 10000

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))

s.send('VERSION\r\n')
print s.recv(BUFFER_SIZE)

#for x in range(0, 1000):
#	s.send("CG 1-40 UPDATE 1  \"<templateData><componentData id=\\\"quarter\\\"><data id=\\\"text\\\" value=\\\"%s\\\"/></componentData><componentData id=\\\"away_name\\\"><data id=\\\"text\\\" value=\\\"%s\\\"/></componentData><componentData id=\\\"home_name\\\"><data id=\\\"text\\\" value=\\\"%s\\\"/></componentData><componentData id=\\\"home_fouls\\\"><data id=\\\"text\\\" value=\\\"%s\\\"/></componentData><componentData id=\\\"game_clock\\\"><data id=\\\"text\\\" value=\\\"%s\\\"/></componentData><componentData id=\\\"shot_clock\\\"><data id=\\\"text\\\" value=\\\"%s\\\"/></componentData></templateData>\"\r\n"%(x,x,x,x,x,x))
#	data = s.recv(BUFFER_SIZE)
#	print data, x
#	time.sleep(0.05)

#s.send("INFO")
data = s.recv(BUFFER_SIZE)
s.close()

print "received data:", data