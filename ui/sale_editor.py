import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QSpinBox,
    QPushButton, QHBoxLayout, QLineEdit, QDateEdit, QDialog, QLabel, QComboBox, QCheckBox, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QDate
from PyQt5.QtCore import QDateTime
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtWidgets import QDateTimeEdit
from PyQt5.QtGui import QColor, QTextDocument
from models import get_sales,get_products, get_sale_items, update_sale_status, update_sale_items, _get_saved_total
from datetime import datetime
import datetime
from functools import partial

from receipt_printer import print_receipt

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
        for i, (sid, date, total, paid, method, guest_name, c1) in enumerate(sales):
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

        # поле даты
        self.date_edit = QDateTimeEdit()
        self.date_edit.setCalendarPopup(True)
        self.layout.addWidget(QLabel("Дата чека"))
        self.layout.addWidget(self.date_edit)


        self.guest_label = QLabel("Гость: —")
        self.layout.addWidget(self.guest_label)

        self.paid_checkbox = QCheckBox("Оплачено")
        self.payment_method = QComboBox()
        self.payment_method.addItems(["Нал", "Безнал"])
        self.layout.addWidget(QLabel("Статус оплаты"))
        self.layout.addWidget(self.paid_checkbox)
        self.layout.addWidget(QLabel("Метод оплаты"))
        self.layout.addWidget(self.payment_method)
        self.setMinimumSize(600, 500)

        self.item_table = QTableWidget()
        self.item_table.setColumnCount(3)
        self.item_table.setHorizontalHeaderLabels(["Название", "Кол-во", "Цена"])
        self.layout.addWidget(QLabel("Состав счёта"))
        self.layout.addWidget(self.item_table)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save)
        btn_row.addWidget(save_btn)

        # НОВАЯ КНОПКА: редактирование содержимого
        edit_items_btn = QPushButton("Редактировать")
        edit_items_btn.clicked.connect(self.open_edit_items)
        btn_row.addWidget(edit_items_btn)

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
        for sid, date, total, paid, method, guest_name, c1 in sales:
            if sid == self.sale_id:
                self.paid_checkbox.setChecked(bool(paid))
                self.payment_method.setCurrentText(method)
                self.guest_label.setText(f"Гость: {guest_name}")

                # преобразуем строку даты из БД в QDateTime
                qt_dt = QDateTime.fromString(date, "yyyy-MM-dd HH:mm:ss")
                if qt_dt.isValid():
                    self.date_edit.setDateTime(qt_dt)
                else:
                    from datetime import datetime as py_dt
                    try:
                        d = py_dt.strptime(date, "%Y-%m-%d %H:%M:%S")
                        self.date_edit.setDateTime(QDateTime(d))
                    except Exception:
                        pass
                break

    def open_edit_items(self):
        dlg = SaleEditDialog(self.sale_id, self)
        if dlg.exec_():
            # после сохранения — перезагрузим таблицу и статус (итог мог измениться)
            self.load_items()
            self.load_status()

    def save(self):
        paid = self.paid_checkbox.isChecked()
        method = self.payment_method.currentText()
        new_date = self.date_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")

        update_sale_status(self.sale_id, paid, method, new_date)
        QMessageBox.information(self, "Готово", "Статус обновлён.")
        self.accept()

    def print_receipt(self):
        guest = self.guest_label.text().replace("Гость: ", "")
        method = self.payment_method.currentText()

        items = get_sale_items(self.sale_id)

        print_receipt(self, self.sale_id, guest, self.paid_checkbox.isChecked(), method, items)


class SaleEditDialog(QDialog):
    def __init__(self, sale_id, parent=None):
        super().__init__(parent)
        self.sale_id = sale_id
        self.saved_total = _get_saved_total(self)
        self.setWindowTitle(f"Редактирование чека #{sale_id}")
        self.setMinimumSize(600, 400)

        self.layout = QVBoxLayout(self)

        # Панель добавления позиции
        add_row = QHBoxLayout()
        add_row.addWidget(QLabel("Товар:"))
        self.product_combo = QComboBox()
        self.products = self._load_products()  # {name: (id, price)}
        self.product_combo.addItems(list(self.products.keys()))
        add_row.addWidget(self.product_combo)

        add_row.addWidget(QLabel("Кол-во:"))
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 1000)
        self.qty_spin.setValue(1)
        add_row.addWidget(self.qty_spin)

        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(self.add_item)
        add_row.addWidget(add_btn)

        self.layout.addLayout(add_row)

        # Таблица текущих позиций: Название | Цена | Кол-во | Удалить
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Название", "Цена", "Кол-во", ""])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.layout.addWidget(self.table)

        # Итоговая сумма
        self.total_label = QLabel("Итого: 0.00 BYN")
        font = self.total_label.font()
        font.setPointSize(14)
        font.setBold(True)
        self.total_label.setFont(font)
        self.total_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.layout.addWidget(self.total_label)

        # Кнопки управления
        btn_row = QHBoxLayout()
        save_btn = QPushButton("Сохранить изменения")
        save_btn.clicked.connect(self.save_changes)
        btn_row.addWidget(save_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self.layout.addLayout(btn_row)

        # внутреннее хранилище позиций: list of dict
        # [{"product_id": int, "name": str, "price": float, "qty": int}]
        self.items = []
        self._load_sale_items()
        self._refresh_table()
        self._update_total()

    def _load_products(self):
        # Словарь name -> (id, price)
        mapping = {}
        for pid, name, price, *_ in get_products():
            mapping[name] = (pid, float(price))
        return mapping

    def _load_sale_items(self):
        self.items.clear()
        for name, qty, price in get_sale_items(self.sale_id):
            qty_val = int(qty) if str(qty).isdigit() else int(float(qty))
            self.items.append({
                "product_id": self.products.get(name, (None, float(price)))[0],
                "name": name,
                "price": float(price),
                "qty": qty_val
            })

    def _refresh_table(self):
        self.table.setRowCount(len(self.items))
        for i, it in enumerate(self.items):
            # Название
            self.table.setItem(i, 0, QTableWidgetItem(it["name"]))
            # Цена
            self.table.setItem(i, 1, QTableWidgetItem(f"{it['price']:.2f}"))
            # Кол-во — редактируемое
            qty_item = QTableWidgetItem(str(it["qty"]))
            qty_item.setFlags(qty_item.flags() | Qt.ItemIsEditable)
            self.table.setItem(i, 2, qty_item)

            # Удалить
            del_btn = QPushButton("Удалить")
            del_btn.clicked.connect(partial(self.remove_row, i))
            self.table.setCellWidget(i, 3, del_btn)
        self._update_total()

    def _update_total(self):
        new_total = sum(it["price"] * it["qty"] for it in self.items)
        diff = new_total - self.saved_total

        # формируем строку с разницей
        if abs(diff) < 0.001:
            diff_text = "(без изменений)"
        elif diff > 0:
            diff_text = f"(+{diff:.2f})"
        else:
            diff_text = f"({diff:.2f})"

        self.total_label.setText(
            f"Итого: {new_total:.2f} BYN | было: {self.saved_total:.2f} BYN {diff_text}"
        )


    def add_item(self):
        name = self.product_combo.currentText()
        pid, price = self.products[name]
        qty = int(self.qty_spin.value())

        # если уже в списке — увеличим количество
        for it in self.items:
            if it["product_id"] == pid:
                it["qty"] += qty
                self._refresh_table()
                return

        self.items.append({
            "product_id": pid,
            "name": name,
            "price": float(price),
            "qty": qty
        })
        self._refresh_table()

    def remove_row(self, idx):
        if 0 <= idx < len(self.items):
            self.items.pop(idx)
            self._refresh_table()

    def save_changes(self):
        # cчитываем количество из таблицы перед сохранением
        for i, it in enumerate(self.items):
            qty_item = self.table.item(i, 2)
            try:
                it["qty"] = int(float(qty_item.text()))
            except Exception:
                it["qty"] = 1

        # подготовка для модели: [(product_id, price, qty), ...]
        items_for_db = [(it["product_id"], it["price"], it["qty"]) for it in self.items]

        try:
            update_sale_items(self.sale_id, items_for_db)
            QMessageBox.information(self, "Готово", "Состав чека обновлён.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить изменения:\n{e}")
        
