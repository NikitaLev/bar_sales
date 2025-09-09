import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QLineEdit, QDateEdit, QDialog, QLabel, QComboBox, QCheckBox, QMessageBox
)
from PyQt5.QtCore import QDate

from PyQt5.QtGui import QColor
from models import get_sales, get_sale_items, update_sale_status
from datetime import datetime
import datetime

class SaleEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Счета")
        self.setMinimumSize(800, 600)
        self.layout = QVBoxLayout()

         # — фильтры —
        fl = QHBoxLayout()

        QV_column = QVBoxLayout()

        fl1 = QHBoxLayout()
        fl2 = QHBoxLayout()

        fl1.addWidget(QLabel("Дата от:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        # по умолчанию — вчера
        self.date_from.setDate(QDate.currentDate().addDays(-1))
        self.date_from.setFixedWidth(100)
        fl1.addWidget(self.date_from)


        fl1.addWidget(QLabel("До:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        # по умолчанию — сегодня
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setFixedWidth(100)
        fl1.addWidget(self.date_to)


        fl2.addWidget(QLabel("Сумма от:"))
        self.sum_min = QLineEdit()
        self.sum_min.setPlaceholderText("мин")
        self.sum_min.setFixedWidth(100)
        fl2.addWidget(self.sum_min)


        fl2.addWidget(QLabel("До:"))
        self.sum_max = QLineEdit()
        self.sum_max.setPlaceholderText("макс")
        self.sum_max.setFixedWidth(100)
        fl2.addWidget(self.sum_max)

        QV_column.addLayout(fl1)
        QV_column.addLayout(fl2)
        
        fl.addLayout(QV_column)
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
        self.date_from.setDate(QDate.currentDate().addDays(-1))
        self.date_to.setDate(QDate.currentDate())
        self.sum_min.clear()
        self.sum_max.clear()
        self.paid_filter.setCurrentIndex(0)
        self.method_filter.setCurrentIndex(0)
        self.guest_filter.clear()
        self.apply_filters()


    def apply_filters(self):
        # текстовые фильтры
        df = self.date_from.date().toPyDate()
        dt = self.date_to.date().toPyDate()
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
            date_str = self.table.item(row, 1).text()
            show = True
            # фильтр по дате-диапазону
            date_str = self.table.item(row, 1).text()
            try:
                current_dt = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").date()
            except:
                current_dt = None

            if not current_dt or current_dt < df or current_dt > dt:
                show = False

            total_str = self.table.item(row, 2).text().split()[0]
            paid = self.table.item(row, 3).text()
            method = self.table.item(row, 4).text()
            guest = self.table.item(row, 5).text().lower()

            # текущее значение суммы
            try:
                current_sum = float(total_str)
            except ValueError:
                current_sum = None

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
    def try_float(s):
        try: return float(s.strip())
        except: return None


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
        print_btn.clicked.connect(self.print_receipt)

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

    def print_receipt(self):
        guest = self.guest_label.text().replace("Гость: ", "")
        paid = "Оплачено" if self.paid_checkbox.isChecked() else "Не оплачено"
        method = self.payment_method.currentText()

        items = get_sale_items(self.sale_id)

        total_sum = sum(qty * price for name, qty, price in items)

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Шаблон HTML
        html = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
          <meta charset="utf-8">
          <title>Чек #{self.sale_id}</title>
          <style>
            body {{ font-family: sans-serif; max-width: 300px; }}
            h2, h3 {{ text-align: center; margin: 0; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ padding: 4px; border-bottom: 1px dashed #444; }}
            .right {{ text-align: right; }}
          </style>
        </head>
        <body>
          <h2>ИП «КОММУНА»</h2>
          <h3>Чек №{self.sale_id}</h3>
          <p>
            Адрес: Тот самый адрес<br>
            УНП: 123456789<br>
            Касса: 01<br>
            Дата: {now}<br>
            Гость: {guest}<br>
            Статус: {paid}, {method}
          </p>
          <table>
            <tr><th>Товар</th><th>Кол-во</th><th class="right">Цена</th></tr>
        """

        # Строки таблицы с товарами
        for name, qty, price in items:
            line_sum = qty * price
            html += (
                f"<tr>"
                f"<td>{name}</td>"
                f"<td class='right'>{qty:.3f}</td>"
                f"<td class='right'>{line_sum:.2f}</td>"
                f"</tr>"
            )

        # Вывод итоговой суммы
        html += f"""
          </table>
          <h3 class="right">Итого: {total_sum:.2f} BYN</h3>
          <p style="text-align:center; margin-top:20px;">
            Спасибо за покупку!
          </p>
        </body>
        </html>
        """

        filename = f"cheque_{self.sale_id}.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)

        QMessageBox.information(self, "Печать", f"Чек сохранён: {os.path.abspath(filename)}")

