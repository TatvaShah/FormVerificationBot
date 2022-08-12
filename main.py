from telegram.ext import *
from telegram.update import Update
from telegram.bot import Bot
from telegram import ChatPermissions
import config
import mysql.connector
import csv

def get_msg_no(u_id):
    conn = mysql.connector.connect(user=config.db_user, password=config.db_pass, host=config.host, database=config.db)
    cur = conn.cursor()
    sql = "SELECT msg_id FROM msg_state WHERE u_id = %s"
    value = (u_id,)
    cur.execute(sql, value)
    result = cur.fetchone()
    conn.close()
    return result[0]

def msg_state(msg_no, u_id):
    conn = mysql.connector.connect(user=config.db_user, password=config.db_pass, host=config.host, database=config.db)
    cur = conn.cursor()
    sql = 'INSERT INTO msg_state (u_id, msg_id) VALUES (%s, %s)'    
    value = (u_id, msg_no)
    try:
        cur.execute(sql, value)
        conn.commit()
    except mysql.connector.IntegrityError:
        sql = 'UPDATE msg_state SET msg_id = %s WHERE u_id = %s'    
        value = (msg_no, u_id)
        cur.execute(sql, value)
        conn.commit()
    conn.close()

def respons(update: Update, context: CallbackContext):
    text = update.message.text
    u_id = update.effective_user.id
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    f_name = update.effective_user.first_name
    chat_type = update.effective_chat.type
    
    if chat_type == 'private':
        if text in ('/start', '/Start'):        
            bot.send_message(chat_id = chat_id, text = 'Please enter your name :')
            msg_state(1, u_id)
        elif text in ('/userinfo', '/Userinfo'):
            Send_userinfo(chat_id)
        else:
            msg_no = get_msg_no(u_id)
            if msg_no == 1:
                bot.send_message(chat_id = chat_id, text = 'Which platform do you offer marketing for? (eg: twitter, YouTube) :')
                msg_state(2, u_id)
                Update_db('name', text, u_id)
            elif msg_no == 2:
                bot.send_message(chat_id = chat_id, text = 'Please provide a link to your channel or portfolio :')
                msg_state(3, u_id)
                Update_db('platform', text, u_id)
            elif msg_no == 3:
                bot.send_message(chat_id = chat_id, text = 'Your telegram username :')
                msg_state(4, u_id)
                Update_db('link', text, u_id)
            elif msg_no == 4:
                Give_access(chat_id, u_id)
                msg_state(0, u_id)
                Update_db('username', text, u_id)

def Update_db(cmd, text, u_id):    
    conn = mysql.connector.connect(user=config.db_user, password=config.db_pass, host=config.host, database=config.db)
    cur = conn.cursor()
    if cmd == 'name':
        sql = 'INSERT INTO user_info (u_id, name) VALUES (%s, %s)'    
        value = (u_id, text)
        try:
            cur.execute(sql, value)
            conn.commit()
        except mysql.connector.IntegrityError:
            sql = 'UPDATE user_info SET name = %s WHERE u_id = %s'    
            value = (text, u_id)
            cur.execute(sql, value)
            conn.commit()
    else:
        sql = 'UPDATE user_info SET '+ cmd +' = %s WHERE u_id = %s'    
        value = (text, u_id)
        cur.execute(sql, value)
        conn.commit()
    conn.close()

def Give_access(chat_id, u_id):
    bot.restrictChatMember(
        chat_id = '@{}'.format(config.group),
        user_id = u_id, 
        permissions = ChatPermissions(
            can_send_messages = True, 
            can_send_media_messages = True, 
            can_send_polls = True, 
            can_send_other_messages = True
        )
    )
    inline = '{"inline_keyboard":[[{"text":"✅ Join the group chat","url":"https://t.me/'+ config.group +'"}]]}'
    bot.send_message(
        chat_id = chat_id, 
        text = 'Thanks for supporting us.', 
        reply_markup= inline
    )

def Send_group_link(chat_id):
    invite_link = bot.createChatInviteLink(
        chat_id = config.group, 
        member_limit = 1
    )
    bot.send_message(
        chat_id = chat_id, 
        text = 'Link to join our group: {}'.format(invite_link.invite_link)
    )

def Main_menu(chat_id, f_name):
    inline = '{"inline_keyboard":[[{"text":"Get Started","callback_data":"get_started"}]]}'
    bot.send_message(
        chat_id = chat_id, 
        text = 'Hello {} 👋.We ask some questions from you. You can get an invitation link to the group after completing all the questions.'.format(f_name), 
        reply_markup= inline
    )      

def group_status(update: Update, context: CallbackContext):
    if update.message.new_chat_members:
        for member in update.message.new_chat_members:
            bot.restrictChatMember(
                chat_id = update.effective_chat.id,
                user_id = member.id, 
                permissions = ChatPermissions(
                    can_send_messages = False, 
                    can_send_media_messages = False, 
                    can_send_polls = False, 
                    can_send_other_messages = False
                )
            )
            inline = '{"inline_keyboard":[[{"text":"👨🏼‍💻 Get Started","url":"http://t.me/Roshambo_Verification_Bot"}]]}'
            bot.send_message(
                chat_id = update.effective_chat.id, 
                text = 'Hello {} 👋. Welcome to the {} Group. Please go to the verification process using this button. 👇'.format(member.first_name, update.effective_chat.title), 
                reply_markup= inline
            )

def Send_userinfo(chat_id):
    conn = mysql.connector.connect(user=config.db_user, password=config.db_pass, host=config.host, database=config.db)
    cur = conn.cursor()
    sql = "SELECT * FROM user_info"
    cur.execute(sql, )
    result = cur.fetchall()
    with open("user_info.csv", "w", encoding='UTF-8') as f:
        writer = csv.writer(f, delimiter=",", lineterminator="\n")
        writer.writerow(['NAME', 'PLATFORM', 'LINK', 'USERNAME'])
        for I in result:
            writer.writerow([I[1], I[2], I[3], I[4]])
    bot.send_document(
        chat_id = chat_id, 
        document=open('user_info.csv', 'rb')
    )

if __name__ == '__main__':
    bot = Bot(config.token)
    updater = Updater(config.token, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text, respons))
    dp.add_handler(MessageHandler(Filters.status_update, group_status))
    updater.start_polling()
    updater.idle()
