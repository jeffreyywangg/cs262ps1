def receive_sized_int(s, size) -> int:
  return int.from_bytes(receive_sized(s, size), 'big')

def receive_sized_string(s, size) -> str:
  return receive_sized(s, size).decode('utf-8')

def receive_sized(s, size):
  combined = b''

  while True:
    msg = s.recv(size)
    combined += msg
    if len(combined) >= size:
      return combined

def send_sized_int(s, num, size) -> None:
  s.send(num.to_bytes(size, 'big'))

