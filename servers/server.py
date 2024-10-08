import socket
import random
import string
import time
import re
import select
from multiprocessing.dummy import Pool as ThreadPool
import subprocess
import signal
import sys
import os

if sys.platform.startswith('win'):
    import console_ctrl

STATE_DISCONNECTED = 1
STATE_CONNECTED = 2
STATE_LOGGEDIN = 3

RPL_WELCOME = '001'

TERMINATED = False

def random_string(length: int):
    return ''.join(random.choices(string.ascii_uppercase, k=length))

class DummyClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.nick = random_string(9)
        self.user = random_string(10)
        self.name = random_string(10) + ' ' + random_string(10)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.MAX_LEN = 512
        self.state = STATE_DISCONNECTED
        time.sleep(1) # Sleep for 1 second to let the server start up 

    def idle_loop(self):
        while not TERMINATED:
            if self.state == STATE_DISCONNECTED:
                self.connect()
            elif self.state == STATE_CONNECTED:
                self.login()
            elif self.state == STATE_LOGGEDIN:
                msg = self.get_response_nonblocking()
                if msg is not None:
                    self.handle_incoming(msg) # ping-pong

            time.sleep(0.1)


    def get_response(self):
        return self.socket.recv(self.MAX_LEN).decode()
    
    def get_response_nonblocking(self):
        r,w,e = select.select([self.socket], [] , [], 0)
        if r == []: return None # No data available
        return self.get_response() # Data available

    def send(self, s):
        self.socket.send((s+'\r\n').encode())

    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            self.state = STATE_CONNECTED
            print('Connected to server.')
        except Exception as e:
            print('Could not connect ({}).'.format(str(e)))
            self.state = STATE_DISCONNECTED

    # http://chi.cs.uchicago.edu/chirc/irc_examples.html#chirc-irc-examples
    def login(self):
        self.send(f'NICK {self.nick}')
        self.send(f'USER {self.user} * *:{self.name}')
        msg = self.get_response()
        m = re.match(':(.+) (\d+) (.+) :(.+)', msg)
        if m:
            servername = m.group(1)
            rplid = m.group(2)
            nick = m.group(3)
            welcome_msg = m.group(4)
            if rplid == RPL_WELCOME:
                self.state = STATE_LOGGEDIN
                self.send(f'JOIN #main')
                return
        print('Failed to login...: ' + msg)

    def handle_incoming(self, msg):
        print('Received ' + msg + ' (len=' + str(len(msg))+')')
        chunks = msg.split()

        # Handle PING-PONG
        if len(chunks) > 1:
            if chunks[0] == 'PING':
                self.send(f'PONG {chunks[1]}')

def start_client(i):
    client = DummyClient('localhost', 6667)
    client.idle_loop()

def main():
    print('Running irc server with coverage measurement.')

    pool = ThreadPool(processes=10)
    pool.map_async(start_client, range(10))
    timeout = 62

    if sys.platform.startswith('win'):
        with open('tmp.log', 'w') as log_file:
            p = subprocess.Popen(['python', '-m', 'coverage', 'run', os.path.join('miniircd', 'miniircd'), '--debug'], stdout=log_file, creationflags=subprocess.CREATE_NEW_CONSOLE)
            time.sleep(timeout)
            console_ctrl.send_ctrl_c(p.pid)
            log_file.flush()
        try:
            with open('tmp.log', 'r') as log_file:
                print(log_file.read())
            os.remove('tmp.log')
        except FileNotFoundError:
            pass
    else:
        p = subprocess.Popen(['python', '-m', 'coverage', 'run', os.path.join('miniircd', 'miniircd'), '--debug'])
        try:
            p.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.send_signal(signal.SIGINT)
    print('Timeout, finishing')
    global TERMINATED
    TERMINATED = True # ends client threads
    pool.close()
    pool.join()

    print('Finished. To report coverage, type: coverage report')

if __name__ == "__main__":
    main()