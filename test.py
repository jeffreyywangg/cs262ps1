import threading
import unittest
from server import *
from client import *

class ClientServersTest(unittest.TestCase):
  def setup_server_and_clients(self, port, client_count):
    server = Server()
    threading.Thread(target=server.start, args=(port,)).start()

    clients = []
    for i in range(client_count):
      client = Client()
      client.run('localhost', port)
      clients.append(client)
    return clients

  def test_signup(self):
    clients = self.setup_server_and_clients(8000, 1)
    self.assertTrue(clients[0].authenticate('test', 'test'))

  def test_list(self):
    clients = self.setup_server_and_clients(8001, 2)
    clients[0].authenticate('test_a', 'test')
    clients[1].authenticate('test_b', 'test')

    clients[0].send_action_and_body(2, b'\n')
    _, response = clients[0].receive_response_from_server()
    self.assertEqual(response, b'test_a,test_b')

  def test_send_deliver(self):
    clients = self.setup_server_and_clients(8002, 2)
    clients[0].authenticate('test_a', 'test')
    clients[1].authenticate('test_b', 'test')

    clients[0].send_action_and_body(3, b'test_b:hello1')
    self.assertTrue(clients[0].receive_success_from_server())

    clients[0].send_action_and_body(3, b'test_b:hello2')
    self.assertTrue(clients[0].receive_success_from_server())

    clients[1].send_action_and_body(4, b'test_b')
    self.assertTrue(clients[1].receive_success_from_server())
    messages = clients[1].flush_messages()
    self.assertEqual(len(messages), 2)
    self.assertEqual(messages[0], 'hello1')
    self.assertEqual(messages[1], 'hello2')

if __name__ == '__main__':
  unittest.main()
