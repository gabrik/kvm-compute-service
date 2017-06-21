from dds.dds import *
from utils import types
import time
import sys
import logging
import json
import uuid


def init():
    logger.info('######### Starting Compute Server #########')


    #### DDS ###
    rt=Runtime()
    dp=Participant(0)

    #dp2=Participant(0)


    register_topic=FlexyTopic(dp,'ComputeInfo', lambda x: x.id,None)
    register_subscriber=Subscriber(dp,[Partition(['dds-kvm-compute'])])
    register_reader=FlexyReader(register_subscriber,register_topic,[Reliable(),KeepLastHistory(1)],add_zone_dds)

    
    compute_topic=FlexyTopic(dp,'ZoneInfo', lambda c: c.id,None)
    compute_publisher=Publisher(dp,[Partition(['dds-kvm-compute'])])

    global compute_writer
    compute_writer=FlexyWriter(compute_publisher,compute_topic,[Reliable()])
    
    time.sleep(1)
    announce_compute()




def add_zone_dds(r):
    samples = r.read(all_samples())
    for s in samples:
        print ('reader>> {0})'.format(s))
    

def announce_compute():
    while True:
        #{"name":"zone-name","uuid":"zone-uuid","address":"zone-ip-address","port":"zone-tcp-port"}
        info=types.KVMServiceMessage(2,{'name':'local','uuid':my_uuid})
        compute_writer.write(info)
        time.sleep(5)


if __name__=='__main__':

    '''filename=LOG_FILE'''

    logging.basicConfig(stream=sys.stdout,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	level=logging.INFO)
    global logger
    logger = logging.getLogger(__name__)

    global my_uuid
    my_uuid=uuid.uuid4().urn[9:]

    init()