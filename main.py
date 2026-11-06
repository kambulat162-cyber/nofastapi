"""Локальная консольная программа для пользователей, товаров и заказов."""

from datetime import date, datetime
from getpass import getpass
import hashlib
from pathlib import Path
import secrets
import sqlite3

DB_PATH = Path(__file__).resolve().with_name("demo.db")


def init_db(connection):
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    with connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, name TEXT, password TEXT,
            phone TEXT, birthday TEXT)""")
        columns = {row[1] for row in connection.execute("PRAGMA table_info(users)")}
        for column in ("password", "phone", "birthday"):
            if column not in columns:
                connection.execute(f"ALTER TABLE users ADD COLUMN {column} TEXT")
        connection.execute("""CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY, name TEXT, category TEXT, price INTEGER)""")
        connection.execute("""CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            "sum" INTEGER NOT NULL CHECK ("sum" >= 0),
            create_date TEXT NOT NULL,
            user_id INTEGER NOT NULL REFERENCES users(id))""")
        connection.execute("""CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            product_id INTEGER NOT NULL REFERENCES products(id),
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            unit_price INTEGER NOT NULL CHECK (unit_price >= 0))""")


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
    if name is not None:
        rows = [row for row in rows if name.casefold() in (row['name'] or '').casefold()]
    if not rows:
        print("Товары не найдены.")
    for row in rows:
        print(f"ID: {row['id']} | {row['name']} | "
              f"Категория: {row['category']} | Цена: {row['price']} руб.")


def getUserId(connection, userName):
    user = getUserByName(connection, userName)
    if user is None:
        return None
    return user["id"]


def getUserByName(connection, userName):
    users = connection.execute(
        "SELECT id, name, phone, birthday FROM users ORDER BY id"
    ).fetchall()
    for user in users:
        if user["name"].casefold() == userName.casefold():
            return user
    return None


def getProductById(connection, productId):
    return connection.execute(
        "SELECT id, name, category, price FROM products WHERE id = ?",
        (productId,),
    ).fetchone()


def getAllProductByCategory(connection, category):
    products = connection.execute(
        "SELECT id, name, category, price FROM products ORDER BY id"
    ).fetchall()
    result = []
    for product in products:
        if (product["category"] or "").casefold() == category.casefold():
            result.append(product)
    return result


def getOrdersByUserId(connection, userId):
    orders = connection.execute(
        'SELECT id, "sum", create_date, user_id FROM orders '
        "WHERE user_id = ? ORDER BY id",
        (userId,),
    ).fetchall()
    result = []
    for order in orders:
        order_data = dict(order)
        order_data["orderItems"] = connection.execute(
            "SELECT oi.id, oi.product_id, p.name AS product_name, oi.quantity, "
            "oi.unit_price FROM order_items AS oi "
            "JOIN products AS p ON p.id = oi.product_id "
            "WHERE oi.order_id = ? ORDER BY oi.id",
            (order["id"],),
        ).fetchall()
        result.append(order_data)
    return result


def getOrdersByBeetwinDate(connection, startDate, endDate):
    start = date.fromisoformat(startDate).isoformat()
    end = date.fromisoformat(endDate).isoformat()
    if start > end:
        raise ValueError("Начальная дата не должна быть позже конечной.")

    orders = connection.execute(
        'SELECT id, "sum", create_date, user_id FROM orders '
        "WHERE date(create_date) BETWEEN ? AND ? ORDER BY create_date, id",
        (start, end),
    ).fetchall()
    result = []
    for order in orders:
        order_data = dict(order)
        order_data["orderItems"] = connection.execute(
            "SELECT oi.id, oi.product_id, p.name AS product_name, oi.quantity, "
            "oi.unit_price FROM order_items AS oi "
            "JOIN products AS p ON p.id = oi.product_id "
            "WHERE oi.order_id = ? ORDER BY oi.id",
            (order["id"],),
        ).fetchall()
        result.append(order_data)
    return result


def getBestProductsRange(connection, startDate, endDate):
    start = date.fromisoformat(startDate).isoformat()
    end = date.fromisoformat(endDate).isoformat()
    if start > end:
        raise ValueError("Начальная дата не должна быть позже конечной.")

    rows = connection.execute(
        "SELECT p.id, p.name, p.category, p.price, "
        "SUM(oi.quantity) AS buy_count "
        "FROM order_items AS oi "
        "JOIN orders AS o ON o.id = oi.order_id "
        "JOIN products AS p ON p.id = oi.product_id "
        "WHERE date(o.create_date) BETWEEN ? AND ? "
        "GROUP BY p.id, p.name, p.category, p.price "
        "ORDER BY buy_count DESC, p.id",
        (start, end),
    ).fetchall()
    result = []
    for row in rows:
        product = {
            "id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "price": row["price"],
        }
        result.append((product, row["buy_count"]))
    return result


def addOrder(connection, userId, orderItems):
    user = connection.execute(
        "SELECT id FROM users WHERE id = ?", (userId,)
    ).fetchone()
    if user is None:
        raise ValueError("Пользователь не найден.")
    if not orderItems:
        raise ValueError("Нельзя создать заказ без товаров.")

    items = []
    total = 0
    for productId, quantity in orderItems:
        if quantity <= 0:
            raise ValueError("Количество товара должно быть больше нуля.")
        product = getProductById(connection, productId)
        if product is None:
            raise ValueError(f"Товар с ID {productId} не найден.")
        items.append((product, quantity))
        total += product["price"] * quantity

    createDate = datetime.now().astimezone().isoformat(timespec="seconds")
    with connection:
        cursor = connection.execute(
            'INSERT INTO orders ("sum", create_date, user_id) VALUES (?, ?, ?)',
            (total, createDate, userId),
        )
        orderId = cursor.lastrowid
        for product, quantity in items:
            connection.execute(
                "INSERT INTO order_items "
                "(order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (orderId, product["id"], quantity, product["price"]),
            )
    return orderId


def main():
    connection = None
    try:
        connection = sqlite3.connect(DB_PATH)
        init_db(connection)
        while True:
            print("\n1. Добавить пользователя\n2. Список пользователей\n"
                  "3. Найти пользователя по ID\n4. Добавить товар\n"
                  "5. Список товаров\n6. Найти товар по названию\n"
                  "7. Создать заказ\n0. Выход")
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
                elif choice == "7":
                    user_id = read_integer("ID пользователя: ")
                    user = connection.execute(
                        "SELECT id FROM users WHERE id = ?", (user_id,)
                    ).fetchone()
                    if user is None:
                        print("Пользователь не найден.")
                        continue
                    show_products(connection)
                    order_items = []
                    while True:
                        product_id = read_integer(
                            "ID товара (0 — завершить список): ", minimum=0
                        )
                        if product_id == 0:
                            break
                        product = getProductById(connection, product_id)
                        if product is None:
                            print("Товар не найден.")
                            continue
                        quantity = read_integer("Количество: ")
                        order_items.append((product_id, quantity))
                    if order_items:
                        order_id = addOrder(connection, user_id, order_items)
                        print(f"Заказ создан. ID: {order_id}")
                    else:
                        print("Заказ без товаров не создан.")
                else:
                    print("Выберите пункт меню от 0 до 7.")
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
