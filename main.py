import sys, socket 
import time
import threading
from threading import Lock, Event
import re
import apputils
import cli_met

from wireprotocol import *

"""
TODO:
GRPC CONSIDERATIONS
- how much easier to write code in one way vs other (grpc vs non)
- how much code do u not need to write
- size of code
- size of buffers
- should have client IDs in the wire protocol
- does grpc hold a new socket for each call or just reuse ? most rpc systems keep a socket open with the client for a while

- CLIENT: 
  - what behavior when user cmd+c's and exits? ANS - SERVER should let that thread idle for a bit before closing it in XX time. 
  - what happens when server suddenly loses connection?
- SERVER: https://stackoverflow.com/questions/9681531/graceful-shutdown-server-socket-in-linux
  - should include decisions like timeouts, how long to hold socket, etc. in eng notebook 
"""

def server(port):

  def send_action(s, body=None):
    """
    Server-specific method to send an action (with a body, if needed). Uses same wire protocol as client, except w/out action.
    """
    try:
      send_sized_int(s, 0, 1)
    except: # connection broken
      print("\n ERROR - Connection lost to client. \n")
      del thread_watchdog[s] # Gracefully handle - delete client information? probably not. 
    
    if body:
      send_sized_int(s, len(body), 4)
      s.send(body)

  def watchdog():
    """
    Poll threads for closure
    Spawn a new thread, and poll.
    """
    while True: # while server is running? 
      print("ping!")
      time.sleep(5) # only poll every 5 seconds
      remove = []
      # print("ping!2")
      for thread in thread_watchdog:
        # print("ping!3")
        timediff: float = time.time() - thread_watchdog[thread]
        # Kill threads that are idle for more than X seconds
        if timediff > 120:
          print(f"Shutting down thread {str(thread)}")
          thread.shutdown(socket.SHUT_RDWR) # TODO how to justify this particular shutdown mode
          thread.close()
          socket_thread_event[thread].set() # kill the thread
          remove.append(thread)

      mutex.acquire()
      for r in remove:
          del thread_watchdog[r]
      mutex.release()

  def graceful_exit():
    """
    Server-side:
    Block all incoming requests
    Read all material
    Process all material
    Close all threads
    Shut down

    TODO: How to invoke?
    """
    pass

  serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  serversocket.bind(('', port))
  serversocket.listen()

  socket_thread_event: dict[socket.socket, threading.Event] = {} 
  server_messages: dict[str, list[str]] = {}              # username -> [pswd, msg 1, msg 2, ...]
  server_client_sockets: dict[str, socket.socket] = {}    # username -> sockets 

  # thread watchdog
  thread_watchdog: dict[socket.socket, float] = {}
  mutex = Lock()

  def server_client_handler(s, e: threading.Event):

    while True:
      
      if e.is_set():
        break
      
      version = receive_sized_int(s, 1)

      mutex.acquire()
      thread_watchdog[s] = time.time()
      mutex.release()

      print('Version:', version)

      if version == 0:
        action = receive_sized_int(s, 1)
        print('Action:', action)
        print(type(action))
        
        if action == -1:
          size = receive_sized_int(s, 4)
          body = receive_sized_string(s, size)
          user, pswd = body.split("\n")[0], body.split("\n")[1]
          if body in server_messages and server_messages[body][0] == pswd:
            send_action(s, bytes('Confirm', 'utf-8')) # can probably be done better
          send_action(s, bytes('Deny', 'utf-8')) # can probably be done better
          
        if action == 0:
          # Check if username alr exists
          size = receive_sized_int(s, 4)
          body = receive_sized_string(s, size)
          if body in server_messages:
            send_action(s, bytes('Exists', 'utf-8')) # can probably be done better
          else:
            send_action(s, bytes('DNE', 'utf-8')) # can probably be done better

        elif action == 1:
          # CREATE or LOGIN
          size = receive_sized_int(s, 4)
          body = receive_sized_string(s, size)
          create, user, password = body.split("\n")[0], body.split("\n")[1], body.split("\n")[2]
          ret_msg = ""

          if user in server_messages:
            if create == "True":
              ret_msg = f'{user} already has an account.\n'
              print(ret_msg)
            else:
              if password == server_messages[user][0]:
                ret_msg = f'Success!'
                print(ret_msg)
              else:
                ret_msg = 'Try again. Incorrect password.'
                print(ret_msg)
          elif '\n' in user or '\n' in password:
            ret_msg = "Invalid username or password. Do not include a newline character.\n"
            print(ret_msg)
          else:
            server_messages[user] = [password]
            server_client_sockets[user] = s
        
            ret_msg = "Account Created!\n"
            print(ret_msg)
          
          send_action(s, bytes(ret_msg, 'utf-8'))

        elif action == 2:
          # List Accts
          size = receive_sized_int(s, 4)
          body = receive_sized_string(s, size)
          acct_str = "Accounts:\n"

          if body == "\n":
            print("No regex received from client. Returning all acct usernames.")
            print(server_messages.keys())
            for k in server_messages.keys():
              acct_str += f"  - {k}\n"
          else:
            try:
              pattern = re.compile(body)
              for uname in server_messages.keys():
                if pattern.match(uname):
                  acct_str = acct_str + "\n" + uname
            except re.error:
              acct_str = "Invalid regex. Try again with a different regex, or without one."
        
          print(acct_str)
          send_action(s, bytes(acct_str, 'utf-8'))

        elif action == 3:
          # Send
          size = receive_sized_int(s, 4)
          body = receive_sized_string(s, size)
          index = body.index('\n')  
          username = body[0:index]
          text = body[index+1:]
          ret_msg = ""

          if username not in server_messages:
            ret_msg = "User doesn't exist!\n"
            server_client_sockets[username].send(bytes(ret_msg, 'utf-8'))
          else:
            server_messages[username].append(text)
            ret_msg = "Message Sent!\n"

          send_action(s, bytes(ret_msg, 'utf-8'))

        elif action == 4:

          # Deliver
          size = receive_sized_int(s, 4)
          body = receive_sized_string(s, size)
          ret_msg = ""

          if body not in server_messages:
            ret_msg = "This account does not exist. Please create an account to receive messages."
          elif len(server_messages[body]) == 1:
            ret_msg = "There are no pending messages for this account."
          else:
            for i in range(1, len(server_messages[body])):
              ret_msg += "\n-------------\n"
              ret_msg += server_messages[body][i]
              ret_msg += "-------------\n"

            # Clear
            pswd = server_messages[body][0]
            server_messages[body] = [pswd]

          print(ret_msg)
          send_action(s, bytes(ret_msg, 'utf-8'))

        elif action == 5:
          # Delete
          size = receive_sized_int(s, 4)
          body = receive_sized_string(s, size)
          del server_messages[body]
          del server_client_sockets[body]
          
          ret_msg = "Account Deleted!\n"
          print("Account Deleted!\n")
          send_action(s, bytes(ret_msg, 'utf-8'))

  while True:
    s, _ = serversocket.accept()
    mutex.acquire()
    thread_watchdog[s] = time.time()
    mutex.release()
    event = Event()
    socket_thread_event[s] = event
    threading.Thread(target=server_client_handler, args=(s, event)).start()
    threading.Thread(target=watchdog, daemon=True).start()

def client(host, port):

  s = cli_met.bootup(host, port)
  apputils.print_progress_bar("Connecting to server")
  valid_responses = ["H", "0", "1", "2", "3", "4", "5", "6"]
  signed_in_user = ""
  
  response = cli_met.user_query()
  firstTime = True

  while response in valid_responses:

    if firstTime:
      firstTime = False
    else:
      disp_msg = "Take your next action. Press H to get the directions again. "
      response = cli_met.user_query(disp_msg)
      
    if response == "H":
      response = cli_met.user_query()
      
    if response == "0" or response == "1":
      # LOGIN or SIGNIN to acct

      if len(signed_in_user) > 0:
        logout = cli_met.logout_confirm(signed_in_user)
        if logout == "Y":
          print(f"Logging out of {signed_in_user}...")
          time.sleep(0.1)
          signed_in_user = ""
          continueFlag, uname = cli_met.create_login_logic(response, s)

          if not continueFlag:
            signed_in_user = uname
        else:
          print("Staying logged in.\n")
          continue
      else:
        continueFlag, uname = cli_met.create_login_logic(response, s)
        if not continueFlag:
          signed_in_user = uname
      if continueFlag:
        continue

    elif response == "2":
      cli_met.list_users(s)

    elif response == "3":
      cli_met.send_msg(s, signed_in_user)
    
    elif response == "4":
      cli_met.get_messages(s, signed_in_user)

    elif response == "5":
      if cli_met.delete_acct(s, signed_in_user):
        signed_in_user = ""

  print("Thanks for visiting the Marco/Jeffrey chat room!")

if sys.argv[1] == 'server':
  server(8013)
else:
  client('localhost', 8013)


