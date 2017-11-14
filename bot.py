#!/usr/bin/env python
from flask import Flask, request

from google.appengine.api import urlfetch

import telegram
import logging
import datetime

import core
from datastore import Ping

# Constants
RESPONSE_OK = "OK"
RESPONSE_FAIL = "FAIL"


def send_pulse_cmd(lock_host, lock_port, lock_code):
    # type: (str, str, str) -> bool
    logging.debug("Sending pulse request to %s %s", lock_host, lock_port)
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


app = Flask(__name__)
app.config.from_pyfile('bot.cfg', silent=True)

global bot
bot = telegram.Bot(token=app.config['BOT_TOKEN'])


@app.route(app.config['BOT_HOOK'], methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        # retrieve the message in JSON and then transform it to Telegram object
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        text = update.message.text

        if text[0] == "/":
            # Command received
            command = text[1:]

            logging.info("Command %s received from user %s", command, update.message.from_user.id)

            if command in core.cmd_classes:
                command_handler = core.cmd_classes[command](bot, update)
                command_handler.run()

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
