import socket
import threading
import logging
import json
from unidecode import unidecode
import uuid
import time
from utils import utility
import os
import sys
from dds.dds import *

#LOG_FILE = 'compute_node.log'




# Enable logging
#logging.basicConfig(filename=LOG_FILE,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#    level=logging.INFO)
#logger = logging.getLogger(__name__)

logger=None


commands=["startvm","shutdownvm","destroyzone","close",'killvm']

conf={}

class ZoneInformation:
    def __init__(self,json):
    #{"name":self.name,"uuid":self.uuid,"address":self.local_address,"port":self.port}
        self.name=json.get('name')
        self.uuid=json.get('uuid')
        self.address=json.get('address')
        self.port=json.get('port')

    def __str__(self):
        return 'ZoneInformation >> ({0}, {1})'.format(self.uuid, self.name)




#TODO load configuration from file (ip,port, compute server ip, zone name)

class ThreadedServer(object):

    def __init__(self,host,port):
        logger.info('######### Starting Compute CLient #########')
        self.port = port
        self.name=conf['zone']['name']
        self.server_address=conf['server']['ip']
        self.server_port=int(conf['server']['port'])
        self.uuid=conf['zone']['uuid']
        # get local address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((self.server_address,80))
        self.local_address=s.getsockname()[0]
        s.close()

        self.vms={}

        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
#        self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
#        self.sock.bind((self.local_address,self.port))
        self.count=0

        ### DDS ###

        self.rt=Runtime()
        self.dp=Participant(0)


        self.register_topic=FlexyTopic(self.dp,'KeyValue', lambda x: x.uuid,None)
        self.register_publisher=Publisher(self.dp,[Partition(['dds-kvm.registration'])])
        self.register_writer=FlexyWriter(self.register_publisher,self.register_topic,[Reliable(),KeepLastHistory(1)])

        ### DDS ###
        


        logger.info('[ DONE ] Server binded on %s:%d' % (self.local_address,self.port))

    def listen(self):
        self.sock.listen(5)
        #threading.Thread(target=self.register_to_server).start()
        threading.Thread(target=self.register_to_server_dds).start()
        logger.info('[ DONE ] Server listen on %s:%d' % (self.local_address,self.port))
        while True:
            client,address = self.sock.accept()
            logger.info('[ INFO ] Connection from %s:%s' % address)
            client.settimeout(120)
            threading.Thread(target=self.serveClient,args=(client,address)).start()


    ## DDS ##

    def register_to_server_dds(self):
        msg_value={"name":self.name,"uuid":self.uuid,"address":self.local_address,"port":self.port}

        info=ZoneInformation(msg_value)

        self.register_writer.write(info)

    ## DDS  ##

    def register_to_server(self):
        SIZE=1024
        logger.info('Registering to compute server')
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.connect((self.server_address,self.server_port))
        #{"name":"zone_name","uuid":"zone_uuid","address":"zone_ip_address","port":"zone_tcp_port"} ZONE FORMAT
        
        msg_value={"name":self.name,"uuid":self.uuid,"address":self.local_address,"port":self.port}
        msg_type=2
        msg={'type':msg_type,'value':msg_value}
        msg=json.dumps(msg)

        logger.info('sending %s to server node' % msg)

        server.send(msg)

        recv_data=self.read_from_client(server)
        msg_type=recv_data.get('type',10)
        msg_value=recv_data.get('value',None)

        
        if msg_type==12:
            logger.info('status of registration %s', msg_value.get('status',False))
        while True:
            recv_data=self.read_from_client(server)
            msg_type=recv_data.get('type',10)
            msg_value=recv_data.get('value',None)
            if msg_type==7:
                logger.info('ping receiver from %r' % server.getpeername()[0])
                self.pong(server)
            elif msg_type==8:
                logger.info('pong from %r' % server.getpeername()[0])
                self.ping(client)
            elif msg_type==10:
                server.close()
                return True



        

    def start_vm(self,client,value):
        logger.info('Received start vm request')
        SIZE=1024
        #VM FORMAT {"name":"vmname","type":"vmtype"}
        #client.send('OK WAITING\n')
        #data=unidecode(client.recv(SIZE).decode('ascii').strip())
        #vm_data=json.loads(data)
        vm_data=value
        mac=utility.generate_mac_address(self.count,self.uuid)
        self.count+=1
        logger.info('Generating file and image...')
        #filename=utility.create_vm_start_file(vm_data.get('name'),mac,"/home/user2/Scrivania/template_vm/vm.img","512",conf['zone']['bridge'])
        filename=utility.create_vm_start_file(vm_data.get('name'),mac,"/home/user2/Scrivania/template_vm/acquirer/acquirer.bin","128",conf['zone']['bridge'])
        logger.info('Generated file %s' % filename)
        os.system('chmod +x ' + filename)
        logger.info('Starting vm %s' % filename)
        os.system('sudo ./'+filename)
        logger.info('Waiting for boot to complete...')
        vm_uuid=uuid.uuid4().urn[9:]
        while True:
            time.sleep(2)
            res=utility.get_inet_address_from_mac("192.168.0.1",mac)
            ip=""
            logger.info("Getting IP from Controller VM MAC: %s" % mac)
            if res!=False:
                logger.info('Instance started ip is %s' % res)
                ip=res
                msg_value={"name":vm_data.get('name'),"address":mac,"uuid":vm_uuid,"ip":ip,"status":1}
                msg_type=11
                msg={'type':msg_type,'value':msg_value}
                msg=json.dumps(msg)
                logger.info('sending to compute server %s' % msg)
                client.send(msg)
                self.vms[vm_uuid]=vm_data
                break
            msg_value={"name":vm_data.get('name'),"address":mac,"uuid":vm_uuid,"ip":ip,"status":0}
            msg_type=11
            msg={'type':msg_type,'value':msg_value}
            msg=json.dumps(msg)
            logger.info('sending to compute server %s' % msg)
            client.send(msg)

        msg_type=99
        while msg_type!=10:
            recv_data=self.read_from_client(client)
            msg_type=recv_data.get('type',10)
            msg_value=recv_data.get('value',None)
            if msg_type==10:
                client.close()
                logger.info('closing connection....')



    def kill_vm(self,client,value):
        #SIZE=1024
        #logger.info('Received kill vm request')
        #client.send('OK WAITING\n')
        #data=unidecode(client.recv(SIZE).decode('ascii').strip())
        #VM DATA {"uuid":"vmuuid"}
        #vm_data=json.loads(data)
        vm_data=value
        vm_name=self.vms.get(vm_data.get('uuid')).get('name')
        utility.destroy_vm(vm_name)

        msg_value={"status":True}
        msg_type=12
        msg={'type':msg_type,'value':msg_value}
        msg=json.dumps(msg)
        client.send(msg)

    def read_from_client(self,client):
        SIZE=1024
        recv_data=unidecode(client.recv(SIZE).decode('ascii').strip())
        logger.info('Received %s from client' % recv_data)
        recv_data=json.loads(recv_data)
        return recv_data

#    def pong(self,client):
#        msg_type=8
#        msg={'type':msg_type,'value':None}
#        msg=json.dumps(msg)
#        client.send(msg)

#    def ping(self,client):
#        msg_type=7
#        msg={'type':msg_type,'value':None}
#        msg=json.dumps(msg)
#        client.send(msg)

    def serveClient(self,client,address):
        logger.info('[ INFO ] New Thread on connection from %s:%s' % address)
        SIZE=1024
        while True:
            try:
                
                recv_data=unidecode(client.recv(SIZE).decode('ascii').strip())
                logger.info('Received %s from client' % recv_data)
                ammisible_types=[0,1,4,7,8,9,10]
                recv_data=json.loads(recv_data)
                
                msg_type=recv_data.get('type',10)
                msg_value=recv_data.get('value',None)
                
                if msg_type in ammisible_types:

                    if msg_type==0:
                        self.start_vm(client,msg_value)
                    elif msg_type==1:
                       self.kill_vm(client,msg_value)
                    elif msg_type==7:
                        logger.info('Ping from %s:%s' % address.getpeername()[0])
                        self.pong(client)
                    elif msg_type==8:
                        logger.info('pong from %s:%s' % address.getpeername()[0])
                        self.ping(client)
                    elif msg_type==10:
                        client.close()
                        return True
                        
                else:
                    client.send("{'status':false,'error':'wrong command'}\n")
                    logger.info('[ ERRO ] Client %s:%s wrong command!' % address)
                    raise error('client disconnected')
            except Exception as e:
                #client.send("{'status':false,'error':'aborting'}\n")
                #client.close()
                logger.error('%r' % e)
                print ('error %r' % e)
                return False


if __name__ == "__main__":
    
    global conf
    conf=utility.load_configuration(sys.argv[1])
    LOG_FILE=str('compute_node_%s.log' % conf['zone']['name'])
    logging.basicConfig(filename=LOG_FILE,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
    global logger
    logger = logging.getLogger(__name__)

    #{'zone': {'bridge': 's1-br0', 'uuid': 'a4e6e4ea-c047-11e6-b33b-b742217de0a3', 'name': 'ct', 'port': '5001'}, 'server': {'ip': '127.0.0.1', 'port': '5050'}}


    ThreadedServer('0.0.0.0',int(conf['zone']['port'])).listen()