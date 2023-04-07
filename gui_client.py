import socket
import threading
import time
from tkinter import *
from tkinter.scrolledtext import ScrolledText
from client_handler import ClientHandler

class GuiClient:

    WELCOME_MSG = """
    - BEFORE WE START - 
    You must enter a name before you can start chatting!
    Only alphanumerical characters allowed.
    The length of the name has to be 4-12 characters long.

    Once you're up and chatting you can send private messages by starting the message with @<username of receiver> message goes here...
    """

    def _connect_to_server(self):
        connect_to = ("localhost", 56789)

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #client.settimeout(30)
        client.connect(connect_to)
        print("Now connected to server!")

        self._client = ClientHandler(client)


    def _start_listen_thread(self):
        listen_thread = threading.Thread(target=self._listen)
        listen_thread.daemon = True
        listen_thread.start()
        return listen_thread


    def _add_text_to_chat_box(self, sender, msg_type, msg):
        #tm = time.strftime("%y/%m/%d %H:%M", time.localtime())
        recv_time = time.strftime("(%H:%M:%S)", time.localtime())
        self._output_box["state"] = "normal"
        self._output_box.insert("end", f"{recv_time} ", "grey")
        self._output_box.insert("end", f"{sender}:: ", "red" if msg_type == "pri" else ("green" if sender == self._username else "blue"))
        self._output_box.insert("end", f"{msg}\n")
        self._output_box["state"] = "disabled"
        self._output_box.see("end")


    def _init_welcome_content(self):
        self._output_box["font"] = ("Times New Roman", 12)
        self._output_box["foreground"] = "black"

        self._output_box["state"] ="normal"
        self._output_box.delete("1.0", "end")
        self._output_box["state"] ="disabled"

        welcome_data = self._client.recieve_text_data()

        message_name = welcome_data.split(":: ")
        welcome_msg = message_name[0]
        self._username = message_name[1]
        
        self._add_text_to_chat_box(welcome_msg, "", self._username)
        
        self._online_users = self._client.recieve_text_data()[4:].split("\n")


    def _modify_user_list(self):
        self._user_list["state"] = "normal"
        self._user_list.delete("1.0", "end")
        self._user_list.insert("end", f"USERS ONLINE: {len(self._online_users)}\n{'=' * 16}\n")
        self._user_list.insert("end", "\n".join(self._online_users))
        self._user_list["state"] = "disabled"


    def _listen(self):
        listening = True

        while listening:
            try:
                data = self._client.recieve_text_data()
            except Exception as err:
                listening = False
                print("LOST CONNECTION TO THE SERVER?!?!?!")
                print(err)
                print("Trying to reconnect....")
                #raise SystemExit(1)
                #print(f"THREADS NOW: {threading.active_count()}")
                return self._start_listen_thread()

            if not data: return
            
            msg_type = data[:3]
            if msg_type == "add" or msg_type == "del":
                user_name = data[4:]
                match msg_type:
                    case "add":
                        self._online_users.append(user_name)
                    case "del":
                        self._online_users.remove(user_name)
                self._modify_user_list()
            else:
                name_part = data.index("/", 4)
                sender = data[4:name_part]
                msg_part = data[name_part + 1:]
                self._add_text_to_chat_box(sender, msg_type, msg_part)


    def _speak(self):
        msg = self._chat_box.get()
        self._chat_box.delete(0, "end")
        if not msg.strip(): return
        try:
            self._client.send_text_data(msg)
        except Exception as err:
            print("LOST CONNECTION TO THE SERVER?!?!?!")
            print(err)
            raise SystemExit(1)


    def _check_username(self):
        name = self._name_box.get()

        if not name: return

        self._client.send_text_data(name)
        status = self._client.recieve_text_data()
        if status == "200":
            self._name_box["state"] = "disabled"
            self._name_btn["state"] = "disabled"

            self._chat_box["state"] = "normal"
            self._chat_btn["state"] = "normal"

            self._init_welcome_content()
            self._modify_user_list()
            self._start_listen_thread()
        else:
            self._output_box["state"] = "normal"
            self._output_box.insert("end", "INVALID USERNAME, TRY AGAIN!\n", "center")
            self._output_box["state"] = "disabled"


    def run(self):
        self._connect_to_server()
        self._client.send_token()
        
        root = Tk()
        root.title("Cha-Cha-Chat")
        root.geometry("960x540+250+50")
        num_columns = 10
        last_col_width = 20

        name_label = Label(root, text="Username:")
        name_label.grid(row=0, column=0, columnspan=2, sticky="wns")

        name_input = Entry(root, font=("Helvetica", 12), highlightthickness=2)
        name_input.config(highlightbackground="blue", highlightcolor="blue")
        name_input.grid(row=0, column=2, columnspan=6, sticky="nswe")
        self._name_box = name_input

        name_btn = Button(root, text="Enter")
        name_btn.grid(row=0, column=8, columnspan=2, sticky="nswe")
        self._name_btn = name_btn

        user_list_label = Label(root, text=" - ALL USERS ONLINE - ", width=last_col_width)
        user_list_label.grid(row=0, column=10, sticky="nswe")

        output_box = ScrolledText(root, wrap="word", font=("Times New Roman", 18, "bold"))
        output_box.grid(row=1, column=0, columnspan=10, sticky="nswe")
        self._output_box = output_box

        output_box.tag_configure("center", justify="center", foreground="red")
        output_box.tag_configure("bold", justify="center")
        output_box.tag_configure("black", foreground="black")
        output_box.tag_configure("grey", foreground="grey")
        output_box.tag_configure("blue", foreground="blue")
        output_box.tag_configure("green", foreground="green")
        output_box.tag_configure("red", foreground="red")

        output_box.insert("end", self.WELCOME_MSG, "center")
        output_box["state"] = "disabled"

        user_list = ScrolledText(root, wrap="word", font=("Times New Roman", 12), width=last_col_width)
        user_list.grid(row=1, rowspan=2, column=10, sticky="nswe")
        user_list["state"] = "disabled"
        self._user_list = user_list

        send_label = Label(root, text="Say something:")
        send_label.grid(row=2, column=0, columnspan=2, sticky="w")

        input_box = Entry(root, state="disabled", font=("Helvetica", 12), highlightthickness=2)
        input_box.config(highlightbackground="green", highlightcolor="green")
        input_box.grid(row=2, column=2, columnspan=6, sticky="we")
        input_box.bind("<Return>", lambda _: self._speak())
        self._chat_box = input_box

        chat_btn = Button(root, text="Send", state="disabled", command= lambda: self._speak())
        chat_btn.grid(row=2, column=8, columnspan=2, sticky="we")
        self._chat_btn = chat_btn

        name_btn["command"] = lambda: self._check_username()

        root.grid_rowconfigure(1, weight=1)
        for i in range(num_columns):
            root.grid_columnconfigure(i, weight=1, uniform="yes")

        root.bind("<Escape>", lambda _: root.destroy())
        root.mainloop()

        #self._client.close()
        del self._client
        print("Now shutting down!")



if __name__ == "__main__":
    gui = GuiClient()
    gui.run()