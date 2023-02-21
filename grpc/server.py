import sys, socket
import time
import threading
import re
import uuid
from concurrent import futures
import grpc
import service_pb2
import service_pb2_grpc
from threading import Lock, Event
from typing import List, Dict

class ServerServicer(service_pb2_grpc.MessageServiceServicer):
  mutex = Lock()                              # Lock for all server dictionaries
  client_messages: Dict[str, List[str]] = {}  # {username: [user_msgs]}
  client_passwords: Dict[str, str] = {}       # {username: password}
  client_tokens: Dict[str, bytes] = {}        # {username: authentication_token}

  def check_authentication(self, request):
    """
    Check if user is logged in (with authentication token sent in message).
    """
    for username in self.client_tokens:
      if self.client_tokens[username] == request.token:
        return username

  def Authenticate(self, request, context):
    """
    Authenticate a login, or create an account.
    """
    username = request.username
    password = request.password
    if username in self.client_messages: # if user exists, attempt login.
      if self.client_passwords[username] == password:
        print(f'User {username} logged in successfully.')
        return service_pb2.StringResponse(success=True, response=self.client_tokens[username])
      else:
        print(f'User {username} failed to login.')
        return service_pb2.StringResponse(success=False, response="")
    else: # if user does not exist, attempt account creation.
      if re.match('^[a-zA-Z_]+$', username) and len(password) > 0: # usernames must be alphabetical
        self.mutex.acquire()
        self.client_messages[username] = []
        self.client_passwords[username] = password
        self.client_tokens[username] = str(uuid.uuid4())
        self.mutex.release()
        print(f'User {username} created successfully.')
        return service_pb2.StringResponse(success=True, response=self.client_tokens[username])
      else:
        print(f'User {username} failed to sign up.')
        return service_pb2.StringResponse(success=False, response="")

  def List(self, request, context):
    """
    List accounts, separated by a comma.
    """
    if not self.check_authentication(request):
      return service_pb2.StringResponse(success=False, response="")

    body = request.request
    if body == "\n":
      print("No regex received from client. Returning all account usernames.")
      return service_pb2.StringResponse(success=True, response=', '.join(self.client_messages.keys()))
    else:
      try:
        pattern = re.compile(body)
        matches = []
        for uname in self.client_messages.keys():
          if pattern.match(uname):
            matches.append(uname)
        print('Sent usernames matching regex.')
        return service_pb2.StringResponse(success=True, response=', '.join(matches))
      except re.error:
        return service_pb2.StringResponse(success=False, response="")

  def Send(self, request, context):
    """
    Add a message to someone's undelivered.
    """
    if not self.check_authentication(request):
      return service_pb2.EmptyResponse(success=False)

    if request.username not in self.client_messages:
      return service_pb2.EmptyResponse(success=False)
    else:
      self.mutex.acquire()
      self.client_messages[request.username].append(request.body)
      self.mutex.release()
      print('Sent message.')
      return service_pb2.EmptyResponse(success=True)

  def Deliver(self, request, context):
    """
    Pull user's undelivered messages and send.
    """
    matching_username = self.check_authentication(request)
    if not matching_username:
      return service_pb2.StringResponse(success=False, response="")
    return service_pb2.StringResponse(success=True, response="\n\n".join(self.client_messages[matching_username]))

  def Delete(self, request, context):
    """
    Delete account.
    """
    if not self.check_authentication(request):
      return service_pb2.EmptyResponse(success=False)

    if request.username not in self.client_messages:
      return service_pb2.EmptyResponse(success=False)

    self.mutex.acquire()
    del self.client_messages[request.username]
    del self.client_passwords[request.username]
    del self.client_tokens[request.username]
    self.mutex.release()

    print(f'Deleted account for {request.username}.')
    return service_pb2.EmptyResponse(success=True)

class Server():
  servicer = ServerServicer()

  def start(self, port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_pb2_grpc.add_MessageServiceServicer_to_server(self.servicer, server)
    server.add_insecure_port('[::]:' + str(port))
    server.start()
    server.wait_for_termination()
