
def create_vm_start_file(name,address,image_file,ram_size):
    template="nohup kvm -name %s -hda %s -m %sd -net bridge,br=s1-br0,name=br0 -net nic,name=ens3,macaddr=%s > /dev/null 2>&1 & echo $! > %s.pid"

    data=str(template % (name,ram_size,image_file,address,name))
    file_name=str("%.sh" % name)
    with open(file_name,'wb') as f:
        f.write(data)
    return file_name
