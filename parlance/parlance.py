#!/usr/bin/env python

import sys
import argparse
from chat_view import ChatView
from chat_controller import ChatController

# TODO retain focus on input widget on click
# TODO redirect 'up' and 'down' key events to message_widget for scrolling
# TODO display how to quit

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
