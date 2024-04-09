import psycopg2
import telebot
import datetime
import time
import hashlib
import pyotp
import qrcode
from PIL import Image
from io import BytesIO
import logging

from dotenv import load_dotenv
import os

# Загрузка переменных окружения
load_dotenv()
token = os.getenv("BOT_TOKEN")
dbhost23 = os.getenv("DB_HOST")
dbport23 = os.getenv("DB_PORT")
dbname23 = os.getenv("DB_NAME")
dbuser23 = os.getenv("DB_USER")
dbpass23 = os.getenv("DB_PASS")

bot = telebot.TeleBot(token)

HELP = os.getenv("HELP")
HELPM0 = os.getenv("HELPM0")
HELPM1 = os.getenv("HELPM1")
HELPM2 = os.getenv("HELPM2")
HELPM3 = os.getenv("HELPM3")
LISTOFT = os.getenv("LISTOFT")
LISTOFR = os.getenv("LISTOFR")

# команда для вывода списка аудиторий, имеющихся в базе данных в системе (для уровней доступа - курсант, преподаватель, руководитель) 
@bot.message_handler(commands=["sh_rooms"])
def sh_rooms(message):
    try:
        conn = psycopg2.connect(database=dbname23, user=dbuser23, password=dbpass23, host=dbhost23, port=dbport23)
        conn.autocommit = True
        cursor = conn.cursor()
        sqlstr0 = 'SELECT chat_id, code_acl FROM active_list2 WHERE chat_id = '+str(message.chat.id)
        cursor.execute(sqlstr0)
        rows = cursor.fetchall()
        numcs = 0
        UserActive = 0
        for row in rows:
            numcs = numcs+1
            aclc = row[1]
            if ((numcs == 1) and (aclc > 0) and (aclc < 4)):
                UserActive = 1
        # если пользователь авторизовался в системе, формируем для него список комнат
        if UserActive == 1:
            ROOMSL = LISTOFR
            sqlstr0 = 'SELECT code, naim FROM rooms ORDER BY naim'
            cursor.execute(sqlstr0)
            rows = cursor.fetchall()
            numcs = 0
            UserActive = 0
            for row in rows:
                rcode = row[0]
                rnaim = row[1]
                if rcode < 100:
                    ROOMSL = ROOMSL + "\n" + rnaim
            bot.send_message(message.chat.id, ROOMSL)
        conn.close()
    except:
        bot.send_message(message.chat.id, 'Возникла ошибка при выполнении команды sh_rooms.')

# команда для вывода списка преподавателей, имеющихся в базе данных в системе (для уровней доступа - курсант, преподаватель, руководитель)
@bot.message_handler(commands=["sh_teachers"])
def sh_teachers(message):
    try:
        conn = psycopg2.connect(database=dbname23, user=dbuser23, password=dbpass23, host=dbhost23, port=dbport23)
        conn.autocommit = True
        cursor = conn.cursor()
        sqlstr0 = 'SELECT chat_id, code_acl FROM active_list2 WHERE chat_id = '+str(message.chat.id)
        cursor.execute(sqlstr0)
        rows = cursor.fetchall()
        numcs = 0
        UserActive = 0
        for row in rows:
            numcs = numcs+1
            aclc = row[1]
            if ((numcs == 1) and (aclc > 0) and (aclc < 4)):
                UserActive = 1
        # если пользователь авторизовался в системе, формируем для него список преподавателей
        if UserActive == 1:
            TEACHERSL = LISTOFT
            sqlstr0 = 'SELECT tabno, fio FROM teachers where (code_acl>1) ORDER BY tabno'
            cursor.execute(sqlstr0)
            rows = cursor.fetchall()
            numcs = 0
            UserActive = 0
            nrow0 = 0
            for row in rows:
                nrow0 = nrow0 + 1
                tabno = row[0]
                fio = row[1]
                if tabno < 100:
                    TEACHERSL = TEACHERSL + "\n" +str(nrow0)+': '+fio
            bot.send_message(message.chat.id, TEACHERSL)
        conn.close()
    except:
        bot.send_message(message.chat.id, 'Возникла ошибка при выполнении команды sh_teachers.')

# команда выхода из системы (сброса авторизации, для уровней доступа - не авторизован, курсант, преподаватель, руководитель)
@bot.message_handler(commands=["logout"])
def logout(message):
    try:
        conn = psycopg2.connect(database=dbname23, user=dbuser23, password=dbpass23, host=dbhost23, port=dbport23)
        conn.autocommit = True
        cursor = conn.cursor()
        # проверяем - находится ли текущий ChatID в списке активных пользователей
        # чтобы не выполнять команду выхода для еще не зашедшего в систему
        sqlstr0 = 'SELECT chat_id FROM active_list2 WHERE chat_id = '+str(message.chat.id)
        cursor.execute(sqlstr0)
        rows = cursor.fetchall()
        numcs = 0
        UserActive = 0
        for row in rows:
            numcs = numcs+1
            CodeChatID=row[0]
            if numcs == 1:
                UserActive = 1
        if UserActive == 1:
            sqlstr1 = 'DELETE FROM active_list2 WHERE chat_id = '+str(message.chat.id)
            cursor.execute(sqlstr1)
            bot.send_message(message.chat.id, 'Произведен выход пользователя из системы.')
        if UserActive == 0:
            bot.send_message(message.chat.id, 'Вы пока еще не авторизованы в системе.')
        conn.close()
    except:
        bot.send_message(message.chat.id, 'Возникла ошибка выхода пользователя из системы.')

# команда выдачи help пользователю с учетом его привилегий (0..3)
@bot.message_handler(commands=["help"])
def help(message):
    try:
        conn = psycopg2.connect(database=dbname23, user=dbuser23, password=dbpass23, host=dbhost23, port=dbport23)
        conn.autocommit = True
        cursor = conn.cursor()
        # проверяем - находится ли текущий ChatID в списке активных пользователей
        # чтобы понять какого рода список команд помощи ему выдать
        sqlstr0 = 'SELECT chat_id, tabno, code_acl FROM active_list2 WHERE chat_id = '+str(message.chat.id)
        cursor.execute(sqlstr0)
        rows = cursor.fetchall()
        numcs = 0
        UserActive = 0
        MandLabel = 0
        for row in rows:
            numcs = numcs+1
            MandLabel = row[2]
            if numcs == 1:
                UserActive = 1
        if ((UserActive == 1) and (MandLabel == 1)):
            bot.send_message(message.chat.id, HELPM1)
        if ((UserActive == 1) and (MandLabel == 2)):
            bot.send_message(message.chat.id, HELPM2)
        if ((UserActive == 1) and (MandLabel == 3)):
            bot.send_message(message.chat.id, HELPM3)
        if ((UserActive == 0) or (MandLabel == 0)):
            bot.send_message(message.chat.id, HELPM0)
        conn.close()
    except:
        bot.send_message(message.chat.id, 'Возникла ошибка вывода подсказки пользователю.')

user_data = {}
no_key_message = """
У вас ещё нет секретного ключа.
Чтобы получить, используйте команду
/get_secret_key
"""
# процедура авторизации пользователя в системе (для всех категорий пользователей, интерактивный ввод логина и пароля)
@bot.message_handler(commands=["login"])
def login(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    splitted_command = message.text.split(maxsplit=2)
    try:
        # получаем значение текущего времени
        now = datetime.datetime.now()
        # забираем логин и пароль из команды
        ttlogin = splitted_command[1]
        ttpass = splitted_command[2]
        user_data[chat_id]['login'] = ttlogin
        user_data[chat_id]['password'] = ttpass

        conn = psycopg2.connect(database=dbname23, user=dbuser23, password=dbpass23, host=dbhost23, port=dbport23)
        conn.autocommit = True
        cursor = conn.cursor()
        sqlstr_key_exist = 'SELECT chat_id, secret_key FROM users_secret WHERE chat_id = '+str(message.chat.id)
        cursor.execute(sqlstr_key_exist)
        res = len(cursor.fetchall())
        if res == 0:
            del user_data[chat_id]
            conn.close()
            bot.send_message(chat_id, no_key_message)
            return  # Прерываем выполнение обработчика

        # проверяем - не заблокирован ли текущий ChatID (текущий пользователь)
        # если заблокирован - выставляем маркер-переменую блокировки
        sqlstr0 = 'SELECT chat_id FROM blocked_list2 WHERE chat_id = '+str(message.chat.id)
        cursor.execute(sqlstr0)
        rows = cursor.fetchall()
        numcs = 0
        UserBlocked = 0
        for row in rows:
            numcs = numcs+1
            CodeChatID=row[0]
            if numcs == 1:
                UserBlocked = 1
        # проверяем - есть ли в списке имеющихся пользователей пользователь с логином и паролем - который предъявили для авторизации
        # если есть - выставляем маркер-переменную авторизации
        sqlstr = 'SELECT tabno, code_acl, fio FROM teachers where login='+"'"+ttlogin+"'"+' and intpasshash=MD5('+"'"+ttpass+"'"+');'
        cursor.execute(sqlstr)
        rows = cursor.fetchall()
        numcs = 0
        UserAuthorized = 0
        for row in rows:
            numcs = numcs+1
            CodeTeacher = row[0]
            CodeAcl = row[1]
            FIO = row[2]

            if numcs == 1:
                UserAuthorized = 1
                sqlstr_key = 'SELECT chat_id, secret_key FROM users_secret WHERE chat_id = '+str(message.chat.id)
                cursor.execute(sqlstr_key)
                secret_key = cursor.fetchone()[1]
                user_data[chat_id]['secret_key'] = secret_key
                user_data[chat_id]['FIO'] = FIO
                user_data[chat_id]['CodeTeacher'] = CodeTeacher
                user_data[chat_id]['CodeAcl'] = CodeAcl
        # если предъявленные логин и пароль есть в базе пользователей, и при этом пользователь не заблокирован
        # то стираем соответствующий chat_id из таблицы пытающихся авторизоваться (если они там есть)
        # и далее предлагаем пользователю ввести код
        if ((UserAuthorized == 1) and (UserBlocked == 0)):
            # удаляем chat_id из таблицы пытающихся
            sqlstr1 = 'DELETE FROM trying_list2 WHERE chat_id = '+str(message.chat.id)
            cursor.execute(sqlstr1)
            # удаляем chat_id из таблицы активных
            sqlstr2 = 'DELETE FROM active_list2 WHERE chat_id = '+str(message.chat.id)
            cursor.execute(sqlstr2)
            cursor.close()
            bot.send_message(message.chat.id, "теперь введите код")

        # если пользователь не авторизован но и не заблокирован - то он пытается авторизоваться
        # нужно найти его в таблице пытающихся и увеличить ему количество попыток авторизации на единицу
        # а при следующей проверке если попыток будет больше допустимого - заблокировать
        if ((numcs == 0) or (UserAuthorized == 0)) and (UserBlocked == 0):
            sqlstr4 = 'SELECT try_num FROM trying_list2 WHERE chat_id='+str(message.chat.id)+';'
            cursor.execute(sqlstr4)
            rows = cursor.fetchall()
            numcs = 0
            for row in rows:
                numcs = numcs+1
                TryNum=row[0]
            if numcs == 1:
                sqlstr6 = 'DELETE FROM trying_list2 WHERE chat_id='+str(message.chat.id)+';'
                cursor.execute(sqlstr6)
                sqlstr7 = 'INSERT INTO trying_list2(chat_id, try_num, add_info) VALUES('+str(message.chat.id)+', '+str(TryNum+1)+', '+"'"+str(now)+"'"+');'
                cursor.execute(sqlstr7)
                MessStr = 'Ошибка авторизации! Попытка №'+str(TryNum)+' из 5. Затем Вы будете заблокированы.'
                # если попытка авторизации неудачна - предупреждаем пользователя
                if TryNum < 5:
                    bot.send_message(message.chat.id, MessStr)
                # если слишком много попыток авторизации - то убираем chat_id из таблицы пытающихся
                # и переводит данный chat_id в таблицу заблокированных
                if TryNum >= 5:
                        sqlstr8 = 'DELETE FROM trying_list2 WHERE chat_id='+str(message.chat.id)+';'
                        cursor.execute(sqlstr8)
                        sqlstr9 = 'DELETE FROM blocked_list2 WHERE chat_id='+str(message.chat.id)+';'
                        cursor.execute(sqlstr9)
                        BlockedStr10 = 'Заблокирован '+str(now)
                        sqlstr10 = 'INSERT INTO blocked_list2(chat_id, time_from, add_info) VALUES('+str(message.chat.id)+', '+"'"+str(now)+"'"+', '+"'"+BlockedStr10+"'"+');'
                        cursor.execute(sqlstr10)
                        MessStr = 'Ошибка авторизации! Попытка №'+str(TryNum)+' из 5. Вы заблокированы.'
                        bot.send_message(message.chat.id, MessStr)
            # если это первая неудачная попытка авторизации - добавлем пользователя chat_id в таблицу пытающихся
            if numcs == 0:
                sqlstr5 = 'INSERT INTO trying_list2(chat_id, try_num, add_info) VALUES('+str(message.chat.id)+', 1, '+"'"+str(now)+"'"+');'
                cursor.execute(sqlstr5)
                bot.send_message(message.chat.id, 'Ошибка авторизации!')
        conn.close()
    # если что-то пошло не так во всей процедуре авторизации - просто сообщаем об этом в текущий чат пользователя
    except:
        del user_data[chat_id]
        bot.send_message(message.chat.id, 'Возникла ошибка авторизации.')
        conn.close()


# ввод кода после правильного ввода логина и пароля
@bot.message_handler(func=lambda message: 'login' in user_data.get(message.chat.id, {}))
def handle_2fa_code(message):
    chat_id = message.chat.id
    try:
        conn = psycopg2.connect(database=dbname23, user=dbuser23, password=dbpass23, host=dbhost23, port=dbport23)
        conn.autocommit = True
        cursor = conn.cursor()
        now = datetime.datetime.now()
        chat_id = message.chat.id
        FIO = user_data[chat_id]['FIO']
        CodeAcl = user_data[chat_id]['CodeAcl']
        CodeTeacher = user_data[chat_id]['CodeTeacher']
        secret_key = user_data[chat_id]['secret_key']
        entered_code = message.text

        # user_data[chat_id]['code_try_num'] = 0
        # code_try_num = user_data[chat_id]['code_try_num']

        # проверяем - не заблокирован ли текущий ChatID
        # если заблокирован - выставляем маркер блокировки
        sqlstr0 = 'SELECT chat_id FROM blocked_list2 WHERE chat_id = ' + str(message.chat.id)
        cursor.execute(sqlstr0)
        rows = cursor.fetchone()
        numcs = 0
        UserBlocked = 0
        if rows:
            UserBlocked = 1

        # Создаем объект TOTP с использованием секретного ключа
        totp = pyotp.TOTP(secret_key)

        # Проверяем введенный код
        if totp.verify(entered_code):
            # Одноразовый код верен, пользователь успешно вошел
            sqlstr1 = 'DELETE FROM trying_list2 WHERE chat_id = ' + str(message.chat.id)
            cursor.execute(sqlstr1)
            # вновь записываем chat_id в active_list2(обновляем последнее время активности для данного chat_id)
            sqlstr2 = 'DELETE FROM active_list2 WHERE chat_id = ' + str(message.chat.id)
            addinfo = 'Пользователь ' + FIO + ' авторизовался ' + str(
                now) + '.' + "\n" + 'Выход по команде' + "\n" + '/logout' + "\n" + 'Продуктивной работы!'
            sqlstr3 = 'INSERT INTO active_list2(chat_id, tabno, code_acl, last_active_time, add_info) VALUES(' + str(
                message.chat.id) + ', ' + str(CodeTeacher) + ', ' + str(CodeAcl) + ', ' + "'" + str(
                now) + "'" + ', ' + "'" + addinfo + "'" + ');'
            cursor.execute(sqlstr2)
            cursor.execute(sqlstr3)
            bot.send_message(message.chat.id, addinfo)
            del user_data[chat_id]  # Удаляем временные данные
        else:

            if (numcs == 0) and (UserBlocked == 0):
                # code_try_num += 1
                sqlstr4 = 'SELECT try_num FROM trying_list2 WHERE chat_id=' + str(message.chat.id) + ';'
                cursor.execute(sqlstr4)
                rows = cursor.fetchone()
                numcs = 0
                if rows:
                    numcs += 1
                    TryNum = rows[0]
                if numcs == 1:
                    sqlstr6 = 'DELETE FROM trying_list2 WHERE chat_id=' + str(message.chat.id) + ';'
                    cursor.execute(sqlstr6)
                    sqlstr7 = 'INSERT INTO trying_list2(chat_id, try_num, add_info) VALUES(' + str(
                        message.chat.id) + ', ' + str(TryNum + 1) + ', ' + "'" + str(now) + "'" + ');'
                    cursor.execute(sqlstr7)
                    MessStr = 'Неверный код! Попытка №' + str(TryNum) + ' из 5. Затем Вы будете заблокированы.'
                    # если попытка авторизации неудачна - предупреждаем пользователя
                    if TryNum < 5:
                        bot.send_message(message.chat.id, MessStr)
                    # если слишком много попыток авторизации - то убираем chat_id из таблицы пытающихся
                    # и переводим данный chat_id в таблицу заблокированных
                    if TryNum >= 5:
                        sqlstr8 = 'DELETE FROM trying_list2 WHERE chat_id=' + str(message.chat.id) + ';'
                        cursor.execute(sqlstr8)
                        sqlstr9 = 'DELETE FROM blocked_list2 WHERE chat_id=' + str(message.chat.id) + ';'
                        cursor.execute(sqlstr9)
                        BlockedStr10 = 'Заблокирован ' + str(now)
                        sqlstr10 = 'INSERT INTO blocked_list2(chat_id, time_from, add_info) VALUES(' + str(
                            message.chat.id) + ', ' + "'" + str(now) + "'" + ', ' + "'" + BlockedStr10 + "'" + ');'
                        cursor.execute(sqlstr10)
                        MessStr = 'Неверный код! Попытка №' + str(TryNum) + ' из 5. Вы заблокированы.'
                        bot.send_message(message.chat.id, MessStr)

                        del user_data[chat_id]
                        conn.close()
                        return

                # если это первая неудачная попытка авторизации - добавлем пользователя chat_id в таблицу пытающихся
                if numcs == 0:
                    sqlstr5 = 'INSERT INTO trying_list2(chat_id, try_num, add_info) VALUES(' + str(
                        message.chat.id) + ', 1, ' + "'" + str(now) + "'" + ');'
                    cursor.execute(sqlstr5)
                    # code_try_num += 1
                    bot.send_message(message.chat.id, 'Неверный код!')
            conn.close()

            #bot.send_message(chat_id, "Неверный одноразовый код.")
            #del user_data[chat_id]
            #conn.close()
            #return
        conn.close()
    except:
        del user_data[chat_id]
        bot.send_message(message.chat.id, 'Возникла ошибка авторизации')


def generate_secret_key():
    secret = pyotp.random_base32()
    return secret

def send_qr_code(chat_id, secret_key):
    totp = pyotp.TOTP(secret_key)
    uri = totp.provisioning_uri(name=str(chat_id), issuer_name='tt2023')

    img = qrcode.make(uri)
    img_bytes_io = BytesIO()
    img = img.convert("RGB")
    img.save(img_bytes_io, 'JPEG')
    img_bytes_io.seek(0)

    sent_message = bot.send_photo(chat_id, img_bytes_io)
    return sent_message

mess = """
Внимание: 
Ключ будет выдан однократно.
Затем ключ будет удалён из этого чата через 5 минут.
Если вы не успеете отсканировать qr-код за это время, либо не сохраните ключ в текстовом виде, вы не сможете запросить их повторно.
Для подтверждения используйте команду:

/yes
"""
# получение секретного ключа - начало
@bot.message_handler(commands=['get_secret_key'])
def get_secret_key1(message):
    chat_id = message.chat.id
    try:
        conn = psycopg2.connect(database=dbname23, user=dbuser23, password=dbpass23, host=dbhost23, port=dbport23)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users_secret WHERE chat_id = %s", (chat_id,))
        existing_record = cursor.fetchone()

        if existing_record:
            # Если запись уже существует, сообщаем пользователю
            bot.send_message(chat_id, "У вас уже есть секретный ключ.")
        else:
            bot.send_message(chat_id, mess)
    except:
        bot.send_message(chat_id, "Возникла ошибка")

log_filename = 'bot_log.txt'
logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('tt2023')

@bot.message_handler(commands=['yes'])
def get_secret_key(message):
    try:
        chat_id = message.chat.id

        conn = psycopg2.connect(database=dbname23, user=dbuser23, password=dbpass23, host=dbhost23, port=dbport23)
        conn.autocommit = True
        cursor = conn.cursor()

        # Проверяем, есть ли уже запись для данного chat_id
        cursor.execute("SELECT * FROM users_secret WHERE chat_id = %s", (chat_id,))
        existing_record = cursor.fetchone()

        if existing_record:
            # Если запись уже существует, сообщаем пользователю
            bot.send_message(chat_id, "У вас уже есть секретный ключ.")
        else:
            # Если записи нет, генерируем новый секретный ключ
            secret_key = generate_secret_key()

            # Вставляем новую запись в базу данных
            cursor.execute("INSERT INTO users_secret (chat_id, secret_key) VALUES (%s, %s)", (chat_id, secret_key))
            conn.commit()

            # Отправляем секретный ключ пользователю
            msg_qr = bot.send_message(chat_id, f"Ваш секретный ключ для сканирования: ")
            msg_qr_send = send_qr_code(chat_id, secret_key)
            msg_secret_key = bot.send_message(chat_id, f"Ваш секретный ключ для ввода вручную: ")
            msg_secret_key_send = bot.send_message(chat_id, f"{secret_key}")

            # Задержка перед удалением сообщений
            time.sleep(10)  # 300 секунд (5 минут)

            # Удаляем сообщения бота
            logger.info("Попытка удаления сообщений")
            try:
                # Замените `message_id` на правильные значения для каждого сообщения
                bot.delete_message(chat_id, msg_qr.message_id)
                bot.delete_message(chat_id, msg_qr_send.message_id)
                bot.delete_message(chat_id, msg_secret_key.message_id)
                bot.delete_message(chat_id, msg_secret_key_send.message_id)
                logger.info("Сообщения успешно удалены")
            except Exception as e:
                logger.error(f"Ошибка при удалении сообщений: {str(e)}")

            # Закрываем соединение с базой данных
            cursor.close()
            conn.close()
    except:
        bot.send_message(message.chat.id, 'Возникла ошибка')
# получение секретного ключа - окончание


# процедура просмотра расписания преподавателя + листов замены для него + невыходов + задач (задач - для преподавателей и руководства)
@bot.message_handler(commands=["sh_tt"])
def sh_tt(message):
    try:
        OrigTgrCommand = message.text
        splitted_command = message.text.split(maxsplit=2)
        if len(OrigTgrCommand) >= 15:
            # читаем дату
            sqldate = splitted_command[1]
            # читаем ФИО
            sqlfio = splitted_command[2]
            conn = psycopg2.connect(database=dbname23, user=dbuser23, password=dbpass23, host=dbhost23, port=dbport23)
            conn.autocommit = True
            cursor = conn.cursor()
            # проверяем авторизовался ли пользователь
            sqlstr0 = 'SELECT chat_id, code_acl FROM active_list2 WHERE chat_id = '+str(message.chat.id)
            cursor.execute(sqlstr0)
            rows = cursor.fetchall()
            numcs = 0
            UserActive = 0
            for row in rows:
                numcs = numcs+1
                aclc = row[1]
                if ((numcs == 1) and (aclc > 0) and (aclc < 4)):
                    UserActive = 1
            # если авторизовался - выполняем нужный запрос
            if UserActive == 1:
                sqlstr = 'SELECT tabno, fio FROM teachers WHERE fio LIKE '+"'%"+sqlfio+"%'"
                cursor.execute(sqlstr)
                rows = cursor.fetchall()
                numcs = 0
                for row in rows:
                    numcs = numcs+1
                    CodeTeacher=row[0]
                    FioTeachr=row[1]
                # если нашли такого преподавателя, причем у него код в диапазоне от 1 до 99, то формируем ответ на запрос - по РАСПИСАНИЮ
                if ((CodeTeacher >= 1) and (CodeTeacher <= 99)):
                    SqlStr0='select tt.ttdate, tt.codepair, pr.timefrom, pr.timeto, sj.naim as subjectnaim, pt.naim as pairtypenaim, tt.theme, tt.groupslist, tc.fio, rm.naim as roomnaim '
                    SqlStr1='from timetable tt, teachers tc, pairs pr, rooms rm, subjects sj, pairtypes  pt '
                    SqlStr2='where ((tt.ttdate='+"'"+sqldate+"'"+') and (tt.codeteacher='+str(CodeTeacher)+') '
                    SqlStr3='and (tc.tabno=tt.codeteacher) and (pr.nopp=tt.codepair) and (rm.code=tt.coderoom) and (sj.code=tt.codesubject) and (pt.code=tt.codesubjtype)) '
                    SqlStr4='order by codepair'
                    SqlStr20=SqlStr0+SqlStr1+SqlStr2+SqlStr3+SqlStr4
                    cursor.execute(SqlStr20)
                    ResultMessage = ''
                    ResultMessage = 'Найдено записей в РАСПИСАНИИ: ' + str(cursor.rowcount)+'. '
                    ResultMessage = ResultMessage + "\n" + "\n"
                    rows = cursor.fetchall()
                    numcs = 0
                    for row in rows:
                        numcs = numcs+1
                        ResultMessage = ResultMessage + str(numcs)+') '+str(row[1])+'-я пара ('+str(row[2])+'-'+str(row[3])+')'+"\n"+str(row[4])+' ('+str(row[5])+')'+"\n"+'Тема: '+str(row[6])+"\n"+'Группа(ы): '+str(row[7])+"\n"+'Ауд.: '+ str(row[9])+"\n"+'Преп.: '+str(row[8])+"\n"+"\n"
                    ResultMessage = ResultMessage + "\n"
                    # если нашли такого преподавателя, причем у него код в диапазоне от 1 до 99, то формируем ответ на запрос
                    # теперь по ЛИСТАМ ЗАМЕНЫ на этого преподавателя - кого он замещает
                    SqlStr10='select lc.grouplist, lc.codepair, pr.timefrom, pr.timeto, tc.fio as fioplan, ab.naim as absnaim '
                    SqlStr11='from listofchanges lc, teachers tc, pairs pr, absenteeisms ab '
                    SqlStr12='where ((lc.lcdate='+"'"+sqldate+"'"+') and (lc.codeteacherfact='+str(CodeTeacher)+') '
                    SqlStr13='and (lc.codeteacherplan=tc.tabno) and (lc.codepair=pr.nopp) and (lc.codeabs=ab.code)) '
                    SqlStr14='order by codepair'
                    SqlStr120=SqlStr10+SqlStr11+SqlStr12+SqlStr13+SqlStr14
                    cursor.execute(SqlStr120)
                    rows2 = cursor.fetchall()
                    ResultMessage = ResultMessage+'Найдено записей в ЛИСТАХ ЗАМЕНЫ: ' + str(cursor.rowcount)+'. '
                    ResultMessage = ResultMessage + "\n" + "\n"
                    numcs = 0
                    for row in rows2:
                        numcs = numcs+1
                        ResultMessage = ResultMessage + str(numcs)+') '+str(row[1])+'-я пара ('+str(row[2])+'-'+str(row[3])+')'+"\n"+'Группа(ы): '+str(row[0])+"\n"+'Преп. (план): '+str(row[4])+"\n"+'Причина: '+str(row[5])+"\n"+"\n"
                    ResultMessage = ResultMessage + "\n"
                    # теперь посмотрим на невыходы - м.б. он в отпуске или болен и т.п. Если есть такие записи - сообщим!
                    SqlStr100='select tc.fio, ta.datefrom, ta.dateto, ab.naim '
                    SqlStr101='from teachers_absence ta, teachers tc, absenteeisms ab '
                    SqlStr102='where ((ta.codeteacher='+str(CodeTeacher)+') and (ta.datefrom<='+"'"+sqldate+"'"+') '
                    SqlStr103='and (ta.dateto>='+"'"+sqldate+"'"+') and (tc.tabno=ta.codeteacher) and (ta.codeabsent=ab.code));'
                    SqlStr105=SqlStr100+SqlStr101+SqlStr102+SqlStr103
                    cursor.execute(SqlStr105)
                    rows3 = cursor.fetchall()
                    numcs = 0
                    ResultMessage = ResultMessage+'Найдено записей в НЕВЫХОДАХ: ' + str(cursor.rowcount)+'. '
                    ResultMessage = ResultMessage + "\n" + "\n"
                    for row in rows3:
                        numcs = numcs+1
                        ResultMessage = ResultMessage + str(numcs)+') '+sqldate+' - '+str(row[3])+"\n"+'Преп.: '+str(row[0])+"\n"+"\n"
                    ResultMessage = ResultMessage + "\n"
                    if ((aclc > 1) and (aclc < 4)):
                        if ((CodeTeacher >= 1) and (CodeTeacher <= 199)):
                            SqlStr0='select zz.nopp_z, zz.time_begin, zz.time_end, zz.zadacha, tc.fio '
                            SqlStr1='from zadachi zz, teachers tc '
                            SqlStr2='where ((zz.zdate='+"'"+sqldate+"'"+') and (zz.tabno_isp='+str(CodeTeacher)+') '
                            SqlStr3='and (tc.tabno=zz.tabno_por)) '
                            SqlStr4='order by nopp_z'
                            SqlStr20=SqlStr0+SqlStr1+SqlStr2+SqlStr3+SqlStr4
                            cursor.execute(SqlStr20)
                            ResultMessage = ResultMessage + 'Найдено записей в ЗАДАЧАХ: ' + str(cursor.rowcount)+'. '
                            ResultMessage = ResultMessage + "\n" + "\n"
                            rows = cursor.fetchall()
                            numcs = 0
                            for row in rows:
                                numcs = numcs+1
                                ResultMessage = ResultMessage + str(numcs)+') '+str(row[0])+'-я задача ('+str(row[1])+'-'+str(row[2])+')'+"\n"+str(row[3])+'.'+"\n"+' (Пост. - '+str(row[4])+');'+"\n"+"\n";
                            ResultMessage = ResultMessage + "\n"
                    bot.send_message(message.chat.id, ResultMessage)
                    conn.close()
            else:
                bot.send_message(message.chat.id, "Вы не авторизованы.")
        else:
            bot.send_message(message.chat.id, "Слишком короткая команда! Правильный пример: '/sh_tt 10.07.2023 Иванов И.И.'.")
    except:
        bot.send_message(message.chat.id, 'Не удалось выполнить запрос!')

# процедура просмотра задач преподавателя (для преподавателей и руководителей)
@bot.message_handler(commands=["sh_tasks"])
def sh_tasks(message):
    try:
        OrigTgrCommand = message.text
        splitted_command = message.text.split(maxsplit=2)
        if len(OrigTgrCommand) >= 15:
            # читаем дату
            sqldate = splitted_command[1]
            # читаем ФИО
            sqlfio = splitted_command[2]
            conn = psycopg2.connect(database=dbname23, user=dbuser23, password=dbpass23, host=dbhost23, port=dbport23)
            conn.autocommit = True
            cursor = conn.cursor()
            # проверяем авторизовался ли пользователь
            sqlstr0 = 'SELECT chat_id, code_acl FROM active_list2 WHERE chat_id = '+str(message.chat.id)
            cursor.execute(sqlstr0)
            rows = cursor.fetchall()
            numcs = 0
            UserActive = 0
            for row in rows:
                numcs = numcs+1
                aclc = row[1]
                if ((numcs == 1) and (aclc > 1) and (aclc < 4)):
                    UserActive = 1
            # если авторизовался - выполняем нужный запрос
            if UserActive == 1:
                sqlstr = 'SELECT tabno, fio FROM teachers WHERE fio LIKE '+"'%"+sqlfio+"%'"
                cursor.execute(sqlstr)
                rows = cursor.fetchall()
                numcs = 0
                for row in rows:
                    numcs = numcs+1
                    CodeTeacher=row[0]
                    FioTeachr=row[1]
                # если нашли такого преподавателя, причем у него код в диапазоне от 1 до 199, то формируем ответ на запрос
                if ((CodeTeacher >= 1) and (CodeTeacher <= 199)):
                    SqlStr0='select zz.nopp_z, zz.time_begin, zz.time_end, zz.zadacha, tc.fio '
                    SqlStr1='from zadachi zz, teachers tc '
                    SqlStr2='where ((zz.zdate='+"'"+sqldate+"'"+') and (zz.tabno_isp='+str(CodeTeacher)+') '
                    SqlStr3='and (tc.tabno=zz.tabno_por)) '
                    SqlStr4='order by nopp_z'
                    SqlStr20=SqlStr0+SqlStr1+SqlStr2+SqlStr3+SqlStr4
                    cursor.execute(SqlStr20)
                    ResultMessage = ''
                    ResultMessage = 'Найдено записей в задачах: ' + str(cursor.rowcount)+'. '
                    ResultMessage = ResultMessage + "\n" + "\n"
                    rows = cursor.fetchall()
                    numcs = 0
                    for row in rows:
                        numcs = numcs+1
                        ResultMessage = ResultMessage + str(numcs)+') '+str(row[0])+'-я задача ('+str(row[1])+'-'+str(row[2])+')'+"\n"+str(row[3])+'.'+"\n"+' (Пост. - '+str(row[4])+');'+"\n"+"\n"
                    bot.send_message(message.chat.id, ResultMessage)
                    conn.close()
            else:
                bot.send_message(message.chat.id, "Вы не авторизованы или недостаточно полномочий на выполнение команды.")
        else:
            bot.send_message(message.chat.id, "Слишком короткая команда! Правильный пример: '/sh_tt 10.07.2023 Иванов И.И.'.")
    except:
        bot.send_message(message.chat.id, 'Не удалось выполнить запрос!')

# процедура добавления задачи пользователя самому себе (для уровней доступа - преподаватель, руководитель)
@bot.message_handler(commands=["add_task"])
def add_task(message):
    try:
        OrigTgrCommand = message.text
        splitted_command = message.text.split(maxsplit=4)
        if len(OrigTgrCommand) >= 15:
            # читаем дату
            sqldate = splitted_command[1]
            # читаем =время с=
            sqltimefrom = splitted_command[2]
            # читаем =время по=
            sqltimeto = splitted_command[3]
            # читаем саму задачу, которую надо добавить в планировщик
            sqltask = splitted_command[4]
            conn = psycopg2.connect(database=dbname23, user=dbuser23, password=dbpass23, host=dbhost23, port=dbport23)
            conn.autocommit = True
            cursor = conn.cursor()
            # проверяем авторизовался ли пользователь
            sqlstr0 = 'SELECT chat_id, code_acl, tabno FROM active_list2 WHERE chat_id = '+str(message.chat.id)
            cursor.execute(sqlstr0)
            rows = cursor.fetchall()
            numcs = 0
            UserActive = 0
            for row in rows:
                numcs = numcs+1
                aclc = row[1]
                tabnoc = row[2]
                if ((numcs == 1) and (aclc > 1) and (aclc < 4)):
                    UserActive = 1
            # если авторизовался - выполняем нужный запрос
            if UserActive == 1:
                sqlstr = 'SELECT tabno, fio FROM teachers WHERE tabno = '+str(tabnoc)
                cursor.execute(sqlstr)
                rows = cursor.fetchall()
                numcs = 0
                for row in rows:
                    numcs = numcs+1
                    CodeTeacher=row[0]
                    FioTeachr=row[1]
                # если нашли такого преподавателя, причем у него код в диапазоне от 1 до 199, то формируем ответ на запрос
                if ((CodeTeacher >= 1) and (CodeTeacher <= 199)):
                    SqlStr0='select zz.nopp_z, zz.time_begin, zz.time_end, zz.zadacha, tc.fio '
                    SqlStr1='from zadachi zz, teachers tc '
                    SqlStr2='where ((zz.zdate='+"'"+sqldate+"'"+') and (zz.tabno_isp='+str(CodeTeacher)+') '
                    SqlStr3='and (tc.tabno=zz.tabno_por)) '
                    SqlStr4='order by nopp_z'
                    SqlStr20=SqlStr0+SqlStr1+SqlStr2+SqlStr3+SqlStr4
                    cursor.execute(SqlStr20)
                    ResultMessage = 'Задача будет создана с номером ' + str(cursor.rowcount+1)+'. '
                    ResultMessage = ResultMessage + "\n" + "\n"
                    rows = cursor.fetchall()
                    numcs = cursor.rowcount
                    # for row in rows:
                    #    numcs = numcs+1
                    #    ResultMessage = ResultMessage + str(numcs)+') '+str(row[0])+'-я задача ('+str(row[1])+'-'+str(row[2])+')'+PERSTR+str(row[3])+'.'+PERSTR+' (Пост. - '+str(row[4])+');'+PERSTR+PERSTR
                    SqlStr0='insert into zadachi (ZDATE, TIME_BEGIN, TIME_END, NOPP_Z, TABNO_POR, TABNO_ISP, ZADACHA) values '
                    SqlStr1='('+"'"+sqldate+"'"+', '+"'"+sqltimefrom+"'"+', '+"'"+sqltimeto+"'"+', '+str(numcs+1)+', '+str(tabnoc)+', '+str(tabnoc)+', '+"'"+sqltask+"'"+')'
                    SqlStr30=SqlStr0+"\n"+SqlStr1
                    cursor.execute(SqlStr30)
                    ResultMessage = ResultMessage+'Готово! '
                    ResultMessage = ResultMessage + "\n" + "\n"
                    SqlStr0='select zz.nopp_z, zz.time_begin, zz.time_end, zz.zadacha, tc.fio '
                    SqlStr1='from zadachi zz, teachers tc '
                    SqlStr2='where ((zz.zdate='+"'"+sqldate+"'"+') and (zz.tabno_isp='+str(CodeTeacher)+') '
                    SqlStr3='and (tc.tabno=zz.tabno_por)) '
                    SqlStr4='order by nopp_z'
                    SqlStr20=SqlStr0+SqlStr1+SqlStr2+SqlStr3+SqlStr4
                    cursor.execute(SqlStr20)
                    ResultMessage = ResultMessage+'Обновленный перечень содержит задач: ' + str(cursor.rowcount)
                    ResultMessage = ResultMessage + "\n" + "\n"
                    rows = cursor.fetchall()
                    numcs1 = 0
                    for row in rows:
                        numcs1 = numcs1+1
                        ResultMessage = ResultMessage + str(numcs1)+') '+str(row[0])+'-я задача ('+str(row[1])+'-'+str(row[2])+')'+"\n"+str(row[3])+'.'+"\n"+' (Пост. - '+str(row[4])+');'+"\n"+"\n"
                    bot.send_message(message.chat.id, ResultMessage)
                    conn.close()
            else:
                bot.send_message(message.chat.id, "Вы не авторизованы или недостаточно полномочий на выполнение команды.")
        else:
            bot.send_message(message.chat.id, "Слишком короткая команда! Правильный пример: '/add_task 10.07.2023 09:00 10:00 Поездка в ВГУ'.")
    except:
        bot.send_message(message.chat.id, 'Не удалось выполнить запрос!')

# процедура удаления задачи пользователя у самого себя (для уровней доступа - преподаватель, руководитель)
@bot.message_handler(commands=["del_task"])
def del_task(message):
    try:
        OrigTgrCommand = message.text
        splitted_command = message.text.split(maxsplit=2)
        if len(OrigTgrCommand) >= 15:
            # читаем дату
            sqldate = splitted_command[1]
            # читаем номер задачи
            sqltasknum = splitted_command[2]
            conn = psycopg2.connect(database=dbname23, user=dbuser23, password=dbpass23, host=dbhost23, port=dbport23)
            conn.autocommit = True
            cursor = conn.cursor()
            # проверяем авторизовался ли пользователь
            sqlstr0 = 'SELECT chat_id, code_acl, tabno FROM active_list2 WHERE chat_id = '+str(message.chat.id)
            cursor.execute(sqlstr0)
            rows = cursor.fetchall()
            numcs = 0
            UserActive = 0
            for row in rows:
                numcs = numcs+1
                aclc = row[1]
                tabnoc = row[2]
                if ((numcs == 1) and (aclc > 1) and (aclc < 4)):
                    UserActive = 1
            # если авторизовался - выполняем нужный запрос
            if UserActive == 1:
                sqlstr = 'SELECT tabno, fio FROM teachers WHERE tabno = '+str(tabnoc)
                cursor.execute(sqlstr);
                rows = cursor.fetchall();
                numcs = 0
                for row in rows:
                    numcs = numcs+1
                    CodeTeacher=row[0]
                    FioTeachr=row[1]
                # если нашли такого преподавателя, причем у него код в диапазоне от 1 до 199, то формируем запрос на удаление задачи из списка задач
                if ((CodeTeacher >= 1) and (CodeTeacher <= 199)):
                    SqlStr0='delete from zadachi '
                    SqlStr1='where ((zdate='+"'"+sqldate+"'"+') and (nopp_z='+str(sqltasknum)+') and (tabno_isp='+str(tabnoc)+') and (tabno_por='+str(tabnoc)+'))'
                    SqlStr40=SqlStr0+"\n"+SqlStr1
                    cursor.execute(SqlStr40)
                    ResultMessage = 'Запрос выполнен!'
                    ResultMessage = ResultMessage + "\n" + "\n"
                    SqlStr0='select zz.nopp_z, zz.time_begin, zz.time_end, zz.zadacha, tc.fio '
                    SqlStr1='from zadachi zz, teachers tc '
                    SqlStr2='where ((zz.zdate='+"'"+sqldate+"'"+') and (zz.tabno_isp='+str(CodeTeacher)+') '
                    SqlStr3='and (tc.tabno=zz.tabno_por)) '
                    SqlStr4='order by nopp_z'
                    SqlStr20=SqlStr0+SqlStr1+SqlStr2+SqlStr3+SqlStr4
                    cursor.execute(SqlStr20)
                    ResultMessage = ResultMessage+'Обновленный перечень содержит задач: ' + str(cursor.rowcount)
                    ResultMessage = ResultMessage + "\n" + "\n"
                    rows = cursor.fetchall()
                    numcs1 = 0
                    for row in rows:
                        numcs1 = numcs1+1
                        ResultMessage = ResultMessage + str(numcs1)+') '+str(row[0])+'-я задача ('+str(row[1])+'-'+str(row[2])+')'+"\n"+str(row[3])+'.'+"\n"+' (Пост. - '+str(row[4])+');'+"\n"+"\n"
                    bot.send_message(message.chat.id, ResultMessage)
                    conn.close()
            else:
                bot.send_message(message.chat.id, "Вы не авторизованы или недостаточно полномочий для выполнения команды!")
        else:
            bot.send_message(message.chat.id, "Слишком короткая команда! Правильный пример: '/del_task 10.07.2023 6'")
    except:
        bot.send_message(message.chat.id, 'Не удалось выполнить запрос!')

# процедура добавления задачи руководителя пользователю (для уровней доступа - руководитель)
@bot.message_handler(commands=["add_directive"])
def add_directive(message):
    try:
        OrigTgrCommand = message.text
        splitted_command = message.text.split(maxsplit=6)
        if len(OrigTgrCommand) >= 15:
            # читаем дату
            sqldate = splitted_command[1]
            # читаем =время с=
            sqltimefrom = splitted_command[2]
            # читаем =время по=
            sqltimeto = splitted_command[3]
            # читаем фамилию пользователя, которому добавляем задачу
            sqluserfam = splitted_command[4]
            # читаем И.О. пользователя, которому добавляем задачу
            sqluserio = splitted_command[5]
            # формируем из фамилии и имени и отчества ФАмилию И.Ю. пользователя, которому нужно добавить задачу
            sqluserfio = sqluserfam + ' ' + sqluserio
            print(sqluserfio)
            # читаем саму задачу, которую надо добавить в планировщик
            sqltask = splitted_command[6]
            conn = psycopg2.connect(database=dbname23, user=dbuser23, password=dbpass23, host=dbhost23, port=dbport23)
            conn.autocommit = True
            cursor = conn.cursor()
            # проверяем авторизовался ли пользователь
            sqlstr0 = 'SELECT chat_id, code_acl, tabno FROM active_list2 WHERE chat_id = '+str(message.chat.id)
            cursor.execute(sqlstr0)
            rows = cursor.fetchall()
            numcs = 0
            UserActive = 0
            for row in rows:
                numcs = numcs+1
                aclc = row[1]
                tabnoc = row[2]
                if ((numcs == 1) and (aclc > 2) and (aclc < 4)):
                    UserActive = 1
            # если авторизовался - выполняем нужный запрос  но сначала
            # проверим нашелся ли в базе сотрудников тот кому руководитель планирует записать задачу
            sqlstr1 = 'SELECT tabno, fio FROM teachers WHERE fio = '+"'"+str(sqluserfio)+"'"
            cursor.execute(sqlstr1)
            rows = cursor.fetchall()
            numcs = 0
            CtrlUserFound = 0
            for row in rows:
                numcs = numcs+1
                fio_ctrluser = row[1]
                tabno_ctrluser = row[0]
                if (numcs == 1):
                    CtrlUserFound = 1
            if ((UserActive == 1) and (CtrlUserFound == 1)):
                sqlstr = 'SELECT tabno, fio FROM teachers WHERE tabno = '+str(tabno_ctrluser)
                cursor.execute(sqlstr)
                rows = cursor.fetchall()
                numcs = 0
                for row in rows:
                    numcs = numcs+1
                    CodeTeacher=row[0]
                    FioTeachr=row[1]
                # если нашли такого преподавателя, причем у него код в диапазоне от 1 до 199, то формируем ответ на запрос
                if ((CodeTeacher >= 1) and (CodeTeacher <= 199)):
                    SqlStr0='select zz.nopp_z, zz.time_begin, zz.time_end, zz.zadacha, tc.fio '
                    SqlStr1='from zadachi zz, teachers tc '
                    SqlStr2='where ((zz.zdate='+"'"+sqldate+"'"+') and (zz.tabno_isp='+str(CodeTeacher)+') '
                    SqlStr3='and (tc.tabno=zz.tabno_por)) '
                    SqlStr4='order by nopp_z'
                    SqlStr20=SqlStr0+SqlStr1+SqlStr2+SqlStr3+SqlStr4
                    cursor.execute(SqlStr20)
                    ResultMessage = 'Задача будет создана с номером ' + str(cursor.rowcount+1)+'. '
                    ResultMessage = ResultMessage + "\n" + "\n"
                    rows = cursor.fetchall()
                    numcs = cursor.rowcount
                    # for row in rows:
                    #    numcs = numcs+1
                    #    ResultMessage = ResultMessage + str(numcs)+') '+str(row[0])+'-я задача ('+str(row[1])+'-'+str(row[2])+')'+"\n"+str(row[3])+'.'+"\n"+' (Пост. - '+str(row[4])+');'+"\n"+"\n"
                    SqlStr0='insert into zadachi (ZDATE, TIME_BEGIN, TIME_END, NOPP_Z, TABNO_POR, TABNO_ISP, ZADACHA) values '
                    SqlStr1='('+"'"+sqldate+"'"+', '+"'"+sqltimefrom+"'"+', '+"'"+sqltimeto+"'"+', '+str(numcs+1)+', '+str(tabnoc)+', '+str(tabno_ctrluser)+', '+"'"+sqltask+"'"+')'
                    SqlStr30=SqlStr0+"\n"+SqlStr1
                    cursor.execute(SqlStr30)
                    ResultMessage = ResultMessage+'Готово! '
                    ResultMessage = ResultMessage + "\n" + "\n"
                    SqlStr0='select zz.nopp_z, zz.time_begin, zz.time_end, zz.zadacha, tc.fio '
                    SqlStr1='from zadachi zz, teachers tc '
                    SqlStr2='where ((zz.zdate='+"'"+sqldate+"'"+') and (zz.tabno_isp='+str(CodeTeacher)+') '
                    SqlStr3='and (tc.tabno=zz.tabno_por)) '
                    SqlStr4='order by nopp_z'
                    SqlStr20=SqlStr0+SqlStr1+SqlStr2+SqlStr3+SqlStr4
                    cursor.execute(SqlStr20)
                    ResultMessage = ResultMessage+'Обновленный перечень задач сотрудника '+sqluserfio+' на дату ' + sqldate + 'содержит записей:' + str(cursor.rowcount)
                    ResultMessage = ResultMessage + "\n" + "\n"
                    rows = cursor.fetchall()
                    numcs1 = 0
                    for row in rows:
                        numcs1 = numcs1+1
                        ResultMessage = ResultMessage + str(numcs1)+') '+str(row[0])+'-я задача ('+str(row[1])+'-'+str(row[2])+')'+"\n"+str(row[3])+'.'+"\n"+' (Пост. - '+str(row[4])+');'+"\n"+"\n"
                    bot.send_message(message.chat.id, ResultMessage)
                    conn.close()
            else:
                bot.send_message(message.chat.id, "Вы не авторизованы, либо недостаточно полномочий на выполнение команды, либо неправильное ФИО сотрудника, которому которому ставится задача.")
        else:
            bot.send_message(message.chat.id, "Слишком короткая команда! Правильный пример: '/add_directive 10.07.2023 09:00 10:00 Иванов И.И. Поездка в ВГУ'.")
    except:
        bot.send_message(message.chat.id, 'Не удалось выполнить запрос!')

# процедура удаления задачи пользователя руководителем - который ее поставил (для уровней доступа - руководитель)
@bot.message_handler(commands=["del_directive"])
def del_directive(message):
    try:
        OrigTgrCommand = message.text
        splitted_command = message.text.split(maxsplit=4)
        if len(OrigTgrCommand) >= 15:
            # читаем дату
            sqldate = splitted_command[1]
            # читаем фамилию сотрудника которому пытаемся удалить задачу
            sqlfam = splitted_command[2]
            # читаем И.О. сотрудника которому пытаемся удалить задачу
            sqlio = splitted_command[3]
            sqluserfio = sqlfam + ' ' + sqlio
            # читаем номер задачи
            sqltasknum = splitted_command[4]
            conn = psycopg2.connect(database=dbname23, user=dbuser23, password=dbpass23, host=dbhost23, port=dbport23)
            conn.autocommit = True
            cursor = conn.cursor()
            # проверяем авторизовался ли пользователь
            sqlstr0 = 'SELECT chat_id, code_acl, tabno FROM active_list2 WHERE chat_id = '+str(message.chat.id)
            cursor.execute(sqlstr0)
            rows = cursor.fetchall()
            numcs = 0
            UserActive = 0
            for row in rows:
                numcs = numcs+1
                aclc = row[1]
                tabnoc = row[2]
                if ((numcs == 1) and (aclc > 2) and (aclc < 4)):
                    UserActive = 1
            # если авторизовался - выполняем нужный запрос
            # но сначала проверим, есть ли такой пользователь в базе, которому нужно удалить задачу
            sqlstr1 = 'SELECT tabno, fio FROM teachers WHERE fio = '+"'"+str(sqluserfio)+"'"
            cursor.execute(sqlstr1)
            rows = cursor.fetchall()
            numcs = 0
            CtrlUserFound = 0
            for row in rows:
                numcs = numcs+1
                fio_ctrluser = row[1]
                tabno_ctrluser = row[0]
                if (numcs == 1):
                    CtrlUserFound = 1
            if ((UserActive == 1) and (CtrlUserFound == 1)):
                sqlstr = 'SELECT tabno, fio FROM teachers WHERE tabno = '+str(tabno_ctrluser)
                cursor.execute(sqlstr)
                rows = cursor.fetchall()
                numcs = 0
                for row in rows:
                    numcs = numcs+1
                    CodeTeacher=row[0]
                    FioTeachr=row[1]
                # если нашли такого преподавателя, причем у него код в диапазоне от 1 до 199, то формируем запрос на удаление задачи из списка задач
                if ((CodeTeacher >= 1) and (CodeTeacher <= 199)):
                    SqlStr0='delete from zadachi '
                    SqlStr1='where ((zdate='+"'"+sqldate+"'"+') and (nopp_z='+str(sqltasknum)+') and (tabno_isp='+str(tabno_ctrluser)+') and (tabno_por='+str(tabnoc)+'))'
                    SqlStr40=SqlStr0+"\n"+SqlStr1
                    cursor.execute(SqlStr40)
                    ResultMessage = 'Запрос выполнен!'
                    ResultMessage = ResultMessage + "\n" + "\n"
                    SqlStr0='select zz.nopp_z, zz.time_begin, zz.time_end, zz.zadacha, tc.fio '
                    SqlStr1='from zadachi zz, teachers tc '
                    SqlStr2='where ((zz.zdate='+"'"+sqldate+"'"+') and (zz.tabno_isp='+str(CodeTeacher)+') '
                    SqlStr3='and (tc.tabno=zz.tabno_por)) '
                    SqlStr4='order by nopp_z'
                    SqlStr20=SqlStr0+SqlStr1+SqlStr2+SqlStr3+SqlStr4
                    cursor.execute(SqlStr20)
                    ResultMessage = ResultMessage+'Обновленный перечень задач сотрудника ' + sqluserfio + ' на дату ' + sqldate + ' содержит записей: ' + str(cursor.rowcount)
                    ResultMessage = ResultMessage + "\n" + "\n"
                    rows = cursor.fetchall()
                    numcs1 = 0
                    for row in rows:
                        numcs1 = numcs1+1
                        ResultMessage = ResultMessage + str(numcs1)+') '+str(row[0])+'-я задача ('+str(row[1])+'-'+str(row[2])+')'+"\n"+str(row[3])+'.'+"\n"+' (Пост. - '+str(row[4])+');'+"\n"+"\n"
                    bot.send_message(message.chat.id, ResultMessage)
                    conn.close()
            else:
                bot.send_message(message.chat.id, "Вы не авторизованы, либо недостаточно полномочий для выполнения команды, либо задача поставлена иным лицом!")
        else:
            bot.send_message(message.chat.id, "Слишком короткая команда! Правильный пример: '/del_directive 10.07.2023 Иванов И.И. 6'")
    except:
        bot.send_message(message.chat.id, 'Не удалось выполнить запрос!')

# процедура смены пароля пользователя самому себе (для уровней доступа - преподаватель, руководитель)
@bot.message_handler(commands=["ch_pass"])
def ch_pass(message):
    try:
        OrigTgrCommand = message.text
        splitted_command = message.text.split(maxsplit=3)
        if len(OrigTgrCommand) >= 15:
            # читаем старый пароль
            sql_oldpass = splitted_command[1]
            # читаем новый пароль
            sql_newpass1 = splitted_command[2]
            # читаем новый пароль (перевведенный - "по классике", проверяем что рука не дрогнула и пароли совпадают)
            sql_newpass2 = splitted_command[3]
            conn = psycopg2.connect(database=dbname23, user=dbuser23, password=dbpass23, host=dbhost23, port=dbport23)
            conn.autocommit = True
            cursor = conn.cursor()
            # проверяем авторизовался ли пользователь
            sqlstr0 = 'SELECT chat_id, code_acl, tabno FROM active_list2 WHERE chat_id = '+str(message.chat.id)
            cursor.execute(sqlstr0)
            rows = cursor.fetchall()
            numcs = 0
            UserActive = 0
            for row in rows:
                numcs = numcs+1
                aclc = row[1]
                tabnoc = row[2]
                if ((numcs == 1) and (aclc > 1) and (aclc < 4)):
                    UserActive = 1
            # если авторизовался - выполняем нужный запрос
            if UserActive == 1:
                sqlstr = 'SELECT tabno, fio, intpasshash FROM teachers WHERE tabno = '+str(tabnoc)
                cursor.execute(sqlstr)
                rows = cursor.fetchall()
                numcs = 0
                for row in rows:
                    numcs = numcs+1
                    CodeTeacher=row[0]+0
                    FioTeachr=row[1]
                    IntPassHashTeacher=row[2]
                    MD5_sql_oldpass=hashlib.md5(sql_oldpass.encode('utf-8')).hexdigest()
                    MD5_sql_newpass=hashlib.md5(sql_newpass1.encode('utf-8')).hexdigest()
                # если нашли такого преподавателя (руководителя), причем у него код в диапазоне от 1 до 199, то формируем запрос на обновление пароля в списке пользователей
                # и если старый пароль совпадает и новый пароль введен правильно (при проверочном вводе тот же что и при первоначальном)
                # if ((CodeTeacher >= 1) and (CodeTeacher <= 199) and (str(MD5_sql_oldpass)==str(IntPassHashTeacher)) and (str(sql_newpass1)==str(sql_newpass2))):
                if ((CodeTeacher >= 1) and (CodeTeacher <= 199) and (MD5_sql_oldpass==IntPassHashTeacher) and (sql_newpass1==sql_newpass2)):
                    SqlStr0='update teachers '
                    SqlStr1='set intpasshash='+"'"+MD5_sql_newpass+"' "
                    SqlStr2='where tabno='+str(CodeTeacher)
                    SqlStr50=SqlStr0+"\n"+SqlStr1+"\n"+SqlStr2
                    cursor.execute(SqlStr50)
                    ResultMessage = 'Запрос выполнен. Новый пароль будет действовать при следующем входе в систему.'
                    ResultMessage = ResultMessage + "\n" + "\n"
                    bot.send_message(message.chat.id, ResultMessage)
                    conn.close()
                else:
                    bot.send_message(message.chat.id, "Пароли не совпадают - старый с имеющимся в базе либо новые между собой. Запрос отклонен.")
            else:
                bot.send_message(message.chat.id, "Вы не авторизованы или недостаточно полномочий для выполнения команды.")
        else:
            bot.send_message(message.chat.id, "Слишком короткая команда! Правильный пример: '/ch_pass 123 g@zTsQ g@zTsQ'")
    except:
        bot.send_message(message.chat.id, 'Не удалось выполнить запрос!')


# процедура нахождения пары в расписании по дате, порядковому номеру пары, и списку (или фрагменту списка групп(ы) для всех авторизованных пользователей)
@bot.message_handler(commands=["find_pair"])
def find_pair(message):
    try:
        OrigTgrCommand = message.text
        splitted_command = message.text.split(maxsplit=3)
        if len(OrigTgrCommand) >= 15:
            # читаем дату
            sqldate = splitted_command[1]
            # читаем номер пары
            sqlpair = splitted_command[2]
            # читаем фрагмент списка групп
            sqlgroup = splitted_command[3]
            conn = psycopg2.connect(database=dbname23, user=dbuser23, password=dbpass23, host=dbhost23, port=dbport23)
            conn.autocommit = True
            cursor = conn.cursor()
            # проверяем авторизовался ли пользователь
            sqlstr0 = 'SELECT chat_id, code_acl FROM active_list2 WHERE chat_id = '+str(message.chat.id)
            cursor.execute(sqlstr0)
            rows = cursor.fetchall()
            numcs = 0
            UserActive = 0
            for row in rows:
                numcs = numcs+1
                aclc = row[1]
                if ((numcs == 1) and (aclc > 0) and (aclc < 4)):
                    UserActive = 1
            # если авторизовался - выполняем нужный запрос
            if UserActive == 1:
                SqlStr0='select tt.ttdate, tt.codepair, pr.timefrom, pr.timeto, sj.naim as subjectnaim, pt.naim as pairtypenaim, tt.theme, tt.groupslist, tc.fio, rm.naim as roomnaim '
                SqlStr1='from timetable tt, teachers tc, pairs pr, rooms rm, subjects sj, pairtypes  pt '
                SqlStr2='where ((tt.ttdate='+"'"+sqldate+"'"+') and (tt.codepair='+sqlpair+') and (tt.groupslist like '+"'"+'%'+sqlgroup+'%'+"'"+') '
                SqlStr3='and (tc.tabno=tt.codeteacher) and (pr.nopp=tt.codepair) and (rm.code=tt.coderoom) and (sj.code=tt.codesubject) and (pt.code=tt.codesubjtype)) '
                SqlStr4='order by codepair'
                SqlStr20=SqlStr0+SqlStr1+SqlStr2+SqlStr3+SqlStr4
                cursor.execute(SqlStr20)
                ResultMessage = ''
                ResultMessage = 'Найдено записей в РАСПИСАНИИ: ' + str(cursor.rowcount)+'. '
                ResultMessage = ResultMessage + "\n" + "\n"
                rows = cursor.fetchall()
                numcs1 = 0
                for row in rows:
                    numcs1 = numcs1+1
                    ResultMessage = ResultMessage + str(numcs1)+') '+str(row[1])+'-я пара ('+str(row[2])+'-'+str(row[3])+')'+"\n"+str(row[4])+' ('+str(row[5])+')'+"\n"+'Тема: '+str(row[6])+"\n"+'Группа(ы): '+str(row[7])+"\n"+'Ауд.: '+ str(row[9])+"\n"+'Преп.: '+str(row[8])+"\n"+"\n"
                ResultMessage = ResultMessage + "\n"
                bot.send_message(message.chat.id, ResultMessage)
                conn.close()
            else:
                bot.send_message(message.chat.id, "Вы не авторизованы.")
        else:
            bot.send_message(message.chat.id, "Слишком короткая команда! Правильный пример: '/find_pair 10.07.2023 2 Р19'.")
    except:
        bot.send_message(message.chat.id, 'Не удалось выполнить запрос!')

# процедура вывода расписания загрузки выбранной аудитории на дату (для всех авторизованных пользователей)
@bot.message_handler(commands=["sh_rt"])
def sh_rt(message):
    try:
        OrigTgrCommand = message.text
        splitted_command = message.text.split(maxsplit=2)
        if len(OrigTgrCommand) >= 15:
            # читаем дату
            sqldate = splitted_command[1]
            # читаем номер аудитории
            sqlroom = splitted_command[2]
            conn = psycopg2.connect(database=dbname23, user=dbuser23, password=dbpass23, host=dbhost23, port=dbport23)
            conn.autocommit = True
            cursor = conn.cursor()
            # проверяем авторизовался ли пользователь
            sqlstr0 = 'SELECT chat_id, code_acl FROM active_list2 WHERE chat_id = '+str(message.chat.id)
            cursor.execute(sqlstr0)
            rows = cursor.fetchall()
            numcs = 0
            UserActive = 0
            for row in rows:
                numcs = numcs+1
                aclc = row[1]
                if ((numcs == 1) and (aclc > 0) and (aclc < 4)):
                    UserActive = 1
            # ищем код запрошенной аудитории - существует ли аудитория с таким названием
            sqlstr0 = 'SELECT code, naim FROM rooms WHERE naim = '+"'"+sqlroom+"'"+';'
            cursor.execute(sqlstr0)
            rows = cursor.fetchall()
            numcs = 0
            RoomExists = 0
            for row in rows:
                numcs = numcs+1
                if numcs == 1:
                    RoomExists = 1
                    sqlroomcode = row[0]
            # если авторизовался и аудитория существует - выполняем нужный запрос
            if (UserActive == 1):
                if (RoomExists == 1):
                    SqlStr0='select tt.ttdate, tt.codepair, pr.timefrom, pr.timeto, sj.naim as subjectnaim, pt.naim as pairtypenaim, tt.theme, tt.groupslist, tc.fio, rm.naim as roomnaim '
                    SqlStr1='from timetable tt, teachers tc, pairs pr, rooms rm, subjects sj, pairtypes  pt '
                    SqlStr2='where ((tt.ttdate='+"'"+sqldate+"'"+') and (tt.coderoom='+str(sqlroomcode)+') '
                    SqlStr3='and (tc.tabno=tt.codeteacher) and (pr.nopp=tt.codepair) and (rm.code=tt.coderoom) and (sj.code=tt.codesubject) and (pt.code=tt.codesubjtype)) '
                    SqlStr4='order by codepair'
                    SqlStr20=SqlStr0+SqlStr1+SqlStr2+SqlStr3+SqlStr4
                    cursor.execute(SqlStr20)
                    ResultMessage = ''
                    ResultMessage = 'Найдено записей в РАСПИСАНИИ: ' + str(cursor.rowcount)+'. '
                    ResultMessage = ResultMessage + "\n" + "\n"
                    rows = cursor.fetchall()
                    numcs = 0
                    for row in rows:
                        numcs = numcs+1
                        ResultMessage = ResultMessage + str(numcs)+') '+str(row[1])+'-я пара ('+str(row[2])+'-'+str(row[3])+')'+"\n"+str(row[4])+' ('+str(row[5])+')'+"\n"+'Тема: '+str(row[6])+"\n"+'Группа(ы): '+str(row[7])+"\n"+'Ауд.: '+ str(row[9])+"\n"+'Преп.: '+str(row[8])+"\n"+"\n"
                    ResultMessage = ResultMessage + "\n"
                    bot.send_message(message.chat.id, ResultMessage)
                    conn.close()
                else:
                    MessStrAudNE = 'Аудитория с указанным номером не найдена. Изучите список доступных аудиторий по команде'+"\n"+' /sh_rooms'
                    bot.send_message(message.chat.id, MessStrAudNE)
            else:
                bot.send_message(message.chat.id, "Вы не авторизованы.")
        else:
            MessStrAudESC = 'Слишком короткая команда! Правильный пример:'+"\n"+'/sh_rt 10.07.2023 2к/221'
            bot.send_message(message.chat.id, MessStrAudESC)
    except:
        bot.send_message(message.chat.id, 'Не удалось выполнить запрос!')

# если прислали непонятного рода текст, то наводим на мысль о том что необходимо вызвать help
@bot.message_handler(content_types=["text"])
def echo(message):
    bot.send_message(message.chat.id, HELP)

bot.polling(none_stop=True)
