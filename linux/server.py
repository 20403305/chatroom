import socket
import threading

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

# To run the server:
server = ChatServer()
server.start()
