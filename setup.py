from flask import Flask
import telegram


global app
app = Flask(__name__)
app.config.from_pyfile('bot.cfg', silent=True)

global bot
bot = telegram.Bot(token=app.config['BOT_TOKEN'])
