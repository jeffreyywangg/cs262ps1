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

class ServerServicer(service_pb2_grpc.MessageServiceServicer):
  mutex = Lock()
  client_messages: dict[str, list[str]] = {}
  client_passwords: dict[str, str] = {}
  client_tokens: dict[str, bytes] = {}

  def check_authentication(self, request):
    for username in self.client_tokens:
      if self.client_tokens[username] == request.token:
        return username

  def Authenticate(self, request, context):
    username = request.username
    password = request.password
    if username in self.client_messages:
      if self.client_passwords[username] == password:
        print(f'User {username} logged in successfully.')
        return service_pb2.StringResponse(success=True, response=self.client_tokens[username])
      else:
        print(f'User {username} failed to login.')
        return service_pb2.StringResponse(success=False, response="")
    else:
      if re.match('^[a-zA-Z_]+$', username) and len(password) > 0:
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
    if not self.check_authentication(request):
      return service_pb2.StringResponse(success=False, response="")

    body = request.request
    if body == "\n":
      print("No regex received from client. Returning all account usernames.")
      return service_pb2.StringResponse(success=True, response=','.join(self.client_messages.keys()))
    else:
      try:
        pattern = re.compile(body)
        matches = []
        for uname in self.client_messages.keys():
          if pattern.match(uname):
            matches.append(uname)
        return service_pb2.StringResponse(success=True, response=','.join(matches))
        print('Sent usernames matching regex.')
      except re.error:
        return service_pb2.StringResponse(success=False, response="")

  def Send(self, request, context):
    if not self.check_authentication(request):
      return service_pb2.EmptyResponse(success=False)

    if request.username not in self.client_messages:
      return service_pb2.EmptyResponse(success=False)
    else:
      self.mutex.acquire()
      self.client_messages[username].append(text)
      self.mutex.release()
      print('Sent message.')
      return service_pb2.EmptyResponse(success=True)

  def Deliver(self, request, context):
    matching_username = self.check_authentication(request)
    if not matching_username:
      return service_pb2.StringResponse(success=False, response="")
    return service_pb2.StringResponse(success=True, response="\n\n".join(self.client_messages[matching_username]))

  def Delete(self, request, context):
    if not self.check_authentication(request):
      return service_pb2.EmptyResponse(success=False)

    if request.username not in self.client_messages:
      return service_pb2.EmptyResponse(success=False)

    self.mutex.acquire()
    del self.client_messages[body]
    del self.client_sockets[body]
    del self.client_passwords[body]
    del self.client_tokens[body]
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
