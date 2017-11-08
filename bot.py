#!/usr/bin/env python
import sys
import os
sys.path.append(os.path.join(os.path.abspath('.'), 'venv/lib/site-packages'))

from google.appengine.ext import vendor
# Add any libraries install in the "lib" folder.
vendor.add('lib')

import telegram
from flask import Flask, request
import core
import logging

app = Flask(__name__)
app.config.from_pyfile('bot.cfg', silent=True)

global bot
bot = telegram.Bot(token=app.config['BOT_TOKEN'])

@app.route(app.config['BOT_HOOK'], methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        # retrieve the message in JSON and then transform it to Telegram object
        update = telegram.Update.de_json(request.get_json(force=True), bot)

        chat_id = update.message.chat.id

        # Telegram understands UTF-8, so encode text for unicode compatibility
        text = update.message.text.encode('utf-8')

        logging.debug("Message from %s: %s", chat_id, text)

        if (text == "/unlock"):
            core.send_unlock_cmd(app.config['LOCK_HOST'],
                    app.config['LOCK_PORT'],
                    app.config['LOCK_AUTHKEY'])
            return "OK!"


@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.setWebhook('https://' + app.config['HOST'] + app.config['BOT_HOOK'])
    if s:
        return "OK!"
    else:
        return "FAIL!"


@app.route('/ping', methods=['GET', 'POST'])
def ping_received():
    # Ping received
    return "OK!"


@app.route('/')
def index():
    return '.'
