import logging
import telegram
import datastore

from google.appengine.api import urlfetch

from datastore import User, Ping
from setup import app


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


class Command(object):

    def __init__(self, bot, update, admin_only=False, status_only=-1, has_argument=False):
        # type: (telegram.Bot, telegram.Update, bool, int) -> None
        self.bot = bot
        self.update = update

        self.chat_id = update.message.chat_id
        self.command = update.message.text
        self.telegram_user = update.message.from_user
        self.admin_only = admin_only
        self.status_only = status_only
        self.has_argument = has_argument

    def __get_user(self):
        # type: () -> User
        user = User.get_by_id(self.telegram_user.id)
        if not user:
            logging.info("user %s not found!", self.telegram_user.id)
            user = User(id=self.telegram_user.id,
                        first_name=self.telegram_user.first_name,
                        last_name=self.telegram_user.last_name)
            user.put()

        return user

    def __cmd_body(self):
        return None

    def run(self):
        user = self.__get_user()
        if self.admin_only and not user.admin:
            self.bot.sendMessage(self.chat_id, "You must be admin to run this command!")
        elif self.status_only > 0 and not user.status == self.status_only:
            self.bot.sendMessage(self.chat_id, "Unknown command!")
        else:
            self.__cmd_body()
            if self.has_argument:
                user.pending_cmd = self.cmd_name
                user.put()

    def __arg_body(self):
        return None

    def get_argument(self):
        # Clear pending argument
        user = self.__get_user()
        user.pending_cmd = None
        user.put()
        self.__arg_body()


class ListUsers(Command):

    def __init__(self, bot, update):
        # type: (telegram.Bot, telegram.Update)
        super(ListUsers, self).__init__(bot, update, True, datastore.STATUS_AUTH)

    def __cmd_body(self):
        query = User.query()
        query_list = list(query.fetch())

        for user in query_list:
            self.bot.sendMessage(self.chat_id, user.first_name + " " + user.last_name)


class DevStatus(Command):

    def __init__(self, bot, update):
        # type: (telegram.Bot, telegram.Update)
        super(DevStatus, self).__init__(bot, update, True, datastore.STATUS_AUTH)

    def __cmd_body(self):
        query = Ping.query()
        query_list = list(query.fetch())

        for ping in query_list:
            self.bot.sendMessage(self.chat_id, "*Last ping:* " + str(ping.date), parse_mode=telegram.ParseMode.MARKDOWN)

        if len(query_list) == 0:
            self.bot.sendMessage(self.chat_id, "No device!")


class Unlock(Command):

    def __init__(self, bot, update):
        # type: (telegram.Bot, telegram.Update)
        super(Unlock, self).__init__(bot, update, False, datastore.STATUS_AUTH)

    def __cmd_body(self):
        self.bot.sendMessage(self.chat_id, "Unlocking...")
        send_pulse_cmd(app.config['LOCK_HOST'],
                       app.config['LOCK_PORT'],
                       app.config['LOCK_AUTHKEY'])


class Login(Command):

    cmd_name = "login"

    def __init__(self, bot, update):
        # type: (telegram.Bot, telegram.Update)
        super(Login, self).__init__(bot, update, False, datastore.STATUS_NEW, True)

    def __cmd_body(self):
        # Update user status
        self.bot.sendMessage(self.chat_id, "Please enter the password...")

    def __arg_body(self):
        if self.update.message.text == app.config['PASS']:
            user = self.__get_user()
            user.status = datastore.STATUS_AUTH
            user.put()
            self.bot.sendMessage(self.chat_id, "Welcome %s %s!", user.first_name, user.last_name)
        else:
            self.bot.sendMessage(self.chat_id, "Wrong password")


class Logout(Command):

    def __init__(self, bot, update):
        # type: (telegram.Bot, telegram.Update)
        super(Logout, self).__init__(bot, update, False, datastore.STATUS_AUTH)

    def __cmd_body(self):
        # Update user status
        user = self.__get_user()
        user.key.delete()

        self.bot.sendMessage(self.chat_id, "See you soon! :-)")


cmd_classes = {
    'devstatus': DevStatus,
    'listusers': ListUsers,
    'login': Login,
    'logout': Logout,
    'unlock': Unlock
}
