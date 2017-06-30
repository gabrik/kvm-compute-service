
import json

class KVMServiceMessage(object):
    def __init__(self,id,value):
        self.id=id
        self.value=json.dumps(value)
    
    def __str__(self):
        return "KVMServiceMessage >> {0} {1}".format(self.id,self.value)

    def toDict(self):
        return {'id':id,'value':value}
