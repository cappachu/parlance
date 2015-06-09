#!/usr/bin/env python

import sys
import socket
import threading
import struct
from blessings import Terminal
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
MULTICAST_GROUP_IP = "224.0.0.1" 
#MULTICAST_GROUP_IP = "224.6.8.11"
MULTICAST_PORT = 9842

class ChatController(object):
    def __init__(self, username):
        self.username = username
        self._view = None
        self._sock_send = None
        self._sock_recv = None

    @property
    def view(self):
        return self._view

    @view.setter
    def view(self, value):
        self._view = value
        self.display()

    def setup_socket_send(self):
        if self._sock_send is None:
            self._sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self._sock_send.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        return self._sock_send
    
    def setup_socket_recv(self):
        if self._sock_recv is None:
            self._sock_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self._sock_recv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # TODO verify "4sl"
            mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP_IP), socket.INADDR_ANY)
            self._sock_recv.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        return self._sock_recv


    def display(self):
        sock = self.setup_socket_recv()
        sock.bind((MULTICAST_GROUP_IP, MULTICAST_PORT))
        t = threading.Thread(target=self.display_messages, args=(sock,))
        t.daemon = True
        t.start()

    def display_messages(self, sock):
        while True:
            # TODO change buffer size
            pickled_msg = sock.recv(1024)
            message = Message.from_pickled(pickled_msg)
            # TODO dont display messages from self
            self.view.add_message(message)
            #if message:
                #print message.username, ':', message.text

    def send_msg(self, text):
        msg = Message(self.username, text)
        sock = self.setup_socket_send()
        sock.sendto(msg.pickle(), (MULTICAST_GROUP_IP, MULTICAST_PORT))
        return msg

class ChatView(object):
    def __init__(self, chat_controller):
        self.chat_controller = chat_controller
        self.messages = []
        self.term = Terminal()
        self.chat_controller.view = self

    def add_message(self, message):
        self.messages.append(message)
        self.paint()

    def show(self):
        self.paint()
        while True:
            self.show_prompt()

    def show_prompt(self):
        with self.term.location(0, self.term.height - 1):
            text = raw_input("> ")
            if len(text) > 0:
                message = self.chat_controller.send_msg(text)
                # TODO add_message ?
                self.add_message(message)
                
                
    def show_messages(self):
        for message in self.messages:
            print("[%s] : %s" % (message.username, message.text))

    def paint(self):
        self.show_messages()
        # move cursor to input line


    


def main():
    args = sys.argv[:] # copy
    if len(args) == 2:
        username = args.pop()
        chat_controller = ChatController(username)
        chat_view = ChatView(chat_controller)
        chat_view.show()
        
        #if app_type == 'send':
            #while True:
                #msg_text = raw_input("> ")
                #controller.send_msg(msg_text)
        #elif app_type == 'recv':
            #controller.view = None
    else:
        print 'Usage: chat username'

if __name__ == '__main__':
    main()
