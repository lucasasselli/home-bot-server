#!/usr/bin/env python
import sys
import os
sys.path.append(os.path.join(os.path.abspath('.'), 'venv/lib/site-packages'))

import telegram
from flask import Flask, request
import core

app = Flask(__name__)
app.config.from_pyfile('bot.cfg', silent=True)

global bot
bot = telegram.Bot(token=app.config['BOT_TOKEN'])

RESPONSE_OK = "OK!"
RESPONSE_FAIL = "FAIL!"

@app.route(app.config['BOT_HOOK'], methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        # retrieve the message in JSON and then transform it to Telegram object
        # update = telegram.Update.de_json(request.get_json(force=True), bot)

        # chat_id = update.message.chat.id

        # Telegram understands UTF-8, so encode text for unicode compatibility
        # text = update.message.text.encode('utf-8')

        core.send_unlock_cmd(app.config['LOCK_HOST'],
                             app.config['LOCK_PORT'],
                             app.config['LOCK_AUTHKEY'])
    return RESPONSE_OK


@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.setWebhook('https://' + app.config['HOST'] + app.config['HOOK'])
    if s:
        return RESPONSE_OK
    else:
        return RESPONSE_FAIL


@app.route('/ping', methods=['GET', 'POST'])
def ping_received():
    # Ping received
    return "OK!"


@app.route('/')
def index():
    return '.'
