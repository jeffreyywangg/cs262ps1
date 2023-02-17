from wireprotocol import *
import socket
import sys
from typing import Tuple

DISP_MSG = "Select from your options: \n Enter 0 to login to an account. You will need a user + pswd." \
                "\n Enter 1 to create an account. You will be prompted for a username" \
                "\n Enter 2 to list current usernames. You will be prompted for a regex (if desired)." \
                "\n Enter 3 to send a message to a recipient. You will be prompted for a user + message." \
                "\n Enter 4 to pull your current undelivered messages." \
                "\n Enter 5 to delete your account. If you have undelivered messages, you can choose to view them." \
                "\n Enter anything else to exit the application. It will make Jeffrey sad :(\n\nYour choice: " 

def listen_server_response(s: socket.socket):
    """Get server response.
    """
    try:
        version = receive_sized_int(s, 1)
    except:
        print("\n ERROR - Connection lost to server. Please reboot. \n")
        sys.exit(1)

    size = receive_sized_int(s, 4)
    body = receive_sized_string(s, size)
    return(body)


def send_action(s, action, body=None):
    """
    Client-specific method to send an action (with a body, if needed). 
    """
    try:
        send_sized_int(s, 0, 1)
    except:
        print("\n ERROR - Connection lost to server. Please reboot. \n")
        sys.exit(1)
    send_sized_int(s, action, 1)

    if body:
        send_sized_int(s, len(body), 4)
        s.send(body)

def bootup(host, port):
    """Initial bootup sequence and server connect for the client. 
    """
    # Bootup
    response: str = input("Welcome to the Marco-Jeffrey Chat App! Press 1 to continue. Press 0 to quit. ")
    while response != "1" and response != "0":
        response: str = input("Oops! You are incapable of following simple directions. Press 1 to continue. Press 0 to quit. ")
    if response == "0":
        sys.exit(0)

    # Connect to server 
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
    except socket.error:
        print(f"Error - server not initialized?") # might be other errors
        sys.exit(1)
    
    return s

def user_query(msg: str=DISP_MSG) -> str:
    return input(msg)

def logout_confirm(signed_in_user: str) -> str:
    return input(f"You are currently logged in as {signed_in_user}. Are you sure you want to log out? Enter Y if you do, anything else to stay. ")

def get_username(login=True) -> str:
    """
    Get username and return it. Slightly different behavior for login vs non-login modes.
    """
    if login:
        return input("Enter a username: \n")
    else:
        uname = input("Enter a username: \n")
        satisfied = input(f"Your input username is {uname}. If you want to re-enter, enter 1. Otherwise, if satisfied, enter anything else. ")
        # Get good uname
        while satisfied == "1":
            uname = input("Enter a username: \n")
            satisfied = input(f"Your input username is {uname}. If you want to re-enter, enter 1. Otherwise, if satisfied, enter anything else. ")

        return uname

def get_password(login=True) -> str:
    """
    Get password and return it. Slightly different behavior for login vs non-login modes.
    """
    if login:
        return input("Enter a password: \n")
    else:
        pswd = input("Enter a password: \n")
        satisfied = input(f"Your input password is {pswd}. If you want to re-enter, enter 1. Otherwise, if satisfied, enter anything else. ")
        # Get good uname
        while satisfied == "1":
            pswd = input("Enter a password: \n")
            satisfied = input(f"Your input username is {pswd}. If you want to re-enter, enter 1. Otherwise, if satisfied, enter anything else. ")

        return pswd

def create_login_logic(response: str, s: socket.socket) -> Tuple[bool, str]:
    """
    Main method to handle login logic.
    """

    uname = get_username()  # get username
    continueFlag = False    # in instances of failure (password wrong/already logged in/account DNE), continue in main event loop.

    # Confirm existence of acct
    send_action(s, 0, bytes(uname, 'utf-8'))
    status = listen_server_response(s)

    if status == "Exists": # account exists

        if response == "1": # create an acct
            print("Account already exists. Try again.\n")
            continueFlag = True
        else: # prompt for pswd login
            pswd = get_password(login=True)
            ret_str = f"False\n{uname}\n{pswd}"
            send_action(s, 1, bytes(ret_str, 'utf-8'))

            retmsg = listen_server_response(s) # check if password is right
            if retmsg == 'Try again. Incorrect password.':
                continueFlag = True

            print(retmsg + "\n")
    else: # account DNE

        if response == "1": # create an acct
            pswd = get_password(login=False)
            ret_str = f"True\n{uname}\n{pswd}"
            send_action(s, 1, bytes(ret_str, 'utf-8'))

            retmsg = listen_server_response(s) # check if password is right
            if retmsg == 'Try again. Incorrect password.':
                continueFlag = True
            
            print(retmsg + "\n")
        else: # prompt for pswd login
            print("Account does not exist. Please create an account or login to a different account.\n")
            continueFlag = True
    
    return continueFlag, uname

def delete_acct(s: socket.socket, signed_in_user: str) -> bool:
    """
    Delete acct. Returns true if user goes thru all the way; false if not. Action #5. 
    """
    signed_in_user = ""
    if len(signed_in_user) == 0:
        print("You are not logged in. Please create an account or log in with Option #1.")
        return False

    confirm = input("You have asked to delete your account! Are you sure? Enter `Yes` to do so. ")
    if confirm == "Yes":
        view = input("Do you want to view your messages? Press 1 to view and return to not. ")
        if view == "1":
            print(send_action(s, 4, bytes(signed_in_user, 'utf-8')))
            return False
        else:
            print(send_action(s, 5, bytes(signed_in_user, 'utf-8')))
            return True

def get_messages(s: socket.socket, signed_in_user: str):
    """
    Get undelivered messages. Action #4. 
    """
    if len(signed_in_user) == 0:
        print("You are not logged in. Please create an account or log in with Option #1.\n")
    else:
        print(send_action(s, 4, bytes(signed_in_user, 'utf-8')))
        print(listen_server_response(s))

def send_msg(s: socket.socket, signed_in_user: str):
    """
    Send a message. Action #3. 
    """
    if len(signed_in_user) == 0:
        print("You need to create a user before you can send messages.")
    else:
        uname = input("Enter a username to send a message to: \n")
        satisfied = input(f"You will send a message to {uname}. If you want to re-enter, enter 1. Otherwise, if satisfied, enter anything else. ")
        while satisfied == "1":
            uname = input("Enter a username: \n")
            satisfied = input(f"You will send a message to {uname}. If you want to re-enter, enter 1. Otherwise, if satisfied, enter anything else. ")
        
        msg = input("Enter a message: \n")
        msg_format = f"{uname}\nFROM: {signed_in_user}\nTO: {uname}\n\nMESSAGE: {msg}\n"
        send_action(s, 3, bytes(msg_format, 'utf-8'))
    print(listen_server_response(s))

def list_users(s: socket.socket):
    """
    List users. Action #2.
    """
    regex = input("Do you wish to list usernames that match a regex? If so, enter one; if not, hit return. \n")
    if len(regex) == 0:
        send_action(s, 2, bytes("\n", 'utf-8')) # TODO - this is hacky, it won't work without adding SOME string
    else:
        send_action(s, 2, bytes(regex, 'utf-8'))
    print(listen_server_response(s))