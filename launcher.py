#!/usr/bin/python
import os
import socket 
import sys
from subprocess import call
import time

def run_es():
	#os.system("nohup vlc-wrapper -vvv rtp://0.0.0.0:50040 --sout '#rtp{dst=192.168.2.2,port=50040,mux=ts}'")
	return '{"status":"ready","address":"192.168.2.80"}'

def run_orchestrator():
    os.system("/home/ubuntu/template/boot.sh")

def run_cp1():
	os.system("/home/ubuntu/template/content/CP1.sh")


def run_cp2():
	os.system("/home/ubuntu/template/content/CP2.sh")




def main():

	

	f=open("/home/gabriele/startup.txt", 'a')
	f.write(str(time.time()) + " Stated!\n")

	BUFFSIZE = 255	
	port = 5050
	address = '0.0.0.0'
	iface=(address,port)	
	f.write ('Starring server...\n')

	sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

	sock.bind(iface)

	f.write('listening to %s:%s\n'  % iface)
	
	sock.listen(5)
		
	while True:
			
		conn,addr = sock.accept()
		f.write('accepted connection from %s:%s\n' % addr)

		conn.send('Connected to compute controller\n')


		data = conn.recv(BUFFSIZE).decode('ascii').strip()
		f.write('Input: %s \n' % data)
		commands=["zones","startvm"]
		if data in commands:
			conn.send('ok')
			pid=os.fork()
			if pid==0:

				if data=="server":
					run_orchestrator()
				elif data == "cp1":
					run_cp1()
				elif data=="cp2":
					run_cp2()
				elif data == "es":
					run_es()
				
			else:
				f.write('Started! on process %d\n' % pid)
				conn.close()
		else:
			f.write('Invalid input! %s \n' % data)
			conn.send('ko')
			conn.close()


if __name__ == '__main__':
	main()
