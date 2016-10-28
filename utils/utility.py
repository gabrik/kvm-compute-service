import os
import urllib2
import re

def create_vm_start_file(name,address,image_file,ram_size):
    print 'creating vm file %s %s %s %s' % (name,address,image_file,ram_size)
    os.system('cp %s vm_dir/%s.img' % (image_file,name))

    template="nohup kvm -name %s -hda vm_dir/%s.img -m %s -net bridge,br=s1-br0,name=br0 -net nic,name=ens3,macaddr=%s > vm_dir/%s.out 2>&1 & echo $! > vm_dir/%s.pid"

    data=str(template % (name,name,ram_size,address,name,name))
    file_name=str("vm_dir/%s.sh" % name)
    with open(file_name,'wb') as f:
        f.write(data)
    return file_name


def destroy_vm(name):
    pid_file = str("vm_dir/%s.pid" % name)
    with open(pid_file) as data_file:
        vm_pid=data_file.read().replace('\n','')
    os.system('sudo kill -9 %s' % vm_pid)
    os.system('rm -rf vm_dir/%s.*' % name)



def generate_mac_address(count,uuid):
    # IL MAC DEVE ESSERE IN BASE ALLA ZONA DE:AD:id di zona
    zoneid=uuid[:2]
    initial_bytes=str("DE:AD:%s:" % zoneid)
    last_bytes="%0.6X" % count
    last_bytes=':'.join([last_bytes[i:i+2] for i in range(0, len(last_bytes), 2)])
    return initial_bytes+last_bytes


def get_inet_address_from_mac(controller,mac):
    url=str('http://%s:8080/vsjol/getHostAddress/%s' % (controller,mac))
    ip_regex='\/(.+)'
    
    resp = urllib2.urlopen(url)
    content = resp.read()
    if content!='false':
        ip=re.findall(ip_regex,content)
        return ip[0]
    else:
        return False