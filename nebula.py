from dds.dds import *
from utils import types
import time
import sys
import logging
import json
from flask import Flask
import uuid
import threading
import libvirt





class Nebula(object):
    def __init__(self,host,port,name):

        '''filename=LOG_FILE'''

        logging.basicConfig(stream=sys.stdout,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	    level=logging.INFO)
        
        self.logger = logging.getLogger(__name__)

        self.logger.info('######### Init Nebula Node #########')

        self.app=app = Flask(__name__)
        self.host=host
        self.port=port
        self.name=name
        self.zones={}
        self.vms={}
        self.my_uuid=uuid.uuid4().urn[9:]

        self.logger.info('######### Nebula Node UUID is: '+self.my_uuid+' #########')
        #Initialize DDS
        self.rt=Runtime()
        self.dp=Participant(0)


        self.zone_topic=FlexyTopic(self.dp,'ZoneInfo',lambda x: x.id,None)
        print ("Create Topic ZoneInfo")


        self.zone_subscriber=Subscriber(self.dp,[Partition(['dds-nebula-compute'])])
        print ("Create Subscriber ZoneInfo")
        self.zone_pubisher=Publisher(self.dp,[Partition(['dds-nebula-compute'])])
        print ("Create Pubisher ZoneInfo")

        
        self.zone_reader=FlexyReader(self.zone_subscriber,self.zone_topic,[Reliable()],self.zone_listener)
        print ("Create Reader ZoneInfo")
        self.zone_writer=FlexyWriter(self.zone_pubisher,self.zone_topic,[Reliable(),KeepLastHistory(1)])
        print ("Create Writer ZoneInfo")

        self.compute_topic=FlexyTopic(self.dp,'ComputeInfo', lambda c: c.id,None)
        print ("Create Topic ComputeInfo")
        self.compute_publisher=Publisher(self.dp,[Partition(['dds-nebula-compute'])])
        print ("Create Publisher ComputeInfo")
        self.compute_subscriber=Subscriber(self.dp,[Partition(['dds-nebula-compute'])])
        print ("Create Subscriber ComputeInfo")

        self.compute_writer=FlexyWriter(self.compute_publisher,self.compute_topic,[Reliable(),KeepLastHistory(1)])
        print ("Create Writer ComputeInfo")
        self.compute_reader=FlexyReader(self.compute_subscriber,self.compute_topic,[Reliable()],self.compute_listener)
        print ("Create Reader ComputeInfo")

        #self.register_topic=FlexyTopic(self.dp,'ZoneInfo', )
        #self.register_subscriber=Subscriber(self.dp,[Partition(['dds-nebula-compute'])])
        #self.register_reader=FlexyReader(self.register_subscriber,self.register_topic,[Reliable()],self.add_zone_dds)
        #self.compute_writer=FlexyWriter(self.compute_publisher,self.compute_topic,[Reliable(),KeepLastHistory(1)])

    def flask_start(self):
        self.app.run(threaded=True,debug=True,use_reloader=False,host=self.host,port=self.port)

    def run(self):
        self.logger.info('######### Starting Nebula Node API #########')
        self.add_endpoint(endpoint='/', endpoint_name='index', handler=self.index)
        self.add_endpoint(endpoint='/zones', endpoint_name='zones', handler=self.get_zones)
        self.add_endpoint(endpoint='/new_instance', endpoint_name='new_instance', handler=self.new_instance)
        
        threading.Thread(target=self.flask_start).start()
        #self.create_instance()
        #self.announce_nebula_node()

   

    def zone_listener(self,r):
        samples = r.read(new_samples())
        for s in samples:
            print ('reader>> {0})'.format(s))

        if(s.id==2):
            zone_info=json.loads(s.value)
            zone_info['last_update']=time.time()
            self.zones[zone_info.get('uuid')]=zone_info

    def compute_listener(self,r):
        samples = r.read(new_samples())
        for s in samples:
            print ('reader>> {0})'.format(s))

    def announce_nebula_node(self):
         while True:
        #{"name":"zone-name","uuid":"zone-uuid","address":"zone-ip-address","port":"zone-tcp-port"}
            info=types.KVMServiceMessage(2,{'name':self.name,'uuid':self.my_uuid})
            self.compute_writer.write(info)
            time.sleep(5)

    def announce_compute(self):
        while True:

            #0 Avvia una VM value -> {"zone":"zone_uuid","name":"vmname","type":"vmtype"}
            #1 Distruggi una VM value -> {'uuid':'vmuuid'}

            info=types.KVMServiceMessage(0,{'zone':'uuid_zona','name':'instance_name','type':'instance_flavor'})
            self.compute_writer.write(info)
            time.sleep(5)

    def create_instance(self):
        conn=libvirt.open("qemu:///system")
        names = conn.listDefinedDomains()
        print names



    ### FLASK REST FOR CLIENTS

    #@self.app.route('/')
    def index(self):
        return "Hello, World!"

    #@self.app.route('/zones')
    def get_zones(self):

        return json.dumps(self.zones)

    #@self.app.route('/new_instance')
    def new_instance(self):
        info=types.KVMServiceMessage(0,{'zone':'uuid_zona','name':'instance_name','type':'instance_flavor'})
        self.compute_writer.write(info)
        return json.dumps(info)


    def add_endpoint(self, endpoint=None, endpoint_name=None, handler=None):
        self.app.add_url_rule(endpoint, endpoint_name,handler)


if __name__=='__main__':
    Nebula('0.0.0.0',int(sys.argv[1]),sys.argv[2]).run()
