import grpc
import sys
import service_pb2
import service_pb2_grpc
import time

DISP_MSG = "Select from your options:" \
        "\n Enter 1 to create an account or log in." \
        "\n Enter 2 to list current usernames. You will be prompted for a regex (if desired)." \
        "\n Enter 3 to send a message to a recipient. You will be prompted for a user + message." \
        "\n Enter 4 to pull your current undelivered messages." \
        "\n Enter 5 to delete your account." \
        "\n Enter Q to exit the application. \n\nYour choice: "

class ClientCli():
  client = None
  signed_in_user = None
  signed_in_token = None

  def user_loop(self):
    valid_responses = ["H", "0", "1", "2", "3", "4", "5", "6"]

    firstTime = True
    while True:
      response = None

      if firstTime:
        firstTime = False
        response = self.user_query()
      else:
        disp_msg = "Take your next action. Press H to get the directions again. "
        response = self.user_query(disp_msg)

      if response == "H":
        firstTime = True
        continue
      elif response == "0" or response == "1":
        if self.signed_in_user:
          logout = self.logout_confirm()
          if logout == "Y":
            print(f"Logging out of {self.signed_in_user}...")
            time.sleep(0.1)
            self.signed_in_user = None
            self.signed_in_token = None

            self.create_login_logic()
          else:
            print("Staying logged in.\n")
            continue
        else:
          self.create_login_logic()
      elif response == "2":
        self.list_users()
      elif response == "3":
        self.send_msg()
      elif response == "4":
        self.get_messages()
      elif response == "5":
        self.delete_acct()
      elif response == "Q":
        break

  def main(self, host, port):
    """Initial bootup sequence and server connect for the client.
    """
    # Bootup
    response: str = input("Welcome to the chat app! Press 1 to continue. Press 0 to quit. ")
    while response != "1" and response != "0":
      response: str = input("Press 1 to continue. Press 0 to quit. ")
    if response == "0":
      sys.exit(0)

    with grpc.insecure_channel(host + ':' + str(port)) as channel:
      self.client = service_pb2_grpc.MessageServiceStub(channel)
      self.user_loop()

  def user_query(self, msg: str=DISP_MSG) -> str:
    return input(msg)

  def logout_confirm(self) -> str:
    return input(f"You are currently logged in as {self.signed_in_user}. Are you sure you want to log out? Enter Y if you do, anything else to stay. ")

  def get_username(self) -> str:
    return input("Enter a username: \n")

  def get_password(self) -> str:
    return input("Enter a password: \n")

  def create_login_logic(self):
    """
    Main method to handle login logic.
    """

    uname = self.get_username()
    pswd = self.get_password()
    token = self.client.Authenticate(service_pb2.AuthenticateRequest(username=uname, password=pswd)).response
    if token:
      self.signed_in_user = uname
      self.signed_in_token = token
      print('Authentication successful!')
    else:
      print('Error. Please try again.')

  def delete_acct(self):
    if not self.signed_in_user:
      print("You are not logged in. Please create an account or log in with Option #1.")
      return

    confirm = input("You have asked to delete your account! Are you sure? Enter Y to do so, anything else to cancel. ")
    if confirm == "Y":
      self.handle_sucess_failure_response(
        self.client.Delete(service_pb2.DeleteRequest(token=self.signed_in_token, username=self.signed_in_user))
      )
      self.signed_in_user = None
      self.signed_in_token = None

  def get_messages(self):
    """
    Get undelivered messages. Action #4.
    """
    if not self.signed_in_user:
      print("You are not logged in. Please create an account or log in with Option #1.\n")
      return

    response = self.client.Deliver(service_pb2.DeliverRequest(token=self.signed_in_token)).response
    print(response)

  def send_msg(self):
    """
    Send a message. Action #3.
    """
    if not self.signed_in_user:
      print("You need to create a user before you can send messages.")
      return

    uname = input("Enter a username to send a message to: \n")
    satisfied = input(f"You will send a message to {uname}. If you want to re-enter, enter 1. Otherwise, if satisfied, enter anything else. ")
    while satisfied == "1":
      uname = input("Enter a username: \n")
      satisfied = input(f"You will send a message to {uname}. If you want to re-enter, enter 1. Otherwise, if satisfied, enter anything else. ")

    msg = input("Enter a message: \n")
    msg_format = f"{uname}:\nFROM: {self.signed_in_user}\nTO: {uname}\nMESSAGE: {msg}\n"
    self.handle_sucess_failure_response(
      self.client.Send(service_pb2.SendRequest(token=self.signed_in_token, username=uname, body=msg_format))
    )

  def list_users(self):
    """
    List users. Action #2.
    """
    regex = input("Do you wish to list usernames that match a regex? If so, enter one; if not, hit return. \n")
    request_search = regex
    if len(regex) == 0:
      request_search = "\n"
    response = self.client.List(service_pb2.ListRequest(token=self.signed_in_token, request=request_search)).response
    if response:
      print(response)
    else:
      print('Error.')

  def handle_sucess_failure_response(self, response):
    if response and response.success:
      print("Success!")
    else:
      print("Error.")
