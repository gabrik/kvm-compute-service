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


    def run_es(self):
        return '{"status":True,"address":"192.168.2.80"}'

    def run_orchestrator(self):
        return '{"status":True,"address":"192.168.2.82"}'

    def run_cp1(self):
        return '{"status":True,"address":"192.168.2.83"}'


    def run_cp2(self):
        return '{"status":True,"address":"192.168.2.84"}'

    def show_vms(self):
        response=json.dumps(self.vms)
        return response

    def show_zones(self):
        response=json.dumps(self.zones)
        return response


    def add_zone(self,client):
        logger.info('Received zone adding request ')
        SIZE=1024
        #{"name":"zone_name","uuid":"zone_uuid","address":"zone_ip_address","port":"zone_tcp_port"} ZONE FORMAT
        client.send('OK WAITING\n')
        data=unidecode(client.recv(SIZE).decode('ascii').strip())
        logger.info('Trying to add zone %s ' % data)
        zone_data=json.loads(data)
        uuid=zone_data['uuid']
        zone_data.pop('uuid')
        self.zones[uuid]=zone_data
        logger.info('Added zone %s' % uuid)
        print 'zona aggiunta %s' % uuid
        response={'status':True,'uuid':uuid}
        return response

    def start_vm(self,client):
        SIZE=1024
        #VM FORMAT {"zone":"zone_uuid","name":"vmname","type":"vmtype"}
        vmtype=['dhcp','es','acquirer','mysql','orchestrator','frontend','cp1','cp2','client']
        client.send('OK WAITING\n')
        data=unidecode(client.recv(SIZE).decode('ascii').strip())
        vm_data=json.loads(data)
        zone=self.zones.get(vm_data['zone'])
        logger.info('Starting vm %s on zone %s ' % (vm_data.get('name'),vm_data.get('zone')))

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((zone.get('address'),zone.get('port')))
        s.send('startvm')
        time.sleep(1)
       

        recv_data=s.recv(SIZE).decode('ascii').strip()
        logger.info('received %s from compute node' % recv_data)
        #VM FORMAT {"name":"vmname","type":"vmtype"}
        data={"name":vm_data.get('name'),"type":vm_data.get('type')}
        data=json.dumps(data)
        s.send(data)

        while True:
            recv_data=unidecode(s.recv(SIZE).decode('ascii').strip())
            recv_data=json.loads(recv_data)
            logger.info('received %s from compute node' % recv_data)
            if recv_data.get('status',False) == True:
                recv_data['status']='running'
                send_data=json.dumps(recv_data)
                #client.send(send_data+'\n')
                self.vms[recv_data.get('uuid')]=vm_data.get('zone')
                break
            else:
                data_client={"status":"booting"}
                data_client=json.dumps(data_client)
                client.send(data_client+'\n')

        #s.close()
        return send_data

    def kill_vm(self,client):
        SIZE=1024
        #VM KILL FORMAT {'uuid':'vmuuid'}
        client.send('OK WAITING\n')
        data=unidecode(client.recv(SIZE).decode('ascii').strip())
        vm_data=json.loads(data)
        zone=self.zones.get(self.vms[vm_data.get('uuid')])
        logger.info('killing vm %s on zone %s ' % (vm_data.get('uuid'),self.vms[vm_data.get('uuid')]))

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((zone.get('address'),zone.get('port')))
        s.send('killvm')

        recv_data=s.recv(SIZE).decode('ascii').strip()
        logger.info('received %s from compute node' % recv_data)
        data={"uuid":vm_data.get('uuid')}
        data=json.dumps(data)
        s.send(data)
        recv_data=s.recv(SIZE).decode('ascii').strip()
        self.vms.pop(vm_data.get('uuid'))
        return json.loads(recv_data)



            
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
                else:
                    client.send("{'status':false,'error':'wrong command'}\n")
                    logger.info('[ ERRO ] Client %s:%s wrong command!' % address)
                    raise Exception('client disconnected')
            except Exception as e:
                client.send("{'status':false,'error':'aborting'}\n")
                client.close()
                logger.error('%r' % e)
                print ('error %r' % e)
                return False


if __name__ == "__main__":
    ThreadedServer('0.0.0.0',5050).listen()