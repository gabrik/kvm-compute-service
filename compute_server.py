#!/usr/bin/env python

import socket
import threading
import logging
import json
from unidecode import unidecode
import time

LOG_FILE = 'compute_server.log'

# Enable logging
logging.basicConfig(filename=LOG_FILE,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	level=logging.INFO)
logger = logging.getLogger(__name__)

commands=["zones","startvm","addzone",'close','vms','killvm']

#TODO load configuration from file (ip,port, controller ip)

class ThreadedServer(object):

    def __init__(self,host,port):
        logger.info('######### Starting Compute Server #########')
        self.host = host
        self.port = port
        self.zones={}
        self.vms={}
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.sock.bind((self.host,self.port))
        logger.info('[ DONE ] Server binded on %s:%d' % (self.host,self.port))
        
    def listen(self):
        self.sock.listen(5)
        logger.info('[ DONE ] Server listen on %s:%d' % (self.host,self.port))
        while True:
            client,address = self.sock.accept()
            logger.info('[ INFO ] Connection from %s:%s' % address)
            client.settimeout(120)
            threading.Thread(target=self.serveClient,args=(client,address)).start()

    def read_from_client(self,client):
        SIZE=1024
        recv_data=unidecode(client.recv(SIZE).decode('ascii').strip())
        logger.info('Received %s from client' % recv_data)
        recv_data=json.loads(recv_data)
        return recv_data

    def run_es(self):
        return '{"status":True,"address":"192.168.2.80"}'

    def run_orchestrator(self):
        return '{"status":True,"address":"192.168.2.82"}'

    def run_cp1(self):
        return '{"status":True,"address":"192.168.2.83"}'


    def run_cp2(self):
        return '{"status":True,"address":"192.168.2.84"}'

    def show_vms(self,client):
        msg_value={"status":True,'res':self.vms}
        msg_type=12
        msg={'type':msg_type,'value':msg_value}
        msg=json.dumps(msg)
        client.send(msg)

    def show_zones(self,client):

        all_zones=[]
        for uuid in self.zones:
            zone={}
            zone['uuid']=uuid
            zone['value']=self.zones[uuid]
            all_zones.append(zone)


        msg_value={"status":True,'res':all_zones}
        msg_type=12
        msg={'type':msg_type,'value':msg_value}
        msg=json.dumps(msg)
        client.send(msg)


    def add_zone(self,client,value):
        logger.info('Received zone adding request ')
        #SIZE=1024
        #{"name":"zone_name","uuid":"zone_uuid","address":"zone_ip_address","port":"zone_tcp_port"} ZONE FORMAT
        #client.send('OK WAITING\n')
        #data=unidecode(client.recv(SIZE).decode('ascii').strip())
        #logger.info('Trying to add zone %s ' % data)
        #zone_data=json.loads(data)
        zone_data=value
        uuid=zone_data['uuid']
        zone_data.pop('uuid')
        self.zones[uuid]=zone_data
        logger.info('Added zone %s' % uuid)
        print 'zona aggiunta %s' % uuid
        
        msg_value={"status":True}
        msg_type=12
        msg={'type':msg_type,'value':msg_value}
        msg=json.dumps(msg)
        client.send(msg)

        while True:
            time.sleep(10)
            self.ping(client)
            recv_data=self.read_from_client(client)
            msg_type=recv_data.get('type',10)
            msg_value=recv_data.get('value',None)
            if msg_type==8:
                logger.info('pong from %r' % client)


    def start_vm(self,client,value):
        SIZE=1024
        #VM FORMAT {"zone":"zone_uuid","name":"vmname","type":"vmtype"}
        #vmtype=['dhcp','es','acquirer','mysql','orchestrator','frontend','cp1','cp2','client']
        #client.send('OK WAITING\n')
        #data=unidecode(client.recv(SIZE).decode('ascii').strip())
        #vm_data=json.loads(data)
        vm_data=value
        zone=self.zones.get(vm_data['zone'])
        logger.info('Starting vm %s on zone %s ' % (vm_data.get('name'),vm_data.get('zone')))

        compute = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        compute.connect((zone.get('address'),zone.get('port')))

        msg_value={"name":vm_data.get('name'),"type":vm_data.get('type')}
        msg_type=0
        msg={'type':msg_type,'value':msg_value}
        msg=json.dumps(msg)

        logger.info('sending %s to compute node' % msg)

        compute.send(msg)

        flag=True
        while flag:
            recv_data=self.read_from_client(compute)
            msg_type=recv_data.get('type',10)
            msg_value=recv_data.get('value',None)

            logger.info('received %s from compute node' % recv_data)
            if msg_value.get('status',0) == 1:
                flag=False
                self.vms[msg_value.get('uuid')]=vm_data.get('zone')
                
                c_msg_type=10
                c_msg={'type':msg_type,'value':None}
                c_msg=json.dumps(c_msg)
                compute.send(c_msg)
                compute.close()
                
            
            msg={'type':msg_type,'value':msg_value}
            msg=json.dumps(msg)
            logger.info('sending %s to client' % msg)
            client.send(msg+'\n')

    def pong(self,client):
        msg_type=8
        msg={'type':msg_type,'value':None}
        msg=json.dumps(msg)
        client.send(msg)

    def ping(self,client):
        msg_type=7
        msg={'type':msg_type,'value':None}
        msg=json.dumps(msg)
        client.send(msg)


    def kill_vm(self,client,value):
        #SIZE=1024
        #VM KILL FORMAT {'uuid':'vmuuid'}
        #client.send('OK WAITING\n')
        #data=unidecode(client.recv(SIZE).decode('ascii').strip())
        #vm_data=json.loads(data)
        vm_data=value
        zone=self.zones.get(self.vms[vm_data.get('uuid')])
        logger.info('killing vm %s on zone %s ' % (vm_data.get('uuid'),self.vms[vm_data.get('uuid')]))


        compute = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        compute.connect((zone.get('address'),zone.get('port')))
        
        msg_value={"uuid":vm_data.get('uuid')}
        msg_type=1
        msg={'type':msg_type,'value':msg_value}
        msg=json.dumps(msg)

        logger.info('sending %s to compute node' % msg)

        compute.send(msg)
        recv_data=self.read_from_client(compute)
        msg_type=recv_data.get('type',10)
        msg_value=recv_data.get('value',None)

        if msg_type==12:
            logger.info('status of kill %s', msg_value.get('status',False))
        msg={'type':msg_type,value:msg_value}
        msg=json.dumps(msg)
        client.send(msg)




            
    def serveClient(self,client,address):
        logger.info('[ INFO ] New Thread on connection from %s:%s' % address)
        SIZE=1024
        while True:
            try:

                recv_data=unidecode(client.recv(SIZE).decode('ascii').strip())
                logger.info('Received %s from client' % recv_data)
                print ('received %s \n' % recv_data)
                ammisible_types=range(0,11)
                recv_data=json.loads(recv_data)
                
                msg_type=recv_data.get('type',10)
                msg_value=recv_data.get('value',None)
                
                if msg_type in ammisible_types:

                    if msg_type==0:
                        self.start_vm(client,msg_value)
                    elif msg_type==1:
                        self.kill_vm(client,msg_value)
                    elif msg_type==2:
                        self.add_zone(client,msg_value)
                    elif msg_type==3:
                        #self.add_zone(client,msg_value)
                        client.send("nope")
                    elif msg_type==4:
                        self.show_vms(client)
                    elif msg_type==5:
                        self.show_zones(client)
                    elif msg_type==7:
                        logger.info('Ping from %s:%s' % address)
                        self.pong(client)
                    elif msg_type==8:
                        logger.info('pong from %s:%s' % address)
                        self.ping(client)
                    elif msg_type==10:
                        client.close()
                        return True


                        '''
                    elif data == "killvm":
                        response=json.dumps(self.kill_vm(client))+'\n'
                    elif data == "zones":
                        response=self.show_zones()+'\n'
                    elif data == "vms":
                        response=self.show_vms()+'\n'
                    elif data=="addzone":
                        response=json.dumps(self.add_zone(client))+'\n'
                    elif data == "close":
                        client.send("{'status':true}\n")
                        client.close()
                        return True

                    client.send(response)
                    '''
                else:
                    client.send("{'status':false,'error':'wrong command'}\n")
                    logger.info('[ ERRO ] Client %s:%s wrong command!' % address)
                    raise Exception('client disconnected')
            except Exception as e:
                #client.send("{'status':false,'error':'aborting'}\n")
                #client.close()
                logger.error('%r' % e)
                print ('error %r' % e)
                return False


if __name__ == "__main__":
    ThreadedServer('0.0.0.0',5050).listen()