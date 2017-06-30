from dds.dds import *
from utils import types
import  time
import sys
import logging
import json
from flask import Flask






class Controller(object):
    def __init__(self,host,port):

        '''filename=LOG_FILE'''

        logging.basicConfig(stream=sys.stdout,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	    level=logging.INFO)
        
        self.logger = logging.getLogger(__name__)

        self.logger.info('######### Init Controller Server #########')

        self.app=app = Flask(__name__)
        self.host=host
        self.port=port
        self.zones={}
        self.vms={}
        
        #Initialize DDS
        self.rt=Runtime()
        self.dp=Participant(0)

        self.register_topic=FlexyTopic(self.dp,'ZoneInfo', lambda x: x.id,None)
        self.register_subscriber=Subscriber(self.dp,[Partition(['dds-kvm-compute'])])
        self.register_reader=FlexyReader(self.register_subscriber,self.register_topic,[Reliable()],self.add_zone_dds)


        self.compute_topic=FlexyTopic(self.dp,'ComputeInfo', lambda c: c.id,None)
        self.compute_publisher=Publisher(self.dp,[Partition(['dds-kvm-compute'])])

        
        self.compute_writer=FlexyWriter(self.compute_publisher,self.compute_topic,[Reliable(),KeepLastHistory(1)])

    
    def run(self):
        self.logger.info('######### Starting Controller Server #########')
        self.add_endpoint(endpoint='/', endpoint_name='index', handler=self.index)
        self.add_endpoint(endpoint='/zones', endpoint_name='zones', handler=self.get_zones)
        self.add_endpoint(endpoint='/new_instance', endpoint_name='new_instance', handler=self.new_instance)
        self.app.run(debug=True,host=self.host,port=self.port)



    def add_zone_dds(self,r):
        samples = r.read(new_samples())
        for s in samples:
            print ('reader>> {0})'.format(s))

        if(s.id==2):
            zone_info=json.loads(s.value)
            zone_info['last_update']=time.time()
            self.zones[zone_info.get('uuid')]=zone_info

    def announce_compute():
        while True:

            #0 Avvia una VM value -> {"zone":"zone_uuid","name":"vmname","type":"vmtype"}
            #1 Distruggi una VM value -> {'uuid':'vmuuid'}

            info=types.KVMServiceMessage(0,{'zone':'uuid_zona','name':'instance_name','type':'instance_flavor'})
            self.compute_writer.write(info)
            time.sleep(5)


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
    Controller('0.0.0.0',5050).run()
