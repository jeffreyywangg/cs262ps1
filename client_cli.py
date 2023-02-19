from wireprotocol import *
from client import *
import socket
import sys
from typing import Tuple

DISP_MSG = "Select from your options:" \
        "\n Enter 1 to create an account or log in." \
        "\n Enter 2 to list current usernames. You will be prompted for a regex (if desired)." \
        "\n Enter 3 to send a message to a recipient. You will be prompted for a user + message." \
        "\n Enter 4 to pull your current undelivered messages." \
        "\n Enter 5 to delete your account. If you have undelivered messages, you can choose to view them." \
        "\n Enter Q to exit the application. \n\nYour choice: "

class ClientCli():
  client = Client()
  signed_in_user = None

  def user_loop(self):
    valid_responses = ["H", "0", "1", "2", "3", "4", "5", "6"]

    firstTime = True
    while True:
      self.client.flush_messages()

      response = None

      if firstTime:
        firstTime = False
        response = self.user_query()
      else:
        disp_msg = "Take your next action. Press H to get the directions again. "
        response = self.user_query(disp_msg)

      if response == "H":
        response = self.user_query()
      elif response == "0" or response == "1":
        if self.signed_in_user:
          logout = self.logout_confirm()
          if logout == "Y":
            print(f"Logging out of {self.signed_in_user}...")
            time.sleep(0.1)
            self.signed_in_user = None

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

    try:
      self.client = Client()
      self.client.run(host, port)
      self.user_loop()
    except socket.error:
      print(f"Error: could not connect to server.")
      sys.exit(1)

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
    if self.client.authenticate(uname, pswd):
      self.signed_in_user = uname
      print('Authentication successful!')
    else:
      print('Error. Please try again.')

  def delete_acct(self):
    """
    Delete acct. Returns true if user goes thru all the way; false if not. Action #5.
    """
    if not self.signed_in_user:
      print("You are not logged in. Please create an account or log in with Option #1.")
      return

    confirm = input("You have asked to delete your account! Are you sure? Enter `Yes` to do so. ")
    if confirm == "Yes":
      self.client.send_action_and_body(5, bytes(self.username, 'utf-8'))
    self.handle_sucess_failure()

  def get_messages(self):
    """
    Get undelivered messages. Action #4.
    """
    if not self.signed_in_user:
      print("You are not logged in. Please create an account or log in with Option #1.\n")
      return

    self.client.send_action_and_body(4, bytes(self.signed_in_user, 'utf-8'))
    self.handle_sucess_failure()

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
    msg_format = f"{uname}:FROM: {self.signed_in_user}\nTO: {uname}\n\nMESSAGE: {msg}\n"
    self.client.send_action_and_body(3, bytes(msg_format, 'utf-8'))
    self.handle_sucess_failure()

  def list_users(self):
    """
    List users. Action #2.
    """
    regex = input("Do you wish to list usernames that match a regex? If so, enter one; if not, hit return. \n")
    if len(regex) == 0:
      self.client.send_action_and_body(2, bytes("\n", 'utf-8'))
    else:
      self.client.send_action_and_body(2, bytes(regex, 'utf-8'))
    _, response = self.client.receive_response_from_server()
    if response:
      print(str(response, 'utf-8'))
    else:
      print('Error.')

  def handle_sucess_failure(self):
    if self.client.receive_success_from_server():
      print("Success!")
    else:
      print("Error.")

