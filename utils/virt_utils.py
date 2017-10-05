import libvirt
from jinja2 import Environment, FileSystemLoader
import random

#sudo dnsmasq -d  --interface=br0 --bind-interfaces  --dhcp-range=192.168.123.2,192.168.123.254 --listen-address 192.168.123.1
# creare br0 - brctl addbr br0
# uppadre br0 - ifconfig br0 up
# assegnare ip br0 - ifconfig br0 192.168.123.1 netmask 255.255.255.0
# condivisone connessione iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE


def randomMAC():
	mac = [ 0x00, 0x16, 0x3e,
		random.randint(0x00, 0x7f),
		random.randint(0x00, 0xff),
		random.randint(0x00, 0xff) ]
	return ':'.join(map(lambda x: "%02x" % x, mac))

def read_file(filename):
    with open(filename, 'r') as myfile:
        data=myfile.read().replace('\n', '')
    return data

#t=template.render(domain_name='prova',vm_uuid='1231491',vm_ram=2049,cpu=1,disk='test.img',config_disk='test2.img',vm_mac='00:11:22:33:44:55',bridge_name='br0')
def generate_domain_configuration(domain_name,domain_uuid,vm_ram,vm_cpu,vm_mac,bridge_name,disk,config_disk):
    env = Environment(loader=FileSystemLoader('utils/template'))
    template = env.get_template('vm_template.xml')
    
    output_from_parsed_template = template.render(domain_name=domain_name,vm_uuid=domain_uuid,vm_ram=vm_ram,cpu=vm_cpu,disk=disk,config_disk=config_disk,vm_mac=vm_mac,bridge_name=bridge_name)
    
    filename= str('%s.xml') % domain_uuid
    with open(filename, "w") as fh:
        fh.write(output_from_parsed_template)

    return filename

def connect():
    connection = libvirt.open("qemu:///system")
    return connection

