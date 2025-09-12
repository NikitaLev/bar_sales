from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QLabel, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt
from db_init import get_connection

class IngredientSelector(QDialog):
    def __init__(self, show_price=False):
        super().__init__()
        self.setWindowTitle("Выбор ингредиента")
        
        self.setMinimumSize(800, 600)
        self.selected = None
        self.show_price = show_price

        self.layout = QVBoxLayout()

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Поиск по названию...")
        self.filter_input.textChanged.connect(self.apply_filter)
        self.layout.addWidget(QLabel("Фильтр"))
        self.layout.addWidget(self.filter_input)

        self.table = QTableWidget()
        self.table.setColumnCount(4 if show_price else 2)
        headers = ["Название", "Ед. изм."]
        if show_price:
            headers += ["Остаток", "Цена"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setEditTriggers(self.table.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.select_current)
        self.table.setColumnWidth(0, 300)
        self.layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        select_btn = QPushButton("Выбрать")
        select_btn.clicked.connect(self.select_current)
        btn_row.addWidget(select_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self.layout.addLayout(btn_row)
        self.setLayout(self.layout)

        self.load_ingredients()

    def load_ingredients(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, unit, quantity, last_price FROM ingredients")
        self.ingredients = cursor.fetchall()
        conn.close()

        self.table.setRowCount(len(self.ingredients))
        for i, ing in enumerate(self.ingredients):
            self.table.setItem(i, 0, QTableWidgetItem(ing[0]))  # name
            self.table.setItem(i, 1, QTableWidgetItem(ing[1]))  # unit
            if self.show_price:
                self.table.setItem(i, 2, QTableWidgetItem(f"{ing[2]:.2f}"))  # quantity
                self.table.setItem(i, 3, QTableWidgetItem(f"{ing[3]:.2f}"))  # last_price

    def apply_filter(self):
        text = self.filter_input.text().lower()
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            if name_item:
                name = name_item.text().lower()
                self.table.setRowHidden(row, text not in name)

    def select_current(self):
        row = self.table.currentRow()
        if row < 0:
            return

        name = self.table.item(row, 0).text()
        unit = self.table.item(row, 1).text()
        price = 0.0
        if self.show_price and self.table.item(row, 3):
            try:
                price = float(self.table.item(row, 3).text().replace(",", "."))
            except ValueError:
                price = 0.0

        self.selected = (name, unit, price)
        self.accept()
