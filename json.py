import ujson as json

class config():

    def __init__(self, file):
        self.config_file = file
        if self.config_file == None:
            print("No Config File provided!")
        else:
            self.data = self.ReadContent()
            self.jsonData = json.loads(self.data)
            #print(self.data)
    
    def IsJson(self, data):
        try:
            json.loads(data)
        except ValueError as e:
            return False
        return True

    def WriteContent(self, content):
        try:
            f = open(str(self.config_file), "w")
            try:
                f.write(content)
            finally:
                f.close()
        except OSError:
            print ('oops!')

    def ReadContent(self):
        try:
            f = open(str(self.config_file), "r")
            try:
                return str(f.readlines()[0])
            finally:
                f.close()
        except OSError:
            print ('oops!')

    def GetContent(self, first):
        return self.jsonData[str(first)]
    
    def WriteValue(self, first, value):
        self.jsonData[first] = value
        self.WriteContent(str(json.dumps(self.jsonData)))

    def WriteAllContent(self, newdata):
        data = json.loads(newdata)
        changes = False
        for key in data.keys():
            value = data[key] 
            if key not in self.jsonData:
                print("found new key {0} with value {1}".format(key, value))
            else:
                if self.jsonData[key] != value: 
                    changes = True
                    print("new value %s for key %s " % (value, key))
                    self.jsonData[key] = value
        if changes:
            self.WriteContent(str(json.dumps(self.jsonData)))
        else:
            print("nothing changed - not writing to json-file")
