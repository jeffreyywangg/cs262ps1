import sys, socket
import threading

def server(port):
  serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  serversocket.bind(('', port))
  serversocket.listen()

  server_messages = {}
  server_client_sockets = {}

  def server_client_handler(s):
    while True:
      version = receive_sized_int(s, 1)
      print('Version:', version)
      if version == 0:
        action = receive_sized_int(s, 1)
        print('Action:', action)
        if action == 1:
          # Create
          size = receive_sized_int(s, 4)
          body = receive_sized_string(s, size)

          if body in server_messages:
            print('Already has account.')
          elif ',' in body:
            print('Invalid username.')
          else:
            server_messages[body] = []
            server_client_sockets[body] = s
        elif action == 2:
          # List
          pass
        elif action == 3:
          # Send
          size = receive_sized_int(s, 4)
          body = receive_sized_string(s, size)
          index = body.index(',')
          username = body[0:index]
          text = body[index+1:]
          server_messages[username].append(text)
        elif action == 4:
          # Deliver
          size = receive_sized_int(s, 4)
          body = receive_sized_string(s, size)
          server_client_sockets[body].send(bytes(','.join(server_messages[body]), 'utf-8'))
        elif action == 5:
          # Delete
          size = receive_sized_int(s, 4)
          body = receive_sized_string(s, size)
          del server_messages[body]
          del server_client_sockets[body]

  while True:
    s, _ = serversocket.accept()
    threading.Thread(target=server_client_handler, args=(s,)).start()

def client(host, port):
  def send_action(s, action, body=None):
    send_sized_int(s, 0, 1)
    send_sized_int(s, action, 1)

    if body:
      send_sized_int(s, len(body), 4)
      s.send(body)

  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.connect((host, port))

  send_action(s, 1, b"test")
  send_action(s, 2)
  send_action(s, 3, b"test,this is a test message")
  send_action(s, 4, b"test")

def receive_sized_int(s, size):
  return int.from_bytes(receive_sized(s, size), 'big')

def receive_sized_string(s, size):
  return receive_sized(s, size).decode('utf-8')

def receive_sized(s, size):
  combined = b''

  while True:
    msg = s.recv(size)
    combined += msg
    if len(combined) >= size:
      return combined

def send_sized_int(s, num, size):
  s.send(num.to_bytes(size, 'big'))

if sys.argv[1] == 'server':
  server(8000)
else:
  client('localhost', 8000)
