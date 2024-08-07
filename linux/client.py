import socket
import threading
import curses

class ChatClient:
    def __init__(self, host='127.0.0.1', port=12345):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))

        self.username = input("Enter your username: ")
        self.client.send(self.username.encode())
        self.chatroom = input("Enter the chatroom number: ")
        self.client.send(self.chatroom.encode())

        self.screen = curses.initscr()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        self.screen.nodelay(1)
        self.screen.timeout(500)

        threading.Thread(target=self.receive_messages).start()

    def send_message(self, message):
        self.client.send(message.encode())

    def receive_messages(self):
        while True:
            try:
                message = self.client.recv(1024).decode()
                if message:
                    self.screen.addstr(message + "\n", curses.color_pair(1))
                    self.screen.refresh()
            except:
                break

    def start(self):
        while True:
            try:
                message = self.screen.getstr().decode()
                if message:
                    self.send_message(message)
            except:
                pass

try:
    client = ChatClient()
    client.start()
except Exception as e:
    curses.endwin()
    print(e)
