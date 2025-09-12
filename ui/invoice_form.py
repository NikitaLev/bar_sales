from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QDateEdit, QComboBox
)
from PyQt5.QtCore import QDate
from functools import partial
from db_init import get_connection
from ui.ingredient_selector import IngredientSelector

class InvoiceForm(QDialog):
    def __init__(self, invoice_id=None, invoice_number=None):
        super().__init__()
        self.setWindowTitle("Накладная")
        self.invoice_id = invoice_id
        self.layout = QVBoxLayout()

        self.layout.addWidget(QLabel("Номер накладной"))
        self.number_input = QLineEdit()
        if invoice_id:
            self.number_input.setText(str(invoice_number))
        else:
            self.number_input.setText(str(0))
        self.layout.addWidget(self.number_input)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.layout.addWidget(QLabel("Дата накладной"))
        self.layout.addWidget(self.date_edit)

        self.supplier_combo = QComboBox()
        self.layout.addWidget(QLabel("Поставщик"))
        self.layout.addWidget(self.supplier_combo)
        self.load_suppliers()

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Ингредиент", "Кол-во", "Цена за ед."])
        self.table.cellDoubleClicked.connect(self.edit_ingredient)
        self.layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Добавить строку")
        add_btn.clicked.connect(self.add_row)
        btn_row.addWidget(add_btn)

        save_btn = QPushButton("Сохранить накладную")
        save_btn.clicked.connect(self.save_invoice)
        btn_row.addWidget(save_btn)

        self.layout.addLayout(btn_row)

        self.total_label = QLabel("Общая сумма: 0.00 BYN")
        self.layout.addWidget(self.total_label)

        self.setLayout(self.layout)

        if invoice_id:
            self.load_invoice()

    def load_suppliers(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM suppliers")
        self.suppliers = cursor.fetchall()
        for sid, name in self.suppliers:
            self.supplier_combo.addItem(name, sid)
        conn.close()

    def load_invoice(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT date, supplier_id, number FROM invoices WHERE id = ?", (self.invoice_id,))
        result = cursor.fetchone()
        if result:
            date_str, supplier_id, number = result
            self.date_edit.setDate(QDate.fromString(date_str, "yyyy-MM-dd"))
            index = next((i for i, (sid, _) in enumerate(self.suppliers) if sid == supplier_id), 0)
            self.supplier_combo.setCurrentIndex(index)

        cursor.execute("""
            SELECT ingredients.name, invoice_items.quantity, invoice_items.price
            FROM invoice_items
            JOIN ingredients ON invoice_items.ingredient_id = ingredients.id
            WHERE invoice_items.invoice_id = ?
        """, (self.invoice_id,))
        rows = cursor.fetchall()
        conn.close()

        for name, qty, price in rows:
            self.add_row(name, qty, price)

    def add_row(self, name="", qty="", price=""):
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
        qty_input.textChanged.connect(self.update_total)
        self.table.setCellWidget(row, 1, qty_input)

        price_input = QLineEdit(str(price))
        price_input.setPlaceholderText("например: 12.5")
        price_input.textChanged.connect(self.update_total)
        self.table.setCellWidget(row, 2, price_input)

        self.update_total()

    def select_ingredient(self, row):
        selector = IngredientSelector(show_price=True)
        if selector.exec_():
            name, unit, price = selector.selected
            self.table.removeCellWidget(row, 0)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setCellWidget(row, 2, QLineEdit(str(price)))
            self.update_total()

    def edit_ingredient(self, row, column):
        if column == 0:
            self.select_ingredient(row)

    def update_total(self):
        total = 0
        for row in range(self.table.rowCount()):
            qty_input = self.table.cellWidget(row, 1)
            price_input = self.table.cellWidget(row, 2)
            try:
                qty = float(qty_input.text().replace(",", "."))
                price = float(price_input.text().replace(",", "."))
                total += qty * price
            except:
                continue
        self.total_label.setText(f"Общая сумма: {total:.2f} BYN")

    def save_invoice(self):
        conn = get_connection()
        cursor = conn.cursor()
        is_change = True
        number = self.number_input.text()
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        supplier_id = self.supplier_combo.currentData()

        if not self.invoice_id:
            cursor.execute("INSERT INTO invoices (date, supplier_id, number) VALUES (?, ?, ?)", (date_str, supplier_id, number))
            self.invoice_id = cursor.lastrowid
            is_change = False
        else:
            cursor.execute("UPDATE invoices SET date = ?, supplier_id = ?, number = ? WHERE id = ?", (date_str, supplier_id, number, self.invoice_id))

        if is_change:
            cursor.execute(
                "SELECT ingredient_id, quantity FROM invoice_items WHERE invoice_id = ?",
                (self.invoice_id,)
            )
            old_items = cursor.fetchall()  # список кортежей (ingredient_id, quantity)
            for ingredient_id, old_qty in old_items:
                cursor.execute(
                    "UPDATE ingredients "
                    "SET quantity = quantity - ? "
                    "WHERE id = ?",
                    (old_qty, ingredient_id)
                )
            cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (self.invoice_id,))

        saved_rows = 0
        failed_rows = []

        for row in range(self.table.rowCount()):
            if self.table.cellWidget(row, 0):
                failed_rows.append(row + 1)
                continue

            name_item = self.table.item(row, 0)
            qty_input = self.table.cellWidget(row, 1)
            price_input = self.table.cellWidget(row, 2)

            if not name_item or not qty_input or not price_input:
                failed_rows.append(row + 1)
                continue

            name = name_item.text().strip()
            if not name:
                failed_rows.append(row + 1)
                continue

            try:
                quantity = float(qty_input.text().replace(",", "."))
                price = float(price_input.text().replace(",", "."))
                if quantity <= 0 or price < 0:
                    failed_rows.append(row + 1)
                    continue
            except ValueError:
                failed_rows.append(row + 1)
                continue

            cursor.execute("SELECT id FROM ingredients WHERE name = ?", (name,))
            result = cursor.fetchone()
            if not result:
                failed_rows.append(row + 1)
                continue
            ingredient_id = result[0]

            cursor.execute("""
                INSERT INTO invoice_items (invoice_id, ingredient_id, quantity, price)
                VALUES (?, ?, ?, ?)
            """, (self.invoice_id, ingredient_id, quantity, price))

            cursor.execute("""
                UPDATE ingredients
                SET quantity = quantity + ?, last_price = ?
                WHERE id = ?
            """, (quantity, price, ingredient_id))

            saved_rows += 1

        conn.commit()
        conn.close()

        if saved_rows == 0:
            QMessageBox.warning(self, "Ошибка", "Ни одна строка не была сохранена. Проверьте выбор и формат данных.")
        else:
            msg = f"Накладная сохранена.\nСтрок сохранено: {saved_rows}"
            if failed_rows:
                msg += f"\nПропущены строки: {', '.join(map(str, failed_rows))}"
            QMessageBox.information(self, "Сохранено", msg)
            self.accept()
