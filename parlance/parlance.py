#!/usr/bin/env python

import sys
import argparse
import socket
import threading
import struct
import urwid
import json
from random import choice

# TODO retain focus on input widget on click
# TODO redirect 'up' and 'down' key events to message_widget for scrolling
# TODO display how to quit

MULTICAST_GROUP_IP = "224.0.0.1" 
MULTICAST_PORT = 9842
# keep only the last 100 messages
MESSAGE_BUFFER_SIZE = 100
SOCKET_BUFFER_SIZE = 4096
FOREGROUND_COLORS = ['dark red',
                     'dark green',
                     'brown',
                     'dark blue',
                     'dark magenta',
                     'dark cyan',
                     'light gray',
                     'light red',
                     'light green',
                     'yellow',
                     'light blue',
                     'light magenta',
                     'light cyan',
                     'white',]

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



class ChatController(object):
    """Manages message sending and receiving messages"""
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
        # begin receiveing messages once the view is set
        self.start_receiving_messages()

    def setup_socket_send(self):
        if self._sock_send is None:
            # UDP socket
            self._sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # TTL: time to live (restrict to local area network)
            self._sock_send.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        return self._sock_send
    
    def setup_socket_recv(self):
        if self._sock_recv is None:
            # UDP socket
            self._sock_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)#, socket.IPPROTO_UDP)
            # enable reuse
            self._sock_recv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # 4sl: 4 chars followed by long 
            mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP_IP), socket.INADDR_ANY)
            # add as member of multicast group
            self._sock_recv.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        return self._sock_recv

    def start_receiving_messages(self):
        """Spawn thread to handle receiving messages, called when view is set"""
        sock = self.setup_socket_recv()
        sock.bind((MULTICAST_GROUP_IP, MULTICAST_PORT))
        t = threading.Thread(target=self.receive_messages, args=(sock,))
        t.daemon = True
        t.start()

    def receive_messages(self, sock):
        """Repeatedly check for messages, deserialize and send to view, called when view is set"""
        while True:
            json_msg, address = sock.recvfrom(SOCKET_BUFFER_SIZE)
            message = ChatMessage.from_json(json_msg)
            assert(self.view is not None)
            self.view.add_message(message, address)

    def send_msg(self, text):
        """Send json message"""
        msg = ChatMessage(self.username, text)
        sock = self.setup_socket_send()
        sock.sendto(msg.json(), (MULTICAST_GROUP_IP, MULTICAST_PORT))
        return msg



class ChatView(object):
    """Display messages and provide means for sending messages"""
    def __init__(self, chat_controller):
        self.chat_controller = chat_controller
        self.chat_controller.view = self
        # list of (message, address) tuples received
        self.message_address_pairs = [] 
        self.address_2_color = {}
        # urwid palette list of tuples 
        # containing (display_attr_name, foreground_color, background_color)
        self.palette = [(c,c,'black') for c in FOREGROUND_COLORS]
        self.init_widgets()
        
    def init_widgets(self):
        """Initialize main Frame containing a ListBox (for displaying all messages) 
           and a Edit widget for sending a message"""
        self.message_widget = urwid.ListBox(urwid.SimpleFocusListWalker([]))
        self.input_widget = urwid.Edit("> ")
        self.frame_widget = urwid.Frame(urwid.AttrWrap(self.message_widget, 'body'), 
                footer=self.input_widget,
                focus_part = 'footer')
        self.loop = urwid.MainLoop(self.frame_widget, self.palette, unhandled_input=self.handle_input)

    def handle_input(self, key):
        if key == 'enter':
            text = self.input_widget.edit_text
            if len(text) > 0:
                if text == ':q' or text == ':quit':
                    raise urwid.ExitMainLoop()
                message = self.chat_controller.send_msg(text)
                self.input_widget.set_edit_text('')

    def add_message(self, message, address):
        self.message_address_pairs.append((message, address))

    def show(self):
        """Start main gui loop and repeatedly paint to display new messages"""
        # TODO use select / gevent / thread instead?
        # schedule a callback (self.paint)
        self.loop.set_alarm_in(0.25, self.paint)
        self.loop.run()

    def paint(self, loop, user_data):
        self.show_messages()
        # schedule a callback (self.paint)
        loop.set_alarm_in(0.25, self.paint)
                
    def show_messages(self):
        """Display all messages received so far"""
        while self.message_address_pairs:
            # FIFO: oldest messages first
            message, address = self.message_address_pairs.pop(0)
            if message is not None:
                attr = self.address_2_color.setdefault(address, choice(FOREGROUND_COLORS))
                text_widget = urwid.Text((attr, str(message)))
                # append to the list of widgets (body) of ListBox (message_widget) managed by ListWalker
                self.message_widget.body.append(text_widget)
                # display and store a limited number of messages
                if len(self.message_widget.body) > MESSAGE_BUFFER_SIZE:
                    self.message_widget.body.pop(0)
                # make newest messages visible 
                self.message_widget.focus_position = len(self.message_widget.body) - 1


def main():
    parser = argparse.ArgumentParser(description='Chat with Folks on Your Local Area Network')
    parser.add_argument('username', help='username')
    args = vars(parser.parse_args())
    if not args['username']:
        parser.print_help()
        return
    username = args['username']
    chat_controller = ChatController(username)
    chat_view = ChatView(chat_controller)
    chat_view.show()

if __name__ == '__main__':
    main()
