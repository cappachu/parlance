
import urwid
from random import choice

# keep only the last 100 messages
MESSAGE_BUFFER_SIZE = 100

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
