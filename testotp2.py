import binascii

import pyotp
key ='dfncufuebgr47347r3ncu'
totp = pyotp.TOTP(key)

try:
    rs = totp.verify(input("Введите код аутентификации: "))
    print("Успешная аутентификация") if rs else print("Повторите ввод. Неудача.")
except binascii.Error:
    print("Перегенерируйте ключ. Длина ключа должна быть не менее 16 символов.")

