import sqlite3

def get_connection():
    return sqlite3.connect("bar_sales.db", timeout=5)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        category_id INTEGER,
        image_path TEXT,
        FOREIGN KEY (category_id) REFERENCES categories(id)
    );

    CREATE TABLE IF NOT EXISTS ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        unit TEXT,
        quantity REAL DEFAULT 0,
        last_price REAL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        supplier_id INTEGER,
        number INTEGER DEFAULT 0,
        FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
    );

    CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER,
        ingredient_id INTEGER,
        quantity REAL,
        price REAL,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id),
        FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
    );

    CREATE TABLE IF NOT EXISTS product_ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        ingredient_id INTEGER,
        quantity REAL,
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
    );

    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        total REAL,
        paid INTEGER,
        payment_method TEXT,
        guest_name TEXT DEFAULT 'Гость',
        C1 INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS sale_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        FOREIGN KEY (sale_id) REFERENCES sales(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );
    """)

    # Миграция: если таблица sales уже существует, но колонки C1 нет — добавить
    cursor.execute("PRAGMA table_info(sales);")
    existing_columns = [row[1] for row in cursor.fetchall()]  # row[1] — имя колонки
    if "C1" not in existing_columns:
        cursor.execute("ALTER TABLE sales ADD COLUMN C1 INTEGER DEFAULT 1;")
        cursor.execute("UPDATE sales SET C1 = 1 WHERE C1 IS NULL;")

    conn.commit()
    conn.close()

def clear_all_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript("""
        PRAGMA foreign_keys = OFF;

        DELETE FROM sale_items;
        DELETE FROM sales;
        DELETE FROM product_ingredients;
        DELETE FROM invoice_items;
        DELETE FROM invoices;
        DELETE FROM products;
        DELETE FROM categories;
        DELETE FROM ingredients;
        DELETE FROM suppliers;

        DELETE FROM sqlite_sequence;

        PRAGMA foreign_keys = ON;
    """)
    conn.commit()
    conn.close()
