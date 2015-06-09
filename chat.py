#!/usr/bin/env python

import sys
import socket
import threading
import struct
import cPickle as pickle


class Message(object):
    def __init__(self, username, text):
        self.username = username
        self.text = text

    @classmethod
    def from_pickled(cls, pickled_msg):
        # TODO review
        return pickle.loads(pickled_msg)

    def pickle(self):
        return pickle.dumps(self) 


# TODO change addresses
MULTICAST_GROUP_IP = "224.0.0.1" #"224.6.8.11"
MULTICAST_PORT = 9842

class Controller(object):
    def __init__(self, username):
        self.username = username
        self._view = None
        self._sock = None

    @property
    def view(self):
        return self._view

    @view.setter
    def view(self, value):
        self._view = value
        self.display()

    def setup_socket(self):
        if self._sock is None:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP_IP), socket.INADDR_ANY)
            self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        return self._sock


    def display(self):
        sock = self.setup_socket()
        sock.bind((MULTICAST_GROUP_IP, MULTICAST_PORT))
        t = threading.Thread(target=self.display_messages, args=(sock,))
        #t.daemon = True
        t.start()

    def display_messages(self, sock):
        while True:
            # TODO change buffer size
            pickled_msg = sock.recv(1024)
            message = Message.from_pickled(pickled_msg)
            # TODO dont display messages from self
            if message:
                print message.username, ':', message.text

    def send_msg(self, text):
        msg = Message(self.username, text)
        sock = self.setup_socket()
        sock.sendto(msg.pickle(), (MULTICAST_GROUP_IP, MULTICAST_PORT))
        return msg

    


def main():
    args = sys.argv[:] # copy
    if len(args) == 3:
        app_type = args.pop()

        username = args.pop()
        print username
        controller = Controller(username)
        
        if app_type == 'send':
            while True:
                msg_text = raw_input("> ")
                controller.send_msg(msg_text)
        elif app_type == 'recv':
            controller.view = None
    else:
        print 'Usage: chat username'

if __name__ == '__main__':
    main()
