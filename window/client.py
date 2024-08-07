import socket
import threading
import tkinter as tk
from tkinter import simpledialog

# Server code
class ChatServer:
    def __init__(self, host='0.0.0.0', port=12345):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(5)
        self.clients = {}
        self.chatrooms = {}

    def broadcast(self, message, chatroom):
        for client in self.chatrooms.get(chatroom, []):
            client.send(message.encode())

    def handle_client(self, client, address):
        client.send("USERNAME:".encode())
        username = client.recv(1024).decode()
        client.send("CHATROOM:".encode())
        chatroom = client.recv(1024).decode()
        ip_username = f"{address[0]}:{username}"

        if chatroom not in self.chatrooms:
            self.chatrooms[chatroom] = []
        self.chatrooms[chatroom].append(client)
        self.broadcast(f"{ip_username} has entered the chatroom.", chatroom)
        
        while True:
            try:
                message = client.recv(1024).decode()
                if message:
                    self.broadcast(f"{ip_username}: {message}", chatroom)
                else:
                    client.close()
                    self.chatrooms[chatroom].remove(client)
                    self.broadcast(f"{ip_username} has left the chatroom.", chatroom)
                    break
            except:
                continue

    def start(self):
        print("Server started...")
        while True:
            client, address = self.server.accept()
            threading.Thread(target=self.handle_client, args=(client, address)).start()

# Client code
class ChatClient:
    def __init__(self, host='127.0.0.1', port=12345):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))

        self.root = tk.Tk()
        self.root.title("Chat Room")

        self.chat_log = tk.Text(self.root, state='disabled', width=50, height=20)
        self.chat_log.pack()

        self.message_entry = tk.Entry(self.root, width=50)
        self.message_entry.pack()
        
        self.send_button = tk.Button(self.root, text="Send", command=self.send_message)
        self.send_button.pack()

        threading.Thread(target=self.receive_messages).start()

        self.username = simpledialog.askstring("Username", "Enter your username:")
        self.client.send(self.username.encode())
        self.chatroom = simpledialog.askstring("Chatroom", "Enter the chatroom number:")
        self.client.send(self.chatroom.encode())

    def send_message(self):
        message = self.message_entry.get()
        self.client.send(message.encode())
        self.message_entry.delete(0, tk.END)

    def receive_messages(self):
        while True:
            try:
                message = self.client.recv(1024).decode()
                self.chat_log.config(state='normal')
                self.chat_log.insert(tk.END, message + "\n")
                self.chat_log.config(state='disabled')
                self.chat_log.yview(tk.END)
            except:
                break

    def start(self):
        self.root.mainloop()

# To run the server:
# server = ChatServer()
# server.start()

# To run the client:
client = ChatClient()
client.start()
