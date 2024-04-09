import pyotp
import qrcode
from PIL import Image


def generate(key):
    uri = pyotp.totp.TOTP(key).provisioning_uri(name='App', issuer_name='Sonya')
    qrcode.make(uri).save('otp.png')
    Image.open("otp.png").show()


def main():
    key = input("Введите секретный ключ: ")
    if len(key) < 16:
        print("Длинна ключа должна быть не менее 16 символов. Повторите ввод.")
        main()
        return
    generate(key)


if __name__ == "__main__":
    main()