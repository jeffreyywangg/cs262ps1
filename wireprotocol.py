"""
The Marco-Jeffrey wire protocol.

Each message looks like this:
[ (1) ] [ (2) ] [ (3) ] [ (4) ]

(1) 1 byte version #
(2) 1 byte action # 
(3) 4 bytes size of body
(4) [size] bytes body
"""

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

