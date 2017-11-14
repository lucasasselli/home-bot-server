#!/usr/bin/env python
import sys
import os
sys.path.append(os.path.join(os.path.abspath('.'), 'venv/lib/site-packages'))

from google.appengine.ext import vendor
# Add any libraries install in the "lib" folder.
vendor.add('lib')

import telegram
from flask import Flask, request
import logging
import datetime
from google.appengine.api import urlfetch
from google.appengine.ext import ndb

# Constants
RESPONSE_OK = "OK"
RESPONSE_FAIL = "FAIL"
STATUS_NEW = 0
STATUS_PENDING = 1
STATUS_AUTH = 2


class User(ndb.Model):
    status = ndb.IntegerProperty(default=STATUS_NEW)
    first_name = ndb.StringProperty()
    last_name = ndb.StringProperty()
    admin = ndb.BooleanProperty(default=False)


class Ping(ndb.Model):
    date = ndb.DateTimeProperty()


def send_unlock_cmd(lock_host, lock_port, lock_code):
    logging.debug("Sending unlock request to %s %s", lock_host, lock_port)
    logging.info("Unlocking...")
    url = "http://" + lock_host + ":" + lock_port + "/unlock?code=" + lock_code
    try:
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            logging.info("Unlock successful!")
            return True
        else:
            logging.info("Unlock failed!")
            return False
    except urlfetch.Error:
        logging.exception('Caught exception fetching url')

    return False


def handle_bot_msg(update):

    chat_id = update.message.chat_id
    command = update.message.text
    telegram_user = update.message.from_user

    logging.debug("Command from %s (admin=%s): %s", chat_id, command)

    user = User.get_by_id(telegram_user.id)
    if not user:
        logging.info("User %s not found!", telegram_user.id)
        user = User(id=telegram_user.id,
                    first_name=telegram_user.first_name,
                    last_name=telegram_user.last_name)
        user.put()


    if user.status == STATUS_AUTH:
        # AUTHENTICATED USERS
        if command == "/listusers":
            if user.admin:
                query = User.query()
                query_list = list(query.fetch())

                for sysuser in query_list:
                    bot.sendMessage(chat_id, user.first_name + " " + user.last_name)
        elif command == "/status":
            if user.admin:
                query = Ping.query()
                query_list = list(query.fetch())

                for ping in query_list:
                    bot.sendMessage(chat_id, "*Last ping:* " + str(ping.date), parse_mode=telegram.ParseMode.MARKDOWN)
                        
                if len(query_list) == 0:        
                    bot.sendMessage(chat_id, "No device!")

        elif command == '/unlock':
            # Send unlock command
            bot.sendMessage(chat_id, "Unlocking...")
            send_unlock_cmd(app.config['LOCK_HOST'],
                            app.config['LOCK_PORT'],
                            app.config['LOCK_AUTHKEY'])
            # Check result
            # if unlock_result:
            #     bot.sendMessage(chat_id, "Door is unlocked!")
            # else:
            #     bot.sendMessage(chat_id, "Unlock failed!")
        elif command == "/logout":
            # User logout
            user.key.delete()
            bot.sendMessage(chat_id, "See you soon!")
        else:
            bot.sendMessage(chat_id, "Unknown command!")

    elif user.status == STATUS_PENDING:
        # PENDING USERS
        if command == app.config['PASS']:
            # Update user status
            user.status = STATUS_AUTH
            user.put()

            # Send response
            bot.sendMessage(chat_id, "Password accepted! Welcome :-)")
            logging.info("User %s added!", chat_id)
        else:
            user.key.delete()
            bot.sendMessage(chat_id, "Wrong password!")

    else:
        # UNKNOWN USERS
        if command == "/login":
            # Update user status
            user.status = STATUS_PENDING
            user.put()

            bot.sendMessage(chat_id, "Please enter the password.")
        else:
            bot.sendMessage(chat_id, "You are not currently logged in!\nUse /login to start a session.")


app = Flask(__name__)
app.config.from_pyfile('bot.cfg', silent=True)

global bot
bot = telegram.Bot(token=app.config['BOT_TOKEN'])


@app.route(app.config['BOT_HOOK'], methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        # retrieve the message in JSON and then transform it to Telegram object
        update = telegram.Update.de_json(request.get_json(force=True), bot)

        handle_bot_msg(update)

        return RESPONSE_OK


@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.setWebhook('https://' + app.config['HOST'] + app.config['BOT_HOOK'])
    if s:
        return RESPONSE_OK
    else:
        return RESPONSE_FAIL


@app.route('/ping', methods=['GET', 'POST'])
def ping_received():
    # Ping received
    ping = Ping.get_by_id(1)
    if not ping:
        ping = Ping(id=1)
    ping.date = datetime.datetime.now()
    ping.put()

    return RESPONSE_OK


@app.route('/')
def index():
    return '.'
