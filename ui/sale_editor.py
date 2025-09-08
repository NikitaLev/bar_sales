from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QDialog, QLabel, QComboBox, QCheckBox, QMessageBox
)
from PyQt5.QtGui import QColor
from models import get_sales, get_sale_items, update_sale_status

class SaleEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Счета")
        self.layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(6)  # ✅ добавлена колонка "Гость"
        self.table.setHorizontalHeaderLabels(["ID", "Дата", "Сумма", "Оплачено", "Метод", "Гость"])
        self.table.cellDoubleClicked.connect(self.edit_sale)
        self.layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_sales)
        btn_row.addWidget(refresh_btn)

        self.layout.addLayout(btn_row)
        self.setLayout(self.layout)

        self.load_sales()

    def load_sales(self):
        sales = get_sales()
        self.table.setRowCount(len(sales))
        for i, (sid, date, total, paid, method, guest_name) in enumerate(sales):
            self.table.setItem(i, 0, QTableWidgetItem(str(sid)))
            self.table.setItem(i, 1, QTableWidgetItem(date))
            self.table.setItem(i, 2, QTableWidgetItem(f"{total:.2f} BYN"))
            self.table.setItem(i, 3, QTableWidgetItem("Да" if paid else "Нет"))
            self.table.setItem(i, 4, QTableWidgetItem(method))
            self.table.setItem(i, 5, QTableWidgetItem(guest_name))  # ✅ имя гостя

            color = QColor(200, 255, 200) if paid else QColor(255, 200, 200)
            for col in range(6):
                self.table.item(i, col).setBackground(color)

    def edit_sale(self, row, column):
        sale_id = int(self.table.item(row, 0).text())
        dialog = SaleForm(sale_id)
        dialog.exec_()
        self.load_sales()


class SaleForm(QDialog):
    def __init__(self, sale_id):
        super().__init__()
        self.sale_id = sale_id
        self.setWindowTitle(f"Счёт #{sale_id}")
        self.layout = QVBoxLayout()

        self.guest_label = QLabel("Гость: —")
        self.layout.addWidget(self.guest_label)

        self.paid_checkbox = QCheckBox("Оплачено")
        self.payment_method = QComboBox()
        self.payment_method.addItems(["Нал", "Безнал"])
        self.layout.addWidget(QLabel("Статус оплаты"))
        self.layout.addWidget(self.paid_checkbox)
        self.layout.addWidget(QLabel("Метод оплаты"))
        self.layout.addWidget(self.payment_method)

        self.item_table = QTableWidget()
        self.item_table.setColumnCount(3)
        self.item_table.setHorizontalHeaderLabels(["Название", "Кол-во", "Цена"])
        self.layout.addWidget(QLabel("Состав счёта"))
        self.layout.addWidget(self.item_table)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save)
        btn_row.addWidget(save_btn)

        print_btn = QPushButton("Печать")
        btn_row.addWidget(print_btn)

        self.layout.addLayout(btn_row)
        self.setLayout(self.layout)

        self.load_items()
        self.load_status()

    def load_items(self):
        items = get_sale_items(self.sale_id)
        self.item_table.setRowCount(len(items))
        for i, (name, qty, price) in enumerate(items):
            self.item_table.setItem(i, 0, QTableWidgetItem(name))
            self.item_table.setItem(i, 1, QTableWidgetItem(str(qty)))
            self.item_table.setItem(i, 2, QTableWidgetItem(f"{price:.2f}"))

    def load_status(self):
        sales = get_sales()
        for sid, date, total, paid, method, guest_name in sales:
            if sid == self.sale_id:
                self.paid_checkbox.setChecked(bool(paid))
                self.payment_method.setCurrentText(method)
                self.guest_label.setText(f"Гость: {guest_name}")
                break

    def save(self):
        paid = self.paid_checkbox.isChecked()
        method = self.payment_method.currentText()
        update_sale_status(self.sale_id, paid, method)
        QMessageBox.information(self, "Готово", "Статус обновлён.")
        self.accept()

