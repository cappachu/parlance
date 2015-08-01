
import json

class ChatMessage(object):
    def __init__(self, username, text):
        self.username = username
        self.text = text

    @classmethod
    def from_json(cls, json_msg):
        """Instantiate ChatMessage from json"""
        decoded = json.loads(json_msg)
        return cls(decoded['username'], decoded['text'])

    def json(self):
        obj_dict = {'username':self.username, 'text':self.text}
        return json.dumps(obj_dict) 

    def __str__(self):
        return "%s : %s" % (self.username, self.text)
