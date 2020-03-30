import copy
import time

class GlobalMemory(object):

    def __init__(self):
        self.Token = False
        self.Error = False
        self.DeviceArray = {}

    def WriteMemory(self,Array):
        i = 0
        maxloop = 10
        while i < maxloop:
            if self.Token == False:
                self.Token = True
                self.DeviceArray = self.dict_merge(self.DeviceArray,Array)
                self.Token = False
                break
            else:
                time.sleep(0.1)
                i += 1
            if i == maxloop:
                print("Error, timeout on WriteMemory")


    def dict_merge(self,a, b):

        '''recursively merges dict's. not just simple a['key'] = b['key'], if
        both a and bhave a key who's value is a dict then dict_merge is called
        on both values and the result stored in the returned dictionary.'''
        if not isinstance(b, dict):
            return b

        result = copy.deepcopy(a)

        for k, v in b.items():

            if k in result and isinstance(result[k], dict):
                result[k] = self.dict_merge(result[k], v)
            else:
                result[k] = copy.deepcopy(v)

        return result