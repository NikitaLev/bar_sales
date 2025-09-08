from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QDialog, QLabel, QLineEdit, QMessageBox,
    QComboBox
)
from functools import partial
from db_init import get_connection
from models import calculate_cost
from ui.ingredient_selector import IngredientSelector

class ProductEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Редактор напитков")
        self.layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Название", "Цена"])
        self.table.cellDoubleClicked.connect(self.edit_product)
        self.table.setColumnWidth(1, 150)
        self.layout.addWidget(self.table)
        self.setMinimumSize(800, 600)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Добавить напиток")
        add_btn.clicked.connect(self.add_product)
        btn_row.addWidget(add_btn)

        self.layout.addLayout(btn_row)
        self.setLayout(self.layout)

        self.load_products()

    def load_products(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price FROM products")
        rows = cursor.fetchall()
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))
        conn.close()

    def add_product(self):
        dialog = ProductForm()
        dialog.exec_()
        self.load_products()

    def edit_product(self, row, column):
        product_id = int(self.table.item(row, 0).text())
        dialog = ProductForm(product_id)
        dialog.exec_()
        self.load_products()


class ProductForm(QDialog):
    def __init__(self, product_id=None):
        super().__init__()
        self.setWindowTitle("Редактировать напиток" if product_id else "Добавить напиток")
        self.product_id = product_id
        self.layout = QVBoxLayout()

        self.name_input = QLineEdit()
        self.price_input = QLineEdit()
        self.category_input = QComboBox()
        self.load_categories()

        self.layout.addWidget(QLabel("Название"))
        self.layout.addWidget(self.name_input)
        self.layout.addWidget(QLabel("Цена (BYN)"))
        self.layout.addWidget(self.price_input)
        self.layout.addWidget(QLabel("Категория"))
        self.layout.addWidget(self.category_input)

        self.cost_label = QLabel("Себестоимость: 0.00 BYN")
        self.margin_input = QLineEdit()
        self.rent_label = QLabel("Рентабельность: 0%")

        self.layout.addWidget(self.cost_label)
        self.layout.addWidget(QLabel("Наценка (%)"))
        self.layout.addWidget(self.margin_input)
        self.layout.addWidget(self.rent_label)

        self.margin_input.textChanged.connect(self.update_price_from_margin)
        self.price_input.textChanged.connect(self.update_rentability)

        recipe_btn = QPushButton("Рецепт напитка")
        recipe_btn.clicked.connect(self.open_recipe_editor)
        self.layout.addWidget(recipe_btn)

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save)
        self.layout.addWidget(save_btn)

        self.setLayout(self.layout)

        if product_id:
            self.load()

    def load_categories(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM categories")
        self.categories = cursor.fetchall()
        for cid, name in self.categories:
            self.category_input.addItem(name, cid)
        conn.close()

    def load(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, price, category_id FROM products WHERE id = ?", (self.product_id,))
        name, price, category_id = cursor.fetchone()
        self.name_input.setText(name)
        self.price_input.setText(str(price))

        index = next((i for i, (cid, _) in enumerate(self.categories) if cid == category_id), 0)
        self.category_input.setCurrentIndex(index)

        cost = calculate_cost(self.product_id)
        self.cost_label.setText(f"Себестоимость: {cost:.2f} BYN")

        if cost > 0:
            margin = (price - cost) / cost * 100
            self.rent_label.setText(f"Рентабельность: {margin:.1f}%")
            self.margin_input.setText(f"{margin:.1f}")
        conn.close()

    def update_price_from_margin(self):
        try:
            margin = float(self.margin_input.text())
            cost = calculate_cost(self.product_id)
            price = cost * (1 + margin / 100)
            self.price_input.setText(f"{price:.2f}")
            self.rent_label.setText(f"Рентабельность: {margin:.1f}%")
        except:
            pass

    def update_rentability(self):
        try:
            price = float(self.price_input.text())
            cost = calculate_cost(self.product_id)
            if cost > 0:
                margin = (price - cost) / cost * 100
                self.rent_label.setText(f"Рентабельность: {margin:.1f}%")
                self.margin_input.setText(f"{margin:.1f}")
        except:
            pass

    def open_recipe_editor(self):
        if not self.product_id:
            self.save()
            if not self.product_id:
                QMessageBox.warning(self, "Ошибка", "Не удалось сохранить напиток")
                return
        dialog = RecipeEditor(self.product_id)
        dialog.exec_()
        self.load()

    def save(self):
        name = self.name_input.text().strip()
        try:
            price = float(self.price_input.text())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Цена должна быть числом")
            return

        category_id = self.category_input.currentData()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Название не может быть пустым")
            return

        conn = get_connection()
        cursor = conn.cursor()
        if self.product_id:
            cursor.execute("""
                UPDATE products SET name=?, price=?, category_id=? WHERE id=?
            """, (name, price, category_id, self.product_id))
        else:
            cursor.execute("""
                INSERT INTO products (name, price, category_id) VALUES (?, ?, ?)
            """, (name, price, category_id))
            self.product_id = cursor.lastrowid
        conn.commit()
        conn.close()
        self.accept()


class RecipeEditor(QDialog):
    def __init__(self, product_id):
        super().__init__()
        self.setWindowTitle("Рецепт напитка")
        self.product_id = product_id
        self.layout = QVBoxLayout()

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Фильтр по названию ингредиента...")
        self.filter_input.textChanged.connect(self.apply_filter)
        self.layout.addWidget(self.filter_input)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Ингредиент", "Кол-во", "Ед. изм.", "Цена за ед.", "Стоимость"])
        self.layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Добавить строку")
        add_btn.clicked.connect(self.add_row)
        btn_row.addWidget(add_btn)

        save_btn = QPushButton("Сохранить рецепт")
        save_btn.clicked.connect(self.save_recipe)
        btn_row.addWidget(save_btn)

        self.layout.addLayout(btn_row)

        self.total_label = QLabel("Итого себестоимость: 0.00 BYN")
        self.layout.addWidget(self.total_label)

        self.setLayout(self.layout)

        self.load_recipe()

    def apply_filter(self):
        text = self.filter_input.text().lower()
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            if name_item:
                name = name_item.text().lower()
                self.table.setRowHidden(row, text not in name)

    def load_recipe(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ingredients.name, pi.quantity, ingredients.unit, ingredients.last_price
            FROM product_ingredients pi
            JOIN ingredients ON pi.ingredient_id = ingredients.id
            WHERE pi.product_id = ?
        """, (self.product_id,))
        rows = cursor.fetchall()
        conn.close()

        for name, qty, unit, price in rows:
            self.add_row(name, qty, unit, price)

    def add_row(self, name="", qty="", unit="", price=0.0):
        row = self.table.rowCount()
        self.table.insertRow(row)

        if name:
            self.table.setItem(row, 0, QTableWidgetItem(name))
        else:
            select_btn = QPushButton("Выбрать")
            select_btn.clicked.connect(partial(self.select_ingredient, row))
            self.table.setCellWidget(row, 0, select_btn)

        qty_input = QLineEdit(str(qty))
        qty_input.setPlaceholderText("например: 0.05")
        qty_input.textChanged.connect(partial(self.update_row, row))
        self.table.setCellWidget(row, 1, qty_input)

        self.table.setItem(row, 2, QTableWidgetItem(unit))
        self.table.setItem(row, 3, QTableWidgetItem(f"{price:.2f}"))
        self.table.setItem(row, 4, QTableWidgetItem(""))

        self.update_row(row)

    def select_ingredient(self, row):
        selector = IngredientSelector(show_price=True)
        if selector.exec_():
            name, unit, price = selector.selected
            self.table.removeCellWidget(row, 0)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 2, QTableWidgetItem(unit))
            self.table.setItem(row, 3, QTableWidgetItem(f"{price:.2f}"))
            self.update_row(row)

    def update_row(self, row):
        qty_input = self.table.cellWidget(row, 1)
        price_item = self.table.item(row, 3)

        try:
            qty = float(qty_input.text())
            price = float(price_item.text())
            cost = qty * price
            self.table.setItem(row, 4, QTableWidgetItem(f"{cost:.2f}"))
        except:
            self.table.setItem(row, 4, QTableWidgetItem(""))

        self.update_total_cost()

    def update_total_cost(self):
        total = 0
        for row in range(self.table.rowCount()):
            cost_item = self.table.item(row, 4)
            if cost_item:
                try:
                    total += float(cost_item.text())
                except:
                    pass
        self.total_label.setText(f"Итого себестоимость: {total:.2f} BYN")

    def save_recipe(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM product_ingredients WHERE product_id = ?", (self.product_id,))

        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            qty_input = self.table.cellWidget(row, 1)

            if not name_item or not qty_input:
                continue

            name = name_item.text().strip()
            if not name:
                continue

            try:
                quantity = float(qty_input.text())
                if quantity <= 0:
                    continue
            except ValueError:
                continue

            cursor.execute("SELECT id FROM ingredients WHERE name = ?", (name,))
            result = cursor.fetchone()
            if not result:
                continue
            ingredient_id = result[0]

            cursor.execute("""
                INSERT INTO product_ingredients (product_id, ingredient_id, quantity)
                VALUES (?, ?, ?)
            """, (self.product_id, ingredient_id, quantity))

        conn.commit()
        conn.close()
        QMessageBox.information(self, "Сохранено", "Рецепт напитка сохранён.")
        self.accept()
