from db_init import get_connection

def get_categories():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM categories")
    result = cursor.fetchall()
    conn.close()
    return result

def get_products_by_category(category_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, price, image_path
        FROM products
        WHERE category_id = ?
    """, (category_id,))
    result = cursor.fetchall()
    conn.close()
    return result

def get_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, image_path FROM products")
    result = cursor.fetchall()
    conn.close()
    return result

def get_ingredients_for_product(product_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ingredient_id, quantity
        FROM product_ingredients
        WHERE product_id = ?
    """, (product_id,))
    result = cursor.fetchall()
    conn.close()
    return result

def create_sale(items, paid, method, guest_name="Гость"):  # ✅ добавлен guest_name
    conn = get_connection()
    cursor = conn.cursor()
    total = sum(price * qty for _, price, qty in items)

    cursor.execute("""
        INSERT INTO sales (date, total, paid, payment_method, guest_name)
        VALUES (datetime('now'), ?, ?, ?, ?)
    """, (total, int(paid), method, guest_name))  # ✅ сохранение имени
    sale_id = cursor.lastrowid

    for product_id, price, qty in items:
        cursor.execute("""
            INSERT INTO sale_items (sale_id, product_id, quantity)
            VALUES (?, ?, ?)
        """, (sale_id, product_id, qty))

        cursor.execute("""
            SELECT ingredient_id, quantity
            FROM product_ingredients
            WHERE product_id = ?
        """, (product_id,))
        recipe = cursor.fetchall()

        for ing_id, ing_qty in recipe:
            total_qty = ing_qty * qty
            cursor.execute("""
                UPDATE ingredients
                SET quantity = quantity - ?
                WHERE id = ?
            """, (total_qty, ing_id))

    conn.commit()
    conn.close()
    return sale_id

def get_sales():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, date, total, paid, payment_method, guest_name
        FROM sales
        ORDER BY date DESC
    """)  # ✅ добавлен guest_name
    result = cursor.fetchall()
    conn.close()
    return result

def get_sale_items(sale_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT products.name, sale_items.quantity, products.price
        FROM sale_items
        JOIN products ON sale_items.product_id = products.id
        WHERE sale_items.sale_id = ?
    """, (sale_id,))
    result = cursor.fetchall()
    conn.close()
    return result

def update_sale_status(sale_id, paid, method):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE sales
        SET paid = ?, payment_method = ?
        WHERE id = ?
    """, (int(paid), method, sale_id))
    conn.commit()
    conn.close()

def calculate_cost(product_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pi.quantity, i.last_price
        FROM product_ingredients pi
        JOIN ingredients i ON pi.ingredient_id = i.id
        WHERE pi.product_id = ?
    """, (product_id,))
    rows = cursor.fetchall()
    conn.close()

    return sum(qty * price for qty, price in rows if qty and price)

def get_ingredient_stock():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, quantity, unit FROM ingredients ORDER BY name")
    result = cursor.fetchall()
    conn.close()
    return result

def get_low_stock(threshold=50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, quantity, unit
        FROM ingredients
        WHERE quantity < ?
        ORDER BY quantity ASC
    """, (threshold,))
    result = cursor.fetchall()
    conn.close()
    return result

def calculate_margin(product_id):
    cost = calculate_cost(product_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT price FROM products WHERE id = ?", (product_id,))
    result = cursor.fetchone()
    conn.close()

    if not result or cost == 0:
        return 0.0

    price = result[0]
    return (price - cost) / cost * 100

from datetime import datetime

def get_sales_by_period(start, end):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT date, total, paid, payment_method, guest_name
        FROM sales
        WHERE date(date) BETWEEN ? AND ?
        ORDER BY date ASC
    """, (start, end))
    result = cursor.fetchall()
    print("Найдено продаж:", len(result))  # ✅ отладка
    conn.close()
    return result


def get_profit_by_period(start, end):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT si.product_id, si.quantity, p.price
        FROM sale_items si
        JOIN sales s ON si.sale_id = s.id
        JOIN products p ON si.product_id = p.id
        WHERE date(s.date) BETWEEN ? AND ?
    """, (start, end))  # ✅ исправлено
    items = cursor.fetchall()
    conn.close()

    profit = 0
    for pid, qty, price in items:
        cost = calculate_cost(pid)
        profit += (price - cost) * qty
    return round(profit, 2)


def get_ingredient_usage(start, end):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT si.product_id, si.quantity
        FROM sale_items si
        JOIN sales s ON si.sale_id = s.id
        WHERE date(s.date) BETWEEN ? AND ?
    """, (start, end))  # ✅ исправлено
    sales = cursor.fetchall()

    usage = {}
    for pid, qty in sales:
        cursor.execute("""
            SELECT ingredient_id, quantity
            FROM product_ingredients
            WHERE product_id = ?
        """, (pid,))
        recipe = cursor.fetchall()
        for ing_id, ing_qty in recipe:
            total = ing_qty * qty
            usage[ing_id] = usage.get(ing_id, 0) + total

    result = []
    for ing_id, total_qty in usage.items():
        cursor.execute("SELECT name, unit FROM ingredients WHERE id = ?", (ing_id,))
        name, unit = cursor.fetchone()
        result.append((name, total_qty, unit))

    conn.close()
    return result


def get_top_products(start, end, by="count"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT si.product_id, SUM(si.quantity) as total_qty
        FROM sale_items si
        JOIN sales s ON si.sale_id = s.id
        WHERE date(s.date) BETWEEN ? AND ?
        GROUP BY si.product_id
    """, (start, end))  # ✅ исправлено
    rows = cursor.fetchall()

    result = []
    for pid, qty in rows:
        cursor.execute("SELECT name, price FROM products WHERE id = ?", (pid,))
        name, price = cursor.fetchone()
        if by == "profit":
            cost = calculate_cost(pid)
            profit = (price - cost) * qty
            result.append((name, profit))
        else:
            result.append((name, qty))

    conn.close()
    return sorted(result, key=lambda x: x[1], reverse=True)

def get_detailed_sales(start, end):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.id, s.date, s.total, s.paid, s.payment_method, s.guest_name
        FROM sales s
        WHERE date(s.date) BETWEEN ? AND ?
        ORDER BY s.date ASC
    """, (start, end))
    sales = cursor.fetchall()

    detailed = []

    for sale_id, date, total, paid, method, guest in sales:
        cursor.execute("""
            SELECT si.product_id, si.quantity, p.name, p.price
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            WHERE si.sale_id = ?
        """, (sale_id,))
        products = cursor.fetchall()

        product_details = []

        for pid, qty, name, price in products:
            cursor.execute("""
                SELECT pi.ingredient_id, pi.quantity, i.name, i.unit
                FROM product_ingredients pi
                JOIN ingredients i ON pi.ingredient_id = i.id
                WHERE pi.product_id = ?
            """, (pid,))
            ingredients = cursor.fetchall()

            ingredient_usage = []
            for ing_id, ing_qty, ing_name, unit in ingredients:
                total_used = ing_qty * qty
                ingredient_usage.append({
                    "name": ing_name,
                    "used": total_used,
                    "unit": unit
                })

            product_details.append({
                "name": name,
                "qty": qty,
                "price": price,
                "ingredients": ingredient_usage
            })

        detailed.append({
            "sale_id": sale_id,
            "date": date,
            "total": total,
            "paid": bool(paid),
            "method": method,
            "guest": guest,
            "products": product_details
        })

    conn.close()
    return detailed

def get_last_sale_id():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM sales ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def generate_receipt_html(sale_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT date, total, paid, payment_method, guest_name FROM sales WHERE id = ?", (sale_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return "<p>Ошибка: продажа не найдена.</p>"

    date, total, paid, method, guest = row

    cursor.execute("""
        SELECT p.name, si.quantity, p.price
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        WHERE si.sale_id = ?
    """, (sale_id,))
    items = cursor.fetchall()

    html = f"""
    <h2>Счёт №{sale_id}</h2>
    <p><b>Дата:</b> {date}<br>
    <b>Гость:</b> {guest}<br>
    <b>Оплачено:</b> {"Да" if paid else "Нет"}<br>
    <b>Метод оплаты:</b> {method}</p>
    <table border="1" cellspacing="0" cellpadding="4">
        <tr><th>Напиток</th><th>Кол-во</th><th>Цена</th></tr>
    """
    for name, qty, price in items:
        html += f"<tr><td>{name}</td><td>{qty}</td><td>{price:.2f}</td></tr>"

    html += f"</table><p><b>Итого:</b> {total:.2f} BYN</p>"
    conn.close()
    return html

def get_margin_report():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, price FROM products")
    products = cursor.fetchall()

    report = []

    for pid, name, price in products:
        cursor.execute("""
            SELECT pi.quantity, i.last_price
            FROM product_ingredients pi
            JOIN ingredients i ON pi.ingredient_id = i.id
            WHERE pi.product_id = ?
        """, (pid,))
        ingredients = cursor.fetchall()

        cost = sum(qty * cost for qty, cost in ingredients)
        margin = ((price - cost) / cost * 100) if cost > 0 else 0

        report.append((name, price, cost, margin))

    conn.close()
    return report
