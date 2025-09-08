from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QLineEdit, QDialog, QLabel, QComboBox, QCheckBox, QMessageBox
)
from PyQt5.QtGui import QColor
from models import get_sales, get_sale_items, update_sale_status

class SaleEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Счета")
        self.setMinimumSize(800, 600)
        self.layout = QVBoxLayout()

         # — фильтры —
        fl = QHBoxLayout()
        # дата
        fl.addWidget(QLabel("Дата:"))
        self.date_filter = QLineEdit()
        self.date_filter.setPlaceholderText("YYYY-MM-DD")
        fl.addWidget(self.date_filter)   

         # диапазон по сумме
        fl.addWidget(QLabel("Сумма от:"))
        self.sum_min = QLineEdit()
        self.sum_min.setPlaceholderText("мин")
        fl.addWidget(self.sum_min)

        fl.addWidget(QLabel("до:"))
        self.sum_max = QLineEdit()
        self.sum_max.setPlaceholderText("макс")
        fl.addWidget(self.sum_max)

        # оплата
        fl.addWidget(QLabel("Оплачено:"))
        self.paid_filter = QComboBox()
        self.paid_filter.addItems(["Все","Да", "Нет"])
        fl.addWidget(self.paid_filter)
        # метод
        fl.addWidget(QLabel("Метод:"))
        self.method_filter = QComboBox()
        self.method_filter.addItems(["Все", "Нал", "Безнал"])
        fl.addWidget(self.method_filter)
        # гость
        fl.addWidget(QLabel("Гость:"))
        self.guest_filter = QLineEdit()
        self.guest_filter.setPlaceholderText("имя гостя")
        fl.addWidget(self.guest_filter)

        # после fl.addWidget(self.guest_filter)
        apply_btn = QPushButton("Применить фильтр")
        fl.addWidget(apply_btn)

        # подключаем фильтрацию только по клику
        apply_btn.clicked.connect(self.apply_filters)

        reset_btn = QPushButton("Сбросить фильтры")
        fl.addWidget(reset_btn)
        reset_btn.clicked.connect(self.reset_filters)

        self.layout.addLayout(fl)

        self.table = QTableWidget()
        self.table.setColumnCount(6)  # ✅ добавлена колонка "Гость"
        self.table.setHorizontalHeaderLabels(["ID", "Дата", "Сумма", "Оплачено", "Метод", "Гость"])
        self.table.setSortingEnabled(True)
        self.table.cellDoubleClicked.connect(self.edit_sale)
        self.table.setColumnWidth(1, 150)
        self.layout.addWidget(self.table)


        btn_row = QHBoxLayout()
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_sales)
        btn_row.addWidget(refresh_btn)

        self.layout.addLayout(btn_row)
        self.setLayout(self.layout)

        self.load_sales()

    def reset_filters(self):
        self.date_filter.clear()
        self.sum_min.clear()
        self.sum_max.clear()
        self.paid_filter.setCurrentIndex(0)
        self.method_filter.setCurrentIndex(0)
        self.guest_filter.clear()
        self.apply_filters()


    def apply_filters(self):
        # текстовые фильтры
        df = self.date_filter.text().lower().strip()
        pf = self.paid_filter.currentText()
        mf = self.method_filter.currentText()
        gf = self.guest_filter.text().lower().strip()

        # диапазон суммы
        sm = None
        sx = None
        try:
            sm_text = self.sum_min.text().strip()
            if sm_text:
                sm = float(sm_text)
        except ValueError:
            sm = None

        try:
            sx_text = self.sum_max.text().strip()
            if sx_text:
                sx = float(sx_text)
        except ValueError:
            sx = None

        for row in range(self.table.rowCount()):
            date = self.table.item(row, 1).text().lower()
            total_str = self.table.item(row, 2).text().split()[0]
            paid = self.table.item(row, 3).text()
            method = self.table.item(row, 4).text()
            guest = self.table.item(row, 5).text().lower()

            # текущее значение суммы
            try:
                current_sum = float(total_str)
            except ValueError:
                current_sum = None

            show = True
            # фильтр по дате
            if df and df not in date:
                show = False

            # фильтр по сумме-диапазону
            if sm is not None and (current_sum is None or current_sum < sm):
                show = False
            if sx is not None and (current_sum is None or current_sum > sx):
                show = False

            # остальные фильтры
            if pf != "Все" and paid != pf:
                show = False
            if mf != "Все" and method != mf:
                show = False
            if gf and gf not in guest:
                show = False

            self.table.setRowHidden(row, not show)


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
        
        # после заполнения — применяем текущие фильтры
        self.apply_filters()

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
        self.setMinimumSize(400, 300)

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

