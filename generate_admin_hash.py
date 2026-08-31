import getpass

from werkzeug.security import generate_password_hash

if __name__ == "__main__":
    password = getpass.getpass("Пароль администратора: ")
    print(generate_password_hash(password))
