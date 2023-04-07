import socket
import threading
from client_handler import ClientHandler


SERVER_LISTEN = ("localhost", 56789)
CLIENT_LIST = {}
RELAY_LOCK = threading.Lock()

MESSAGE_SEPARATOR = "/"
MESSAGE_TYPES = {
    "public msg": "pub",
    "private msg": "pri",
    "add user": "add",
    "del user": "del",
    "user list": "lst",
}


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(SERVER_LISTEN)
    server.settimeout(None)
    server.listen(3)
    return server


def get_valid_username(client):
    global CLIENT_LIST, RELAY_LOCK
    #print("WAITING FOR A NAME......")
    try:
        new_user = client.recieve_text_data()
    except ConnectionAbortedError as connerr:
        #print("USER CONNETION ABORTED BEFORE THEY ENTERED A NAME....")
        print(connerr)
        return None
    #print(f"INCOMING NAME: {new_user}")

    with RELAY_LOCK:
        if new_user in CLIENT_LIST or not new_user.isalnum() or (len(new_user) < 4 or len(new_user) > 12):
            new_user = ""
        else:
            CLIENT_LIST[new_user] = client
            #print(f"ALL CLIENTS ATM: {CLIENT_LIST}")
    
    if not new_user:
        client.send_text_data("409")
        return get_valid_username(client)
    
    client.send_text_data("200")
    client.send_text_data(f"You have now connected as:: {new_user}")
    return new_user


def notify_users_on_user_change(self_client, user_msg):
    global RELAY_LOCK, CLIENT_LIST
    for cli in CLIENT_LIST.values():
        if cli == self_client: continue
        cli.send_text_data(user_msg)


def send_new_message(msg, user_list):
    invalid_users = []
    with RELAY_LOCK:
        for user, sock in user_list:
            #print(f"SENDING DATA TO {user}: {msg}")
            try:
                sock.send_text_data(msg)
            except Exception as user_err:
                print(f"ERROR WITH SENDING ON THE USER SOCKET.!.!.! TO USER: {user}")
                print(user_err)
                invalid_users.append(user)
        for user in invalid_users:
            del CLIENT_LIST[user]


def start_client(client_socket, addr):
    global CLIENT_LIST, RELAY_LOCK

    client = ClientHandler(client_socket)
    # get the secret access token from the client
    if not client.recieved_valid_token(): return
    client.remove_timeout()
    
    # get a valid username from the client
    if not (sender := get_valid_username(client)): return
    #prep_name = new_user + "/"

    # send the list of online users to the new client
    current_users = MESSAGE_TYPES["user list"] + MESSAGE_SEPARATOR + "\n".join(CLIENT_LIST.keys())
    client.send_text_data(current_users)

    # update user list change for all clients
    add_user = MESSAGE_TYPES["add user"] + MESSAGE_SEPARATOR + sender
    notify_users_on_user_change(client, add_user)

    try:
        while (data := client.recieve_text_data()):
            #print(f"Incoming data from: {addr}: {data}")
            msg_type = MESSAGE_TYPES["private msg"] if data.startswith("@") else MESSAGE_TYPES["public msg"]
            
            outgoing_users = []
            with RELAY_LOCK:
                if msg_type == MESSAGE_TYPES["private msg"]:
                    msg_to_user = data.split(" ")[0][1:]
                    outgoing_users = [(sender, CLIENT_LIST[sender])] if msg_to_user != sender else []
                    if (recv_client := CLIENT_LIST.get(msg_to_user, None)):
                        outgoing_users.insert(0, (msg_to_user, recv_client))
                        msg_data = data[len(msg_to_user) + 2:]
                        if not msg_data: continue
                    else:
                        msg_data = "NO SUCH USER ONLINE.... CHECK YOURSELF!!"
                else:
                    msg_data = data
                    outgoing_users = CLIENT_LIST.items()

            outgoing_msg = msg_type + MESSAGE_SEPARATOR + sender + MESSAGE_SEPARATOR + msg_data
            # send the outoing message to the appropriate user(s)
            send_new_message(outgoing_msg, outgoing_users)
    except Exception as ex:
        print(f"ERROR WITH THE CLIENT SOCKET..... {sender}")
        print(ex)
    finally:
        with RELAY_LOCK:
            # remove the disconnected user from the client list
            if sender in CLIENT_LIST: del CLIENT_LIST[sender]
        # notify all clients that the user has left
        remove_user = MESSAGE_TYPES["del user"] + MESSAGE_SEPARATOR + sender
        notify_users_on_user_change(client, remove_user)    

    # print("Client shutting down")
    # print(f"Clients lefT: {CLIENT_LIST}")



if __name__ == "__main__":
    server = start_server()
    accepting = True

    while accepting:
        print("Listening for a new client!")
        client, addr = server.accept()
        print(f"Client connected from: {addr}")

        client_thread = threading.Thread(target=start_client, args=(client, addr))
        client_thread.daemon = True
        client_thread.start()

    server.close()




    # msg = client.recv(4096).decode("UTF-8")
    # client.sendall(msg[::-1].encode(("UTF-8")))
    # client.close()
