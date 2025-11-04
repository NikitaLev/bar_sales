from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDateEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QFileDialog,
    QMessageBox, QSizePolicy, QCheckBox
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QColor
from datetime import datetime
from openpyxl import Workbook
from models import get_sales, get_sale_items

class Report1CViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Отчёт")
        self.setMinimumSize(1000, 600)

        self.left_checkboxes = {}
        self.right_checkboxes = {}

        main_layout = QVBoxLayout()
        controls_layout = QHBoxLayout()

        # Даты
        self.start_date = QDateEdit(); 
        self.start_date.setCalendarPopup(True); 
        self.start_date.setDate(QDate.currentDate().addDays(-1))
        self.end_date   = QDateEdit(); 
        self.end_date.setCalendarPopup(True); 
        self.end_date.setDate(QDate.currentDate())

        controls_layout.addWidget(QLabel("С:")); controls_layout.addWidget(self.start_date)
        controls_layout.addWidget(QLabel("По:")); controls_layout.addWidget(self.end_date)

        # Кнопки: формирование отчёта и только экспорт правой таблицы
        self.generate_btn = QPushButton("Сформировать отчёт"); self.generate_btn.clicked.connect(self.generate_report)
        controls_layout.addWidget(self.generate_btn)

        self.export_right_btn = QPushButton("Экспорт правой таблицы")
        self.export_right_btn.clicked.connect(lambda: self.export_right_table_to_excel())
        controls_layout.addWidget(self.export_right_btn)

        main_layout.addLayout(controls_layout)

        # Таблицы
        tables_row = QHBoxLayout()

        # левая таблица: чекбокс | Дата | Сумма | Оплачено | Метод | Гость | sale_id (скрытая)| 1C (Скрытая)
        self.left_table = QTableWidget(); self.left_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.left_table.setColumnCount(8)
        self.left_table.setHorizontalHeaderLabels(["Вкл", "Дата", "Сумма", "Оплачено", "Метод", "Гость", "sale_id", "1C"])
        self.left_table.hideColumn(6)
        self.left_table.hideColumn(7)
        # правая таблица: чекбокс | Название | Кол-во | Метод
        self.right_table = QTableWidget(); self.right_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.right_table.setColumnCount(4)
        self.right_table.setHorizontalHeaderLabels(["Вкл", "Название", "Кол-во", "Метод"])

        tables_row.addWidget(self.left_table)
        tables_row.addWidget(self.right_table)
        main_layout.addLayout(tables_row)

        self.setLayout(main_layout)

        # Цвета для подсветки (приглушённые)
        self._color_paid = QColor("#e6f4ea")
        self._color_not_paid = QColor("#f7e6e6")
        self._color_cash = QColor("#eaf6e6")
        self._color_non_cash = QColor("#f7eeec")

    def _insert_checkbox(self, table, row, col=0, mapping=None, checked=False):
        cb = QCheckBox()
        cb.setChecked(checked)
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setAlignment(Qt.AlignCenter)
        l.addWidget(cb)
        table.setCellWidget(row, col, w)
        if mapping is not None:
            mapping[row] = cb
        return cb

    def get_period(self):
        start = self.start_date.date().toPyDate().strftime("%Y-%m-%d")
        end = self.end_date.date().toPyDate().strftime("%Y-%m-%d")
        return start, end

    def generate_report(self):
        start_str, end_str = self.get_period()
        start_dt = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_dt   = datetime.strptime(end_str, "%Y-%m-%d").date()

        sales = get_sales()  # id, date, total, paid, payment_method, guest_name

        rows = []
        raw_meta = []
        for sale in sales:
            sale_id, date_raw, total, paid, method, guest, c1  = sale

            sale_date_obj = None
            if isinstance(date_raw, str):
                parsed = None
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                    try:
                        parsed = datetime.strptime(date_raw, fmt)
                        break
                    except ValueError:
                        continue
                if parsed is None:
                    continue
                sale_date_obj = parsed
            elif isinstance(date_raw, (int, float)):
                sale_date_obj = datetime.fromtimestamp(date_raw)
            else:
                continue

            sale_date_only = sale_date_obj.date()
            if not (start_dt <= sale_date_only <= end_dt):
                continue

            paid_text = "Да" if bool(paid) else "Нет"

            if method is None:
                method_text = ""
            else:
                if isinstance(method, (int, float)):
                    method_text = "Нал" if int(method) == 0 else "Безнал"
                else:
                    method_text = str(method)

            rows.append([
                sale_date_obj.strftime("%Y-%m-%d %H:%M:%S"),
                f"{total:.2f}",
                paid_text,
                method_text,
                guest or "",
                sale_id, 
                c1
            ])
            raw_meta.append((bool(paid), method_text, sale_id, c1))

        headers = ["Вкл", "Дата", "Сумма", "Оплачено", "Метод", "Гость", "sale_id", "1C"]
        self.left_table.clear()
        self.left_table.setColumnCount(len(headers))
        self.left_table.setHorizontalHeaderLabels(headers)
        self.left_table.setRowCount(len(rows))
        self.left_checkboxes.clear()

        for i, row in enumerate(rows):
            paid_bool, method_text, _sid, c1_value = raw_meta[i]
            is_non_cash = str(method_text).lower() in ("безнал", "безналичный")
            c1_bool = bool(int(c1_value)) if c1_value is not None else False
            auto_checked = is_non_cash or c1_bool

            # вставляем чекбокс с автоустановкой
            cb = self._insert_checkbox(self.left_table, i, 0, mapping=self.left_checkboxes, checked=auto_checked)
            cb.stateChanged.connect(self._rebuild_right_table_from_selection)

            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                self.left_table.setItem(i, j + 1, item)

            paid_bool, method_text, _sid, c1_value = raw_meta[i]
            paid_item = self.left_table.item(i, 3)
            if paid_item:
                paid_item.setBackground(self._color_paid if paid_bool else self._color_not_paid)
            method_item = self.left_table.item(i, 4)
            if method_item:
                is_cash = str(method_text).lower() in ("нал", "наличный")
                method_item.setBackground(self._color_cash if is_cash else self._color_non_cash)

        self.left_table.hideColumn(6) # sale_id
        self.left_table.hideColumn(7) # C1
        self.left_table.resizeColumnsToContents()
        self._fill_right_table([], reset=True)
        self._rebuild_right_table_from_selection()

    def _rebuild_right_table_from_selection(self, *_args):
        selected_sale_ids = []
        for row, cb in self.left_checkboxes.items():
            if cb.isChecked():
                sid_item = self.left_table.item(row, 6)
                if sid_item:
                    try:
                        sid = int(sid_item.text())
                        selected_sale_ids.append(sid)
                    except ValueError:
                        continue

        agg = {}
        for sid in selected_sale_ids:
            items = get_sale_items(sid)  # (product_name, quantity, price)
            payment_method_text = ""
            for row in range(self.left_table.rowCount()):
                sid_item = self.left_table.item(row, 6)
                if sid_item and sid_item.text():
                    try:
                        if int(sid_item.text()) == sid:
                            payment_method_text = self.left_table.item(row, 4).text() if self.left_table.item(row, 4) else ""
                            break
                    except ValueError:
                        continue

            for prod_name, qty, _price in items:
                key = (prod_name, payment_method_text or "")
                try:
                    qty_val = float(qty)
                except Exception:
                    try:
                        qty_val = float(str(qty).replace(",", "."))
                    except Exception:
                        qty_val = 0.0
                agg[key] = agg.get(key, 0.0) + qty_val

        rows = []
        for (name, method), qty in sorted(agg.items(), key=lambda x: (x[0][0].lower(), x[0][1])):
            qty_str = f"{qty:.3f}".rstrip('0').rstrip('.') if qty % 1 != 0 else f"{int(qty)}"
            rows.append([name, qty_str, method])

        self._fill_right_table(rows, reset=True)

    def _fill_right_table(self, rows, reset=False):
        if reset:
            self.right_checkboxes.clear()

        headers = ["Вкл", "Название", "Кол-во", "Метод"]
        self.right_table.clear()
        self.right_table.setColumnCount(len(headers))
        self.right_table.setHorizontalHeaderLabels(headers)

        self.right_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self._insert_checkbox(self.right_table, i, 0, mapping=self.right_checkboxes, checked=False)
            for j, value in enumerate(row):
                self.right_table.setItem(i, j + 1, QTableWidgetItem(str(value)))
        self.right_table.resizeColumnsToContents()

    def export_right_table_to_excel(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить отчёт", "", "Excel Files (*.xlsx)")
        if not path:
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Агрегат"

        # Заголовки: только Название, Кол-во, Метод
        ws.append(["Название", "Кол-во", "Метод"])

        # Идём по строкам правой таблицы, экспортируем только отмеченные чекбоксы
        for r in range(self.right_table.rowCount()):
            cb_widget = self.right_table.cellWidget(r, 0)
            checked = False
            if cb_widget:
                cb = cb_widget.findChild(QCheckBox)
                if cb:
                    checked = cb.isChecked()
            if not checked:
                continue

            name_item = self.right_table.item(r, 1)
            qty_item = self.right_table.item(r, 2)
            method_item = self.right_table.item(r, 3)
            name = name_item.text() if name_item else ""
            qty = qty_item.text() if qty_item else ""
            method = method_item.text() if method_item else ""
            ws.append([name, qty, method])

        try:
            wb.save(path)
            QMessageBox.information(self, "Готово", f"Отчёт сохранён:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
