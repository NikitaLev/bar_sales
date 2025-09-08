from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QDialog, QSpinBox
)
from models import get_ingredient_stock, get_low_stock

class StockManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Склад: учёт ингредиентов")
        self.layout = QVBoxLayout()

        # 🔹 Таблица всех остатков
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(3)
        self.stock_table.setHorizontalHeaderLabels(["Название", "Остаток", "Ед. изм."])
        self.layout.addWidget(QLabel("Все ингредиенты"))
        self.layout.addWidget(self.stock_table)
        self.setMinimumSize(800, 600)

        # 🔹 Кнопки
        btn_row = QHBoxLayout()
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_stock)
        btn_row.addWidget(refresh_btn)

        low_btn = QPushButton("Показать дефицит")
        low_btn.clicked.connect(self.show_low_stock)
        btn_row.addWidget(low_btn)

        self.layout.addLayout(btn_row)
        self.setLayout(self.layout)

        self.load_stock()

    def load_stock(self):
        stock = get_ingredient_stock()
        self.stock_table.setRowCount(len(stock))
        for i, (name, qty, unit) in enumerate(stock):
            self.stock_table.setItem(i, 0, QTableWidgetItem(name))
            self.stock_table.setItem(i, 1, QTableWidgetItem(f"{qty:.2f}"))
            self.stock_table.setItem(i, 2, QTableWidgetItem(unit))

    def show_low_stock(self):
        dialog = LowStockDialog()
        dialog.exec_()


class LowStockDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Дефицит ингредиентов")
        self.layout = QVBoxLayout()

        self.threshold_input = QSpinBox()
        self.threshold_input.setRange(1, 10000)
        self.threshold_input.setValue(50)
        self.layout.addWidget(QLabel("Порог остатка (меньше — дефицит):"))
        self.layout.addWidget(self.threshold_input)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Название", "Остаток", "Ед. изм."])
        self.layout.addWidget(self.table)

        btn = QPushButton("Показать")
        btn.clicked.connect(self.load)
        self.layout.addWidget(btn)

        self.setLayout(self.layout)

    def load(self):
        threshold = self.threshold_input.value()
        low = get_low_stock(threshold)
        self.table.setRowCount(len(low))
        for i, (name, qty, unit) in enumerate(low):
            self.table.setItem(i, 0, QTableWidgetItem(name))
            self.table.setItem(i, 1, QTableWidgetItem(f"{qty:.2f}"))
            self.table.setItem(i, 2, QTableWidgetItem(unit))
