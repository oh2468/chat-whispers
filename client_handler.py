import socket
import struct


class ClientHandler():
    _SECRET_TOKEN = b"SuperSecretKey0"
    TEXT_ENCODING = "UTF-8"
    DEFAULT_BUFF_SIZE = 4096
    STRUCT_SIZE = 4
    STATUS_MSG_SIZE = 32
    STRUCT_FORMAT = ">I"
    CLINET_TIMEOUT = 10


    def __init__(self, sock):
        self._client = sock
        self._client.settimeout(self.CLINET_TIMEOUT)


    def __del__(self):
        self._client.close()
        #print("Now Deleting The Client Handler..")


    def remove_timeout(self):
        self._client.settimeout(None)


    def send_bin_data(self, data):
        if not data: return
        data_size = struct.pack(self.STRUCT_FORMAT, len(data))
        self._client.sendall(data_size + data)
    

    def send_text_data(self, text):
        if not text: return
        bin_text = bytes(text, self.TEXT_ENCODING)
        self.send_bin_data(bin_text)

    
    def recieve_data(self, size=None):
        if size:
            data_size = size
        else:
            size_struct = self._client.recv(self.STRUCT_SIZE)
            if not size_struct: return size_struct
            data_size = struct.unpack(self.STRUCT_FORMAT, size_struct)[0]

        data = b""
        while data_size and (data_part := self._client.recv(data_size)):
            if data_size < 0: raise SystemExit("WHAT IS GOING ON.... READING TOO MUCH DATA... CORRUPTION AHEAD!!!")
            data_size -= len(data_part)
            data += data_part

        return data

    
    def recieve_text_data(self, size=None):
        data = self.recieve_data(size)
        return str(data, self.TEXT_ENCODING) if data else data


    def send_token(self):
        self._client.sendall(self._SECRET_TOKEN)


    def recieved_valid_token(self):
        return self.recieve_data(len(self._SECRET_TOKEN)) == self._SECRET_TOKEN

