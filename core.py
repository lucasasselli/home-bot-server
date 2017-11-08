import logging
import requests


def send_unlock_cmd(lock_ip, lock_port, lock_code):
    logging.info("Unlocking...")
    response = requests.get("http://" + lock_ip + ":" + str(lock_port) + "/unlock?code=" + lock_code)
    if response.status_code == 200:
        logging.info("Unlock successful!")
        return True
    else:
        logging.info("Unlock failed!")
        return False


# def handle_bot_msg(msg):
#     chat_id = msg['chat']['id']
#     command = msg['text']

#     logging.debug("Command from %s: %s", chat_id, command)

#     if users.is_logged(chat_id):
#         # Logged user
#         if command == '/status':
#             # Send lock status
#             if lock_status:
#                 st = datetime.datetime.fromtimestamp(lock_last_ping).strftime('%H:%M:%S %d-%m-%Y')
#                 bot.sendMessage(chat_id, "Lock ONLINE!\nIP: " + lock_ip + "\nLast ping: " + st)
#             else:
#                 bot.sendMessage(chat_id, "Lock OFFLINE!")
#         elif command == '/unlock':
#             # Send unlock command
#             if not lock_ip:
#                 bot.sendMessage(chat_id, "IP not set.")
#             elif not lock_status:
#                 bot.sendMessage(chat_id, "Lock OFFLINE!")
#             else:
#                 bot.sendMessage(chat_id, "Unlocking...")
#                 unlock_result = unlock()
#                 if unlock_result:
#                     bot.sendMessage(chat_id, "Door is unlocked!")
#                 else:
#                     bot.sendMessage(chat_id, "Unlock failed!")
#         elif command == "/logout":
#             # User logout
#             users.remove(chat_id)
#             bot.sendMessage(chat_id, "See you soon!")
#         else:
#             bot.sendMessage(chat_id, "Unknown command!")

#     elif users.is_pending(chat_id):
#         # Logging user
#         if command == PASSWORD:
#             users.set_logged(chat_id)
#             bot.sendMessage(chat_id, "Password correct! Welcome :-)")
#             logging.info("User %s added!", chat_id)
#         else:
#             users.remove(chat_id)
#             bot.sendMessage(chat_id, "Wrong password!")

#     else:
#         # Unknown user
#         if command == "/login":
#             bot.sendMessage(chat_id, "Please enter the password.")
#             users.set_pending(chat_id)
#         else:
#             bot.sendMessage(chat_id, "You are not currently logged in!\nUse /login to start a session.")