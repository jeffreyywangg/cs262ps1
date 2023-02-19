import sys, socket
import time
import threading
from threading import Lock, Event
import re
import uuid
from wireprotocol import *

class Server:
  mutex = Lock()
  client_messages: dict[str, list[str]] = {}
  client_passwords: dict[str, str] = {}
  client_tokens: dict[str, bytes] = {}
  client_sockets: dict[str, socket.socket] = {}
  sockets_watchdog: dict[socket.socket, float] = {}

  def send_body(self, s, action, body):
    """
    Server-specific method to send a body to the client.
    """
    try:
      send_sized_int(s, 0, 1)
    except:
      print("ERROR - Connection lost to client.")
      del self.sockets_watchdog[s]

    send_sized_int(s, action, 1)
    send_sized_int(s, len(body), 4)
    s.send(body)

  def send_error(self, s, action):
    """
    Server-specific method to send that an error occurred to the client.
    """
    try:
      send_sized_int(s, 0, 1)
    except:
      print("ERROR - Connection lost to client.")
      del self.sockets_watchdog[s]

    send_sized_int(s, action, 1)
    send_sized_int(s, 0, 4)

  def check_authentication(self, s):
    token = receive_sized(s, 16)
    for username in self.client_tokens:
      if self.client_tokens[username] == token:
        return username

  def watchdog(self):
    """
    Poll threads for closure
    Spawn a new thread, and poll.
    """
    while True:
      time.sleep(5)
      to_remove = []
      for s in self.sockets_watchdog:
        timediff: float = time.time() - self.sockets_watchdog[s]
        # Kill sockets that are idle for more than X seconds
        if timediff > 120:
          print(f"Shutting down socket {str(s)}")
          s.shutdown(socket.SHUT_RDWR)
          s.close()
          to_remove.append(s)

      self.mutex.acquire()
      for r in to_remove:
        del self.sockets_watchdog[r]
      self.mutex.release()

  def server_client_loop(self, s):
    while True:
      if s not in self.sockets_watchdog:
        return

      version = receive_sized_int(s, 1)
      print('Incoming message...')

      self.mutex.acquire()
      self.sockets_watchdog[s] = time.time()
      self.mutex.release()

      if version == 0:
        action = receive_sized_int(s, 1)
        print(f'Received action {action}.')

        if action == 1:
          # Authenticate
          size = receive_sized_int(s, 4)
          body = receive_sized_string(s, size)

          index_colon = body.index(':')
          username = body[:index_colon]
          password = body[index_colon+1:]

          if username in self.client_messages:
            if self.client_passwords[username] == password:
              self.client_sockets[username] = s
              self.send_body(s, 10, self.client_tokens[username])
              print(f'User {username} logged in successfully.')
            else:
              self.send_error(s, 10)
              print(f'User {username} failed to login.')
          else:
            if re.match('^[a-z_]+$', username) and len(password) > 0:
              self.mutex.acquire()
              self.client_sockets[username] = s
              self.client_messages[username] = []
              self.client_passwords[username] = password
              self.client_tokens[username] = uuid.uuid4().bytes
              self.mutex.release()
              self.send_body(s, 10, self.client_tokens[username])
              print(f'User {username} created successfully.')
            else:
              self.send_error(s, 10)
              print(f'User {username} failed to sign up.')
        elif action == 2:
          # List
          size = receive_sized_int(s, 4)
          body = receive_sized_string(s, size)
          username = self.check_authentication(s)

          if not username:
            self.send_error(s, 10)
            continue

          if body == "\n":
            print("No regex received from client. Returning all account usernames.")
            self.send_body(s, 10, bytes(','.join(self.client_messages.keys()), 'utf-8'))
          else:
            try:
              pattern = re.compile(body)
              matches = []
              for uname in self.client_messages.keys():
                if pattern.match(uname):
                  matches.append(uname)
              self.send_body(s, 10, bytes(','.join(matches), 'utf-8'))
              print('Sent usernames matching regex.')
            except re.error:
              self.send_error(s, 10)
        elif action == 3:
          # Send
          size = receive_sized_int(s, 4)
          body = receive_sized_string(s, size)
          username = self.check_authentication(s)

          if not username:
            self.send_error(s, 10)
            continue

          index = body.index(':')
          username = body[0:index]
          text = body[index+1:]

          if username not in self.client_messages:
            self.send_error(s, 10)
          else:
            self.mutex.acquire()
            self.client_messages[username].append(text)
            self.mutex.release()
            self.send_body(s, 10, ZERO_BYTE)
            print('Sent message.')
        elif action == 4:
          # Deliver
          size = receive_sized_int(s, 4)
          body = receive_sized_string(s, size)
          username = self.check_authentication(s)

          if not username:
            self.send_error(s, 10)
            continue

          if body not in self.client_messages:
            self.send_error(s, 10)
          else:
            for message in self.client_messages[body]:
              if body in self.client_sockets:
                print(f'Delivering message to {body}.')
                self.send_body(self.client_sockets[body], 11, bytes(message, 'utf-8'))

            self.mutex.acquire()
            self.client_messages[body] = []
            self.mutex.release()

            self.send_body(s, 10, ZERO_BYTE)
            print('Delivered messages.')
        elif action == 5:
          # Delete
          size = receive_sized_int(s, 4)
          body = receive_sized_string(s, size)
          username = self.check_authentication(s)

          if not username:
            self.send_error(s, 10)
            continue

          self.mutex.acquire()
          del self.client_messages[body]
          del self.client_sockets[body]
          del self.client_passwords[body]
          del self.client_tokens[body]
          self.mutex.release()

          self.send_body(s, 10, ZERO_BYTE)
          print(f'Deleted account for {username}.')

  def start(self, port):
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(('', port))
    serversocket.listen()

    threading.Thread(target=self.watchdog, daemon=True).start()

    while True:
      s, _ = serversocket.accept()
      self.mutex.acquire()
      self.sockets_watchdog[s] = time.time()
      self.mutex.release()
      threading.Thread(target=self.server_client_loop, args=(s,)).start()
