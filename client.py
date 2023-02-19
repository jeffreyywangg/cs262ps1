import sys, socket
import time
import threading
from threading import Lock, Event
import re
from wireprotocol import *

class Client():
  s = None
  auth_token = None
  buffered_messages = []

  def receive_response_from_server(self):
    """Get server response.
    """
    try:
      version = receive_sized_int(self.s, 1)
    except:
      print("\n ERROR - Connection lost to server. Please reboot. \n")
      sys.exit(1)

    action = receive_sized_int(self.s, 1)
    size = receive_sized_int(self.s, 4)
    body = None
    if size > 0:
      body = receive_sized(self.s, size)

    if action == 11:
      self.buffered_messages.append(str(body, 'utf-8'))
      return self.receive_response_from_server()

    return action, body

  def receive_success_from_server(self):
    action, body = self.receive_response_from_server()
    return body is not None

  def send_action_and_body(self, action, body=None):
    """
    Client-specific method to send an action (with a body, if needed).
    """
    try:
      send_sized_int(self.s, 0, 1)
    except:
      print("\n ERROR - Connection lost to server. Please reboot. \n")
      sys.exit(1)

    send_sized_int(self.s, action, 1)

    if body:
      send_sized_int(self.s, len(body), 4)
      self.s.send(body)

    if self.auth_token:
      self.s.send(self.auth_token)

  def run(self, host, port):
    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.s.connect((host, port))

  def authenticate(self, username, password):
    self.send_action_and_body(1, bytes(username + ':' + password, 'utf-8'))
    response_action, response_body = self.receive_response_from_server()
    self.auth_token = response_body
    return self.auth_token is not None

  def deauthenticate(self):
    self.auth_token = None

  def flush_messages(self):
    temp_messages = self.buffered_messages
    self.buffered_messages = []
    return temp_messages


