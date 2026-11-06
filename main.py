"""Локальная консольная программа для пользователей и товаров."""

from datetime import date
from getpass import getpass
import hashlib
from pathlib import Path
import secrets
import sqlite3

DB_PATH = Path(__file__).resolve().with_name("demo.db")


def init_db(connection):
    connection.row_factory = sqlite3.Row
    with connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, name TEXT, password TEXT,
            phone TEXT, birthday TEXT)""")
        # Сохраняем старую таблицу с полями name и age.
        columns = {row[1] for row in connection.execute("PRAGMA table_info(users)")}
        for column in ("password", "phone", "birthday"):
            if column not in columns:
                connection.execute(f"ALTER TABLE users ADD COLUMN {column} TEXT")
        connection.execute("""CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY, name TEXT, category TEXT, price INTEGER)""")


def read_text(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Значение не должно быть пустым.")


def read_integer(prompt, minimum=1):
    while True:
        try:
            value = int(input(prompt))
            if minimum <= value <= 9223372036854775807:
                return value
        except ValueError:
            pass
        print(f"Введите целое число от {minimum} до 9223372036854775807.")


def read_birthday():
    while True:
        value = input("Дата рождения (ГГГГ-ММ-ДД, Enter — пропустить): ").strip()
        if not value:
            return None
        try:
            birthday = date.fromisoformat(value)
            if birthday <= date.today():
                return birthday.isoformat()
        except ValueError:
            pass
        print("Введите существующую дату рождения, не позднее сегодняшней.")


def add_user(connection):
    name = read_text("Имя: ")
    password = getpass("Пароль: ")
    while not password.strip():
        print("Пароль не должен быть пустым.")
        password = getpass("Пароль: ")
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600000)
    password_hash = f"pbkdf2_sha256$600000${salt}${digest.hex()}"
    phone = input("Телефон (Enter — пропустить): ").strip() or None
    birthday = read_birthday()
    with connection:
        cursor = connection.execute(
            "INSERT INTO users (name, password, phone, birthday) VALUES (?, ?, ?, ?)",
            (name, password_hash, phone, birthday),
        )
    print(f"Пользователь добавлен. ID: {cursor.lastrowid}")


def show_users(connection, user_id=None):
    query = "SELECT id, name, phone, birthday FROM users"
    params = ()
    if user_id is not None:
        query += " WHERE id = ?"
        params = (user_id,)
    rows = connection.execute(query + " ORDER BY id", params).fetchall()
    if not rows:
        print("Пользователи не найдены.")
    for row in rows:
        print(f"ID: {row['id']} | Имя: {row['name']} | "
              f"Телефон: {row['phone'] or '—'} | Дата рождения: {row['birthday'] or '—'}")


def add_product(connection):
    name = read_text("Название: ")
    category = read_text("Категория: ")
    price = read_integer("Цена (целое число рублей): ", minimum=0)
    with connection:
        cursor = connection.execute(
            "INSERT INTO products (name, category, price) VALUES (?, ?, ?)",
            (name, category, price),
        )
    print(f"Товар добавлен. ID: {cursor.lastrowid}")


def show_products(connection, name=None):
    rows = connection.execute("SELECT * FROM products ORDER BY id").fetchall()
    # Поиск без учёта регистра работает и для кириллицы.
    if name is not None:
        rows = [row for row in rows if name.casefold() in (row['name'] or '').casefold()]
    if not rows:
        print("Товары не найдены.")
    for row in rows:
        print(f"ID: {row['id']} | {row['name']} | "
              f"Категория: {row['category']} | Цена: {row['price']} руб.")


def main():
    connection = None
    try:
        connection = sqlite3.connect(DB_PATH)
        init_db(connection)
        while True:
            print("\n1. Добавить пользователя\n2. Список пользователей\n"
                  "3. Найти пользователя по ID\n4. Добавить товар\n"
                  "5. Список товаров\n6. Найти товар по названию\n0. Выход")
            choice = input("Выберите действие: ").strip()
            try:
                if choice == "0":
                    break
                elif choice == "1":
                    add_user(connection)
                elif choice == "2":
                    show_users(connection)
                elif choice == "3":
                    show_users(connection, read_integer("ID пользователя: "))
                elif choice == "4":
                    add_product(connection)
                elif choice == "5":
                    show_products(connection)
                elif choice == "6":
                    show_products(connection, read_text("Название или его часть: "))
                else:
                    print("Выберите пункт меню от 0 до 6.")
            except sqlite3.Error as error:
                print(f"Ошибка базы данных: {error}")
    except (EOFError, KeyboardInterrupt):
        print("\nВвод завершён.")
    except sqlite3.Error as error:
        print(f"Не удалось открыть или подготовить базу данных: {error}")
    finally:
        if connection is not None:
            connection.close()
    print("До свидания!")


if __name__ == "__main__":
    main()
