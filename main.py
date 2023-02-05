import sys, socket

def server(port):
  serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  serversocket.bind(('', port))
  serversocket.listen()
  s, _ = serversocket.accept()

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
        # TODO
      elif action == 2:
        # List
        # TODO
        pass
      elif action == 3:
        # Send
        size = receive_sized_int(s, 4)
        body = receive_sized_string(s, size)
        # TODO
      elif action == 4:
        # Deliver
        size = receive_sized_int(s, 4)
        body = receive_sized_string(s, size)
        # TODO
      elif action == 5:
        # Delete
        size = receive_sized_int(s, 4)
        body = receive_sized_string(s, size)
        # TODO

def client(host, port):
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.connect((host, port))

  send_sized_int(s, 0, 1)
  send_sized_int(s, 1, 1)

  data = b'examplee'
  send_sized_int(s, len(data), 4)
  s.send(data)

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
