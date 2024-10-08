import socket
import select
import re
import string

from fuzzingbook.GrammarFuzzer import GrammarFuzzer
from fuzzingbook.Grammars import Grammar

STATE_DISCONNECTED = 1
STATE_CONNECTED = 2
STATE_LOGGEDIN = 3

MAX_LEN = 512

RPL_WELCOME = '001'
RPL_YOURHOST = '002'
#...

def srange(characters: str):
    """Construct a list with all characters in the string"""
    return [c for c in characters]






grammar = {
    "<start>": ["<commands>"],
    "<commands>": ["<LIST>", "<PING>", "<MOTD>", "<JOIN>", "<PASS>", "<NICK>", "<USER>", "<ISON>", "<UMODE>",
                   "<PONG>", "<WHO>", "<NAMES>", "<WHOIS>", "<TOPIC>", "<LUSERS>", "<PART>", "<PRIVMSG>", "<CMODE>",
                  "<WALLOPS>", "<INVITE>", "<AWAY>"],


    #"<LINKS>": ["LINKS<space>*.<letters>"],


    "<AWAY>": ["AWAY"],
    "<MOTD>": ["MOTD", "MOTD<space><target>"],

    "<Nickname>": ["<nick>"],
    "<nick>": ["<firstch><nickcomp>"],
    "<firstch>": ["<letter>", "<special>", "<digit>", "-", ""],
    "<special>": ['[', ']', chr(92), ',', '_', '^', '{', '|', '}', ';'],
    "<nickcomp>": ["","<nickcompparm><nickcompparm><nickcompparm><nickcompparm><nickcompparm><nickcompparm><nickcompparm><nickcompparm>"],
    "<nickcompparm>": ["<letter>", "<digit>", "<special>"],

    "<PRIVMSG>": ["PRIVMSG<space><msgtarget><space><text>"],
    "<text>": ["<nickcompparm>", "<text><nickcompparm>"],

    "<PASS>": ["PASS <password>"],
    "<password>": ["<firstch>", "<password><firstch>"],

    "<PART>": ["PART", "PART<space><partparm><partmsg>"],
    "<partparm>": ["<channel>", "<partparm><comma><channel>"],
    "<partmsg>": ["<space>:<letterspa>", "<partmsg><letterspa>", ""],

    "<NICK>": ["NICK<space><Nickname>"],

    "<USER>": ["USER<space><Nickname><space><mode><space><unused><space><realname>"],
    "<mode>": ["<digit>"],
    "<unused>": ["*"],
    "<realname>": [":<firstname><space><lastname>"],
    "<firstname>": ["<letterupper><letterlowerrec>"],
    "<lastname>": ["<letterupper><letterlowerrec>"],
    "<letterlowerrec>": ["<letterlower>", "<letterlowerrec><letterlower>"],

    "<TOPIC>": ["TOPIC", "TOPIC<space><topicparm>"],
    "<topicparm>": ["<channel>", "<channel><space><topic>"],
    "<topic>": ["<nickcompparm>", "<topic><space><nickcompparm>"],

    "<WHOIS>": ["WHOIS<whoisparm>"],
    "<whoisparm>": ["<space><maskrec>", "<space><target><space><maskrec>"],
    "<maskrec>": ["<mask>", "<maskrec><comma><mask>"],

    "<NAMES>": ["NAMES", "NAMES<space><nameparm>"],
    "<nameparm>": ["<partparm>", "<partparm><space><target>"],

    "<LIST>": ["LIST", "LIST<space><Listparm>"],
    "<Listparm>": ["<recchanlist>", "<recchanlist><space><target>"],
    "<recchanlist>": ["<channel>", "<recchanlist><comma><channel>"],

    "<INVITE>": ["INVITE<space><Nickname><space><channel>"],

    "<WHO>": ["WHO", "WHO<space><whoparm>"],
    "<whoparm>": ["<mask>", "<mask><space>o"],

    "<LUSERS>": ["LUSERS","LUSERS<space><lus>"],
    "<lus>": ["<mask>","<mask><space><target>"],

    "<PING>": ["PING", "PING<space><servername>", "PING<space><servername><space><servername>"],

    "<PONG>": ["PONG<space><servername>", "PONG<space><servername><space><servername>"],

    "<WALLOPS>": ["WALLOPS", "WALLOPS<space>:<topic>"],

    "<ISON>": ["ISON<space><Nickname><isonparm>"],
    "<isonparm>": ["<Nickname>", "<isonparm><space><Nickname>"],

    "<msgtarget>": ["<msgto>", "<msgtarget><comma><msgto>"],
    "<msgto>": ["<channel>", "<user><space><msgtohost><at><servername>", "<user><msgtohost>", "<targetmask>", "<Nickname>",
                "<Nickname>!<user><at><host>"],
    "<user>": ["<letterpa>"],
    "<servername>": ["<hostname>"],
    "<msgtohost>": ["%<host>"],
    "<host>": ["<hostname>", "<hostaddr>"],
    "<hostname>": ["<shortname>", "<hostname><dot><shortname>"],
    "<shortname>": ["<letdeg>", "<letdeg><letdigrec>", "<letdeg><letdigrec><letdegR>"],
    "<letdigrec>": ["<letdegunter>", "<letdigrec><letdegunter>", ""],
    "<letdegR>": ["<letdeg>", "<letdegR><letdeg>"],
    "<letdeg>": ["<letter>", "<digit>"],
    "<letdegunter>": ["<letter>", "<digit>", "-"],
    "<hostaddr>": ["<ip4addr>", "<ip6addr>"],
    "<ip4addr>": ["<3dig><dot><3dig><dot><3dig><dot><3dig>"],
    "<3dig>": ["<digit><digit><digit>"],
    "<ip6addr>": ["<hexdigit><hexrec>", "<zerohex><zeroF>:<ip4addr>"],
    "<hexrec>": ["<hexdoplepunkt>", "<hexdoplepunkt><hexdoplepunkt>", "<hexdoplepunkt><hexdoplepunkt><hexdoplepunkt>",
                 "<hexdoplepunkt><hexdoplepunkt><hexdoplepunkt><hexdoplepunkt>",
                 "<hexdoplepunkt><hexdoplepunkt><hexdoplepunkt><hexdoplepunkt><hexdoplepunkt>",
                 "<hexdoplepunkt><hexdoplepunkt><hexdoplepunkt><hexdoplepunkt><hexdoplepunkt><hexdoplepunkt>",
                 "<hexdoplepunkt><hexdoplepunkt><hexdoplepunkt><hexdoplepunkt><hexdoplepunkt><hexdoplepunkt><hexdoplepunkt>"],
    "<zeroF>": ["0", "FFFF"],
    "<zerohex>": ["0:0:0:0:0:"],
    "<hexdoplepunkt>": [":<hexdigit>"],
    "<hexdigit>": ["<digit>", "A", "B", "C", "D", "E", "F"],
    "<targetmask>": ["$<mask>", "#<mask>"],
    "<mask>": ["<maskparm>", "<mask><maskparm>"],
    "<maskparm>": ["<nowild>", "<noesc><wildone>", "<noesc><wildmany>"],
    "<wildone>": ["?"],
    "<wildmany>": ["*"],
    "<nowild>": ["<letterpa>"],
    "<noesc>": ["<letterpa>"],
    "<target>": ["<Nickname>", "<servername>"],

    "<UMODE>": ["MODE", "MODE<space><Nickname><space><usermodeparm>"],
    "<usermodeparm>": ["<modestype>", "<usermodeparm><modestype>"],
    "<modestype>": ["<plusminus><type>", "<plusminus>"],
    "<plusminus>": ["+", "-"],
    "<type>": ["i", "w", "o", "O", "r", "k"],

    "<CMODE>": ["MODE<space><cmoedparm>"],
    "<cmoedparm>": ["<channel><space><modestype><modestyperec><space><modekey>"],
    "<modestyperec>": ["<modestype>", "<modestyperec><modestype>"],
    "<modekey>": ["<nickcompparm>", "<modekey><nickcompparm>"],

     "<JOIN>": ["JOIN", "JOIN<space><joinparm>"],
    "<joinparm>": ["<channels>", "<keys>", "<recCK>", "0"],
    "<channels>": ["<channel>", "<channels><comma><channel>"],
    "<channel>": ["<chansymbol><chanstring>", "!<channelid><chanstring>"],
    "<chansymbol>": ["#", "&", "+"],
    "<channelid>": ["<digiletter>", "<digiletter><channelid>"],
    "<digiletter>": ["<letter>", "<digit>"],
    "<chanstring>": ["<letterpa>"],
    "<keys>": ["<key>", "<keys><comma><key>"],
    "<key>": ["<letterpa>", "<key><space><letterpa>"],
    "<recCK>": ["<channels><space><keys>"],



    "<space>": [" ", " "],
    "<comma>": [","],
    "<dot>": ["."],
    "<at>": ["@"],
    "<letterspa>": ["<letterpa>", "<letterspa><letterpa>"],
    "<letterlower>": srange(string.ascii_lowercase),
    "<letterpa>": srange(string.printable),
    "<letterupper>": srange(string.ascii_uppercase),
    #"<letters>": ["<letter>", "<letters><letter>"],
    "<letter>": srange(string.ascii_letters),
    "<digit>": srange(string.digits),

}




class Client:
    def __init__(self, host, port, nick, user, name, password):
        self.host = host
        self.port = port
        self.nick = nick
        self.user = user
        self.name = name
        self.password = password
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.fuzzer = GrammarFuzzer(grammar)

        self.state = STATE_DISCONNECTED

    def get_response(self):
        return self.socket.recv(MAX_LEN).decode()

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
                return
        print('Failed to login...: ' + msg)

    def handle_incoming(self, msg):
        print('Received ' + msg + ' (len=' + str(len(msg))+')')
        chunks = msg.split()

        # Handle PING-PONG
        if len(chunks) > 1:
            if chunks[0] == 'PING':
                self.send(f'PONG {chunks[1]}')

    def send_fuzz_msg(self):
        s = self.fuzzer.fuzz()
        self.send(s)

    def fuzzer_loop(self):
        try:
            while True:
                if self.state == STATE_DISCONNECTED:
                    self.connect()
                elif self.state == STATE_CONNECTED:
                    self.login()
                elif self.state == STATE_LOGGEDIN:
                    msg = self.get_response_nonblocking()
                    if msg is not None:
                        self.handle_incoming(msg)
                    self.send_fuzz_msg()
        except (BrokenPipeError, ConnectionResetError):
            print('Server closed connection.')

def main():
    client_new = Client('localhost', 6667, 'ahmad', 'hajyomar', 'Mr. ahmad', 'ghost')
    client_new.connect()
    client_new.login()
    client_new.send("QUIT")
    client_new.send("QUIT bye bye")

    client_new2 = Client('localhost', 6667, 'mouayad', 'hajiomar', 'Mr. mouayad', 'csgoking')
    client_new2.connect()
    client_new2.login()
    client_new2.send("MODE mouayad +k")
    client_new2.send("MODE #csgo +k mouayad")












    client = Client('localhost', 6667, 'sponge', 'bob', 'Mr. Sponge', 'password')
    client.fuzzer_loop()

if __name__ == "__main__":
    main()