import sys
from client_cli import *
from server import *

if len(sys.argv) > 1 and sys.argv[1] == 'server':
  server = Server()
  server.start(8015)
else:
  cli = ClientCli()
  cli.main('localhost', 8015)

