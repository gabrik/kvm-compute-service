import socket
import threading
import logging
import json
from unidecode import unidecode
import uuid
import time
from utils import utility
import os
LOG_FILE = 'compute_client.log'

# Enable logging
logging.basicConfig(filename=LOG_FILE,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

commands=["startvm","shutdownvm","destroyzone","close",'killvm']

#TODO load configuration from file (ip,port, compute server ip, zone name)

class ThreadedServer(object):

    def __init__(self,host,port):
        logger.info('######### Starting Compute CLient #########')
        self.port = port
        self.name='local'
        self.server_address='127.0.0.1'
        self.server_port=5050
        self.uuid=uuid.uuid4().urn[9:]
        # get local address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((self.server_address,80))
        self.local_address=s.getsockname()[0]
        s.close()

        self.vms={}

        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.sock.bind((self.local_address,self.port))
        self.count=0
        logger.info('[ DONE ] Server binded on %s:%d' % (self.local_address,self.port))

    def listen(self):
        self.sock.listen(5)
        threading.Thread(target=self.register_to_server).start()
        logger.info('[ DONE ] Server listen on %s:%d' % (self.local_address,self.port))
        while True:
            client,address = self.sock.accept()
            logger.info('[ INFO ] Connection from %s:%s' % address)
            client.settimeout(120)
            threading.Thread(target=self.serveClient,args=(client,address)).start()
            

    def register_to_server(self):
        SIZE=1024
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.server_address,self.server_port))
        #{"name":"zone_name","uuid":"zone_uuid","address":"zone_ip_address","port":"zone_tcp_port"} ZONE FORMAT
        data={"name":self.name,"uuid":self.uuid,"address":self.local_address,"port":self.port}
        data=json.dumps(data)
        s.send('addzone')
        time.sleep(1)
        recv_data=s.recv(SIZE).decode('ascii').strip()
        s.send(data)
        time.sleep(1)
        recv_data=s.recv(SIZE).decode('ascii').strip()
        print recv_data
        recv_data=json.loads(recv_data)
        if (recv_data['status']):
            logger.info('Zone added to server')
        else:
            logger.error('Error on zone adding %s' % recv_data['error'])
        s.send('close')

    def start_vm(self,client):
        logger.info('Received start vm request')
        SIZE=1024
        #VM FORMAT {"name":"vmname","type":"vmtype"}
        client.send('OK WAITING\n')
        data=unidecode(client.recv(SIZE).decode('ascii').strip())
        vm_data=json.loads(data)
        mac=utility.generate_mac_address(self.count,self.uuid)
        self.count+=1
        logger.info('Generating file and image...')
        filename=utility.create_vm_start_file(vm_data.get('name'),mac,"/home/gabriele/Scrivania/vm1.img","512")
        logger.info('Generated file %s' % filename)
        os.system('chmod +x ' + filename)
        logger.info('Starting vm %s' % filename)
        os.system('sudo ./'+filename)
        logger.info('Waiting for boot to complete...')
        vm_uuid=uuid.uuid4().urn[9:]
        while True:
            time.sleep(2)
            res=utility.get_inet_address_from_mac("127.0.0.1",mac)
            if res!=False:
                logger.info('Instance started ip is %s' % res)
                ip=res
                data={"name":vm_data.get('name'),"address":mac,"uuid":vm_uuid,"ip":ip,"status":True}
                data=json.dumps(data)
                logger.info('sending to compute server %s' % data)
                client.send(data)
                self.vms[vm_uuid]=vm_data.get('name')
                break
            logger.info('Waiting for boot to complete...')
            data={"name":vm_data.get('name'),"address":mac,"uuid":vm_uuid,"ip":"","status":False}
            data=json.dumps(data)
            logger.info('sending to compute server %s' % data)
            client.send(data)

        # VM STARTED FORMAT {"name":"vmname","address":"vmmac","uuid":"vmuuid","ip":"vm_ip"}
        client.close()

    def kill_vm(self,client):
        SIZE=1024
        logger.info('Received kill vm request')
        client.send('OK WAITING\n')
        data=unidecode(client.recv(SIZE).decode('ascii').strip())
        #VM DATA {"uuid":"vmuuid"}
        vm_data=json.loads(data)
        vm_name=self.vms.get(vm_data.get('uuid'))
        utility.destroy_vm(vm_name)
        response={'status':True}
        client.send(json.dumps(response)+'\n')



    def serveClient(self,client,address):
        logger.info('[ INFO ] New Thread on connection from %s:%s' % address)
        SIZE=1024
        while True:
            try:
                data=client.recv(SIZE).decode('ascii').strip()
                logger.info('Received %s from client' % data)
                if data in commands:
                    if data=="startvm":
                        response=json.dumps(self.start_vm(client))+'\n'
                    elif data == "killvm":
                         response=json.dumps(self.kill_vm(client))+'\n'
                    elif data == "shutdownvm":
                        response=self.show_zones()+'\n'
                    elif data=="destroyzone":
                        response=json.dumps(self.add_zone(client))+'\n'
                    elif data == "close":
                        client.send("{'status':true}\n")
                        client.close()
                        return True

                    client.send(response)
                else:
                    client.send("{'status':false,'error':'wrong command'}\n")
                    logger.info('[ ERRO ] Client %s:%s wrong command!' % address)
                    raise error('client disconnected')
            except Exception as e:
                client.send("{'status':false,'error':'aborting'}\n")
                client.close()
                logger.error('%r' % e)
                print ('error %r' % e)
                return False


if __name__ == "__main__":
    ThreadedServer('0.0.0.0',5001).listen()