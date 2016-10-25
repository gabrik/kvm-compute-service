import socket
import threading
import logging
import json
from unidecode import unidecode
LOG_FILE = 'compute_server.log'

# Enable logging
logging.basicConfig(filename=LOG_FILE,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	level=logging.INFO)
logger = logging.getLogger(__name__)

commands=["zones","startvm","addzone",'close']

#TODO load configuration from file (ip,port, controller ip)

class ThreadedServer(object):

    def __init__(self,host,port):
        logger.info('######### Starting Compute Server #########')
        self.host = host
        self.port = port
        self.zones={}
        
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
        return zone


            
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
                    elif data == "zones":
                        response=self.show_zones()+'\n'
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
                    raise error('client disconnected')
            except Exception as e:
                client.send("{'status':false,'error':'aborting'}\n")
                client.close()
                logger.error('%r' % e)
                print ('error %r' % e)
                return False


if __name__ == "__main__":
    ThreadedServer('0.0.0.0',5050).listen()