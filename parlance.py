#!/usr/bin/env python

# TODO parLANce 
import sys
import socket
import threading
import struct
import urwid
import cPickle as pickle


# TODO change addresses
MULTICAST_GROUP_IP = "224.0.0.1" 
#MULTICAST_GROUP_IP = "224.6.8.11"
#MULTICAST_GROUP_IP = "224.0.0.252" 
MULTICAST_PORT = 9842


class ChatMessage(object):
    def __init__(self, username, text):
        self.username = username
        self.text = text

    @classmethod
    def from_pickled(cls, pickled_msg):
        # TODO review
        return pickle.loads(pickled_msg)

    def pickle(self):
        return pickle.dumps(self) 

    def __str__(self):
        return "%s : %s" % (self.username, self.text)



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
        self.start_receiving_messages()

    def setup_socket_send(self):
        if self._sock_send is None:
            # UDP socket
            self._sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)#, socket.IPPROTO_UDP)
            # time to live (restrict to local area network)
            self._sock_send.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        return self._sock_send
    
    def setup_socket_recv(self):
        if self._sock_recv is None:
            # UDP socket
            self._sock_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)#, socket.IPPROTO_UDP)
            # enable reuse
            self._sock_recv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # 4 chars followed by long 
            mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP_IP), socket.INADDR_ANY)
            # add as member of multicast group
            self._sock_recv.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        return self._sock_recv

    def start_receiving_messages(self):
        sock = self.setup_socket_recv()
        sock.bind((MULTICAST_GROUP_IP, MULTICAST_PORT))
        t = threading.Thread(target=self.receive_messages, args=(sock,))
        t.daemon = True
        t.start()

    def receive_messages(self, sock):
        while True:
            # TODO change buffer size
            pickled_msg = sock.recv(1024)
            message = ChatMessage.from_pickled(pickled_msg)
            # TODO dont display messages from self
            self.view.add_message(message)
            #if message:
                #print message.username, ':', message.text

    def send_msg(self, text):
        msg = ChatMessage(self.username, text)
        sock = self.setup_socket_send()
        sock.sendto(msg.pickle(), (MULTICAST_GROUP_IP, MULTICAST_PORT))
        return msg


class ChatView(object):
    def __init__(self, chat_controller):
        self.chat_controller = chat_controller
        self.chat_controller.view = self
        self.messages = []
        self.init_widgets()
        
    def init_widgets(self):
        self.message_widget = urwid.Text('')
        self.input_widget = urwid.Edit("> ")
        self.frame_widget = urwid.Frame(
                body = urwid.Filler(self.message_widget, valign='top'),
                footer = self.input_widget,
                focus_part = 'footer')
        self.loop = urwid.MainLoop(self.frame_widget, unhandled_input=self.handle_input)

    def handle_input(self, key):
        if key == 'enter':
            text = self.input_widget.edit_text
            if len(text) > 0:
                if text == ':q':
                    raise urwid.ExitMainLoop()
                message = self.chat_controller.send_msg(text)
                self.input_widget.set_edit_text('')

    def add_message(self, message):
        self.messages.append(message)

    def show(self):
        self.loop.set_alarm_in(0.25, self.paint)
        self.loop.run()

    def paint(self, loop, user_data):
        self.show_messages()
        loop.set_alarm_in(0.25, self.paint)
                
    def show_messages(self):
        #print("[%s] : %s" % (message.username, message.text))
        #print self.message_widget.sizing()
        #print self.message_widget.rows((10,))

        #message_text = '\n'.join([str(m) for m in self.messages])
        #self.message_widget.set_text(message_text)

        while True:
            try:
                message = self.messages.pop(0)
                if message is not None:
                    self.message_widget.set_text(self.message_widget.text + '\n' + str(message))
            except IndexError:
                break

    
    


def main():
    # TODO use argparse
    args = sys.argv[:] # copy
    if len(args) == 2:
        username = args.pop()
        chat_controller = ChatController(username)
        chat_view = ChatView(chat_controller)
        chat_view.show()
    else:
        print 'Usage: chat username'

if __name__ == '__main__':
    main()