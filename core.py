import logging
import telegram
import datastore
from datastore import User, Ping


class Command():

    def __init__(self, bot: telegram.Bot, update: telegram.Update, admin_only=False, status_only=-1):
        self.bot = bot
        self.update = update

        self.chat_id = update.message.chat_id
        self.command = update.message.text
        self.telegram_user = update.message.from_user
        self.admin_only = admin_only
        self.status_only = status_only

    def __get_user(self) -> User:
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


class ListUsers(Command):

    def __init__(self, bot: telegram.Bot, update: telegram.Update):
        super().__init__(bot, update, True, datastore.STATUS_AUTH)

    def __cmd_body(self):
        query = User.query()
        query_list = list(query.fetch())

        for user in query_list:
            self.bot.sendMessage(self.chat_id, user.first_name + " " + user.last_name)


class DevStatus(Command):

    def __init__(self, bot: telegram.Bot, update: telegram.Update):
        super().__init__(bot, update, True, datastore.STATUS_AUTH)

    def __cmd_body(self):
        query = Ping.query()
        query_list = list(query.fetch())

        for ping in query_list:
            self.bot.sendMessage(self.chat_id, "*Last ping:* " + str(ping.date), parse_mode=telegram.ParseMode.MARKDOWN)

        if len(query_list) == 0:
            self.bot.sendMessage(self.chat_id, "No device!")


class Unlock(Command):

    def __init__(self, bot: telegram.Bot, update: telegram.Update):
        super().__init__(bot, update, False, datastore.STATUS_AUTH)

    def __cmd_body(self):
        self.bot.sendMessage(self.chat_id, "Unlocking...")
        # send_pulse_cmd(app.config['LOCK_HOST'],
        #                app.config['LOCK_PORT'],
        #                app.config['LOCK_AUTHKEY'])


class Login(Command):

    def __init__(self, bot: telegram.Bot, update: telegram.Update):
        super().__init__(bot, update, False, datastore.STATUS_PENDING)

    def __cmd_body(self):
        # Update user status
        user = self.__get_user()
        user.status = datastore.STATUS_PENDING
        user.put()

        self.bot.sendMessage(self.chat_id, "Please enter the password.")


class Logout(Command):

    def __init__(self, bot: telegram.Bot, update: telegram.Update):
        super().__init__(bot, update, False, datastore.STATUS_PENDING)

    def __cmd_body(self):
        # Update user status
        user = self.__get_user()
        user.key.delete()

        self.bot.sendMessage(self.chat_id, "See you soon! :-)")


cmd_classes = {
    'dev-status': DevStatus,
    'list-users': ListUsers,
    'login': Login,
    'logout': Logout,
    'unlock': Unlock
}
