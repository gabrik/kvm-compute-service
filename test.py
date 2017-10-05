from utils import types
from utils import virt_utils
import time
import sys
import logging
import json
from flask import Flask
import uuid
import threading
import libvirt



def main():

    hypervisor_connection = virt_utils.connect()

    xml_file = virt_utils.generate_domain_configuration("cirros_py",uuid.uuid4().urn[9:],256,1,virt_utils.randomMAC(),'br0','/home/gabriele/Scaricati/cirros-0.3.5-x86_64-disk.img','/home/gabriele/Scaricati/config_cirros.img')
    
    xml=''
    with open(xml_file, "r") as file:  
        xml = file.read()
    hypervisor_connection.defineXML(xml)
    virtual_machine = hypervisor_connection.lookupByName("cirros_py")
    virtual_machine.create()


    xml_file = virt_utils.generate_domain_configuration("ubuntu_py",uuid.uuid4().urn[9:],2048,2,virt_utils.randomMAC(),'br0','/home/gabriele/Scaricati/xenial-server-cloudimg-amd64-disk1.img','/home/gabriele/Scaricati/config_ubuntu.img')
    
    xml=''
    with open(xml_file, "r") as file:  
        xml = file.read()
    hypervisor_connection.defineXML(xml)
    virtual_machine = hypervisor_connection.lookupByName("ubuntu_py")
    virtual_machine.create()  




if __name__=='__main__':
    main()


