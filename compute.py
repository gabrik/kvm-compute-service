from dds.dds import *
from utils import types
import time
import sys
import logging
import json
import uuid



class Compute(object):
    def __init__(self):
        '''filename=LOG_FILE'''

        logging.basicConfig(stream=sys.stdout,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.my_uuid=uuid.uuid4().urn[9:]
        self.logger.info('######### Init Compute Server #########')


        #Init DDS
        #### DDS ###
        self.rt=Runtime()
        self.dp=Participant(0)


        self.register_topic=FlexyTopic(self.dp,'ComputeInfo', lambda x: x.id,None)
        self.register_subscriber=Subscriber(self.dp,[Partition(['dds-kvm-compute'])])
        self.register_reader=FlexyReader(self.register_subscriber,self.register_topic,[Reliable(),KeepLastHistory(1)],self.add_zone_dds)

    
        self.compute_topic=FlexyTopic(self.dp,'ZoneInfo', lambda c: c.id,None)
        self.compute_publisher=Publisher(self.dp,[Partition(['dds-kvm-compute'])])

        self.compute_writer=FlexyWriter(self.compute_publisher,self.compute_topic,[Reliable()])
    
        
        

    def run(self):
        time.sleep(1)
        self.announce_compute()


    def add_zone_dds(self,r):
        samples = r.read(all_samples())
        for s in samples:
            print ('reader>> {0})'.format(s))
    

    def announce_compute(self):
        while True:
        #{"name":"zone-name","uuid":"zone-uuid","address":"zone-ip-address","port":"zone-tcp-port"}
            info=types.KVMServiceMessage(2,{'name':'local','uuid':self.my_uuid})
            self.compute_writer.write(info)
            time.sleep(5)


if __name__=='__main__':

    Compute().run()