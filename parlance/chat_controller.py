
import socket
import struct
import threading
from chat_message import ChatMessage

MULTICAST_GROUP_IP = "224.0.0.1" 
MULTICAST_PORT = 9842
SOCKET_BUFFER_SIZE = 4096

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
