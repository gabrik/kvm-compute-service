from dds.dds import *
from utils import types
import  time
import sys
import logging
import json
from flask import Flask


app = Flask(__name__)

def init(ip,p):
    logger.info('######### Starting Compute Server #########')
    global host
    host = ip
    global port
    port = p
    global zones
    zones={}
    global vms
    vms={} 
    global sock

    #### DDS ###
    rt=Runtime()
    dp=Participant(0)

    dp2=Participant(0)


    register_topic=FlexyTopic(dp2,'ZoneInfo', lambda x: x.id,None)
    register_subscriber=Subscriber(dp2,[Partition(['dds-kvm-compute'])])
    register_reader=FlexyReader(register_subscriber,register_topic,[Reliable()],add_zone_dds)


    compute_topic=FlexyTopic(dp,'ComputeInfo', lambda c: c.id,None)
    compute_publisher=Publisher(dp,[Partition(['dds-kvm-compute'])])

    global compute_writer
    compute_writer=FlexyWriter(compute_publisher,compute_topic,[Reliable(),KeepLastHistory(1)])


    app.run(debug=True,host=host,port=port)

    announce_compute()

def add_zone_dds(r):
    samples = r.read(new_samples())
    for s in samples:
        print ('reader>> {0})'.format(s))

        if(s.id==2):
            zone_info=json.loads(s.value)
            zone_info['last_update']=time.time()
            zones[zone_info.get('uuid')]=zone_info

def announce_compute():
    while True:

        #0 Avvia una VM value -> {"zone":"zone_uuid","name":"vmname","type":"vmtype"}
        #1 Distruggi una VM value -> {'uuid':'vmuuid'}

        info=types.KVMServiceMessage(0,{'zone':'uuid_zona','name':'instance_name','type':'instance_flavor'})
        compute_writer.write(info)
        time.sleep(5)


### FLASK REST FOR CLIENTS

@app.route('/')
def index():
    return "Hello, World!"

@app.route('/zones')
def get_zones():

    return json.dumps(zones)

@app.route('/new_instance')
def new_instance():
    info=types.KVMServiceMessage(0,{'zone':'uuid_zona','name':'instance_name','type':'instance_flavor'})
    compute_writer.write(info)
    return json.dumps(info)



if __name__=='__main__':

    '''filename=LOG_FILE'''

    logging.basicConfig(stream=sys.stdout,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	level=logging.INFO)
    global logger
    logger = logging.getLogger(__name__)
    init('0.0.0.0',5050)