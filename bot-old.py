import time
import datetime
import configparser
import telepot
import logging
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from urllib.parse import urlparse, parse_qs
from telepot.loop import MessageLoop
from http.server import BaseHTTPRequestHandler, HTTPServer


PASSWORD = "doge"

lock_ip = ""
lock_last_ping = 0
lock_status = False


class UserList():
    user_list = []
    pending_list = []

    def __init__(self):
        pass

    def __remove_all(self, alist, content):
        while content in alist:
            alist.remove(content)

    def set_pending(self, uid):
        self.pending_list.append(uid)

    def is_logged(self, uid):
        return uid in self.user_list

    def set_logged(self, uid):
        self.__remove_all(self.pending_list, uid)
        self.user_list.append(uid)

    def is_pending(self, uid):
        return uid in self.pending_list

    def remove(self, uid):
        self.__remove_all(self.pending_list, uid)
        self.__remove_all(self.user_list, uid)


def broadcast(message):
    for uid in users.user_list:
        bot.sendMessage(uid, message)


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200, "OK")
        self.end_headers()
        self.wfile.write(bytes("OK", "utf-8"))

        # Parse request
        par = urlparse(self.path)

        if par.path == "/ping":
            args = parse_qs(par.query, keep_blank_values=True)
            if args['id'] and len(args['id']) == 1:
                dev_id = int(args['id'][-1])
                ping_received(dev_id, self.client_address[0])
            else:
                logging.error("Device ID not valid!")
        return


def handle_bot_msg(msg):
    chat_id = msg['chat']['id']
    command = msg['text']

    logging.debug("Command from %s: %s", chat_id, command)

    if users.is_logged(chat_id):
        # Logged user
        if command == '/status':
            # Send lock status
            if lock_status:
                st = datetime.datetime.fromtimestamp(lock_last_ping).strftime('%H:%M:%S %d-%m-%Y')
                bot.sendMessage(chat_id, "Lock ONLINE!\nIP: " + lock_ip + "\nLast ping: " + st)
            else:
                bot.sendMessage(chat_id, "Lock OFFLINE!")
        elif command == '/unlock':
            # Send unlock command
            if not lock_ip:
                bot.sendMessage(chat_id, "IP not set.")
            elif not lock_status:
                bot.sendMessage(chat_id, "Lock OFFLINE!")
            else:
                bot.sendMessage(chat_id, "Unlocking...")
                unlock_result = unlock()
                if unlock_result:
                    bot.sendMessage(chat_id, "Door is unlocked!")
                else:
                    bot.sendMessage(chat_id, "Unlock failed!")
        elif command == "/logout":
            # User logout
            users.remove(chat_id)
            bot.sendMessage(chat_id, "See you soon!")
        else:
            bot.sendMessage(chat_id, "Unknown command!")

    elif users.is_pending(chat_id):
        # Logging user
        if command == PASSWORD:
            users.set_logged(chat_id)
            bot.sendMessage(chat_id, "Password correct! Welcome :-)")
            logging.info("User %s added!", chat_id)
        else:
            users.remove(chat_id)
            bot.sendMessage(chat_id, "Wrong password!")

    else:
        # Unknown user
        if command == "/login":
            bot.sendMessage(chat_id, "Please enter the password.")
            users.set_pending(chat_id)
        else:
            bot.sendMessage(chat_id, "You are not currently logged in!\nUse /login to start a session.")


def ping_received(dev_id, dev_ip):
    logging.info("Device %s sent a ping!", dev_id)

    # Only lock right now
    if dev_id == lock_id:
        global lock_ip
        global lock_last_ping
        global lock_status
        lock_ip = dev_ip
        lock_last_ping = time.time()

        if not lock_status:
            broadcast("Lock just returned ONLINE!")
            lock_status = True
            start_timeout()
    else:
        logging.error("Unknown ID!")


def check_timeout():
    now = time.time()
    delta = now - lock_last_ping

    logging.info("Checking lock timeout...")

    if(delta > lock_timeout * 1000):
        broadcast("Lock missed scheduled ping!")
        stop_timeout()


def start_timeout():
    global sched
    sched.resume()


def stop_timeout():
    global sched
    sched.pause()


def unlock():
    logging.info("Unlocking...")
    response = requests.get("http://" + lock_ip + ":" + str(lock_port) + "/unlock?code=" + lock_code)
    if response.status_code == 200:
        logging.info("Unlock successful!")
        return True
    else:
        logging.info("Unlock failed!")
        return False


# Setup logger
logging.basicConfig(level=logging.INFO)

# Read configuration
config = configparser.ConfigParser()
config.read('bot.cfg')
bot_token = config['main']['bot_token']
server_address = config['main']['address']
server_port = int(config['main']['port'])
lock_id = int(config['lock']['id'])
lock_port = int(config['lock']['port'])
lock_timeout = int(config['lock']['timeout'])
lock_code = config['lock']['code']
logging.info("Configuration loaded!")

# Data
users = UserList()

# Setup bot
bot = telepot.Bot(bot_token)
MessageLoop(bot, handle_bot_msg).run_as_thread()

# Start scheduler
sched = BackgroundScheduler()
sched.start()
sched.add_job(check_timeout, 'interval', seconds=lock_timeout)

# Setup server
server = (server_address, server_port)
httpd = HTTPServer(server, RequestHandler)
httpd.serve_forever()
