#!/usr/bin/env python
import setup
from setup import app, bot

from flask import request

import telegram
import logging
import datetime

import core
from datastore import User, Ping

# Constants
RESPONSE_OK = "OK"
RESPONSE_FAIL = "FAIL"

# Initialize Flask and Bot
setup.init()


@app.route(app.config['BOT_HOOK'], methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        # retrieve the message in JSON and then transform it to Telegram object
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        text = update.message.text
        user_id = update.message.from_user.id

        user = User.get_from_id(user_id)
        if user and user.pending_cmd:
            command = user.pending_cmd

            if command in core.cmd_classes:
                command_handler = core.cmd_classes[command](bot, update)
                command_handler.get_argument()

        if text[0] == "/":
            # Command received
            command = text[1:-1]

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
