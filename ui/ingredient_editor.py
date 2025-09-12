from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QDialog, QLabel, QLineEdit, QMessageBox
)
from db_init import get_connection

class IngredientEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ингредиенты")
        self.layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Название", "Остаток", "Ед. изм."])
        self.table.cellDoubleClicked.connect(self.edit_ingredient)
        self.table.setColumnWidth(1, 250)
        self.layout.addWidget(self.table)
        self.setMinimumSize(800, 600)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(self.add_ingredient)
        btn_row.addWidget(add_btn)

        delete_btn = QPushButton("Удалить выбранный")
        delete_btn.clicked.connect(self.delete_ingredient)
        btn_row.addWidget(delete_btn)

        self.layout.addLayout(btn_row)
        self.setLayout(self.layout)

        self.load_ingredients()

    def load_ingredients(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, quantity, unit FROM ingredients")
        rows = cursor.fetchall()
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                # округление не целочисленных значений до 7 знаков после запятой
                if j == 2:
                    try:
                        num = float(value)
                    except (TypeError, ValueError):
                        text = str(value)
                    else:
                        if num.is_integer():
                            text = str(int(num))
                        else:
                            text = f"{num:.7f}"
                else:
                    text = str(value)

                self.table.setItem(i, j, QTableWidgetItem(text))
        conn.close()

    def add_ingredient(self):
        dialog = IngredientForm()
        dialog.exec_()
        self.load_ingredients()

    def edit_ingredient(self, row, column):
        ing_id = int(self.table.item(row, 0).text())
        dialog = IngredientForm(ing_id)
        dialog.exec_()
        self.load_ingredients()

    def delete_ingredient(self):
        selected = self.table.currentRow()
        if selected < 0:
            return
        ing_id = int(self.table.item(selected, 0).text())
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ingredients WHERE id = ?", (ing_id,))
        conn.commit()
        conn.close()
        self.load_ingredients()


class IngredientForm(QDialog):
    def __init__(self, ingredient_id=None):
        super().__init__()
        self.setWindowTitle("Редактировать ингредиент" if ingredient_id else "Добавить ингредиент")
        self.ingredient_id = ingredient_id
        self.setMinimumSize(600, 200)
        self.layout = QVBoxLayout()

        self.name_input = QLineEdit()
        self.qty_input = QLineEdit()
        self.unit_input = QLineEdit()

        self.layout.addWidget(QLabel("Название"))
        self.layout.addWidget(self.name_input)
        self.layout.addWidget(QLabel("Остаток"))
        self.layout.addWidget(self.qty_input)
        self.layout.addWidget(QLabel("Ед. изм."))
        self.layout.addWidget(self.unit_input)

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save)
        self.layout.addWidget(save_btn)

        self.setLayout(self.layout)

        if ingredient_id:
            self.load()

    def load(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, quantity, unit FROM ingredients WHERE id = ?", (self.ingredient_id,))
        name, qty, unit = cursor.fetchone()
        self.name_input.setText(name)
        self.qty_input.setText(str(qty))
        self.unit_input.setText(unit)
        conn.close()

    def save(self):
        name = self.name_input.text().strip()
        unit = self.unit_input.text().strip()
        try:
            qty = float(self.qty_input.text())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Остаток должен быть числом")
            return

        if not name or not unit:
            QMessageBox.warning(self, "Ошибка", "Все поля обязательны")
            return

        conn = get_connection()
        cursor = conn.cursor()
        if self.ingredient_id:
            cursor.execute("""
                UPDATE ingredients SET name=?, quantity=?, unit=? WHERE id=?
            """, (name, qty, unit, self.ingredient_id))
        else:
            cursor.execute("""
                INSERT INTO ingredients (name, quantity, unit) VALUES (?, ?, ?)
            """, (name, qty, unit))
        conn.commit()
        conn.close()
        self.accept()
