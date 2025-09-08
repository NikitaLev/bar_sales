from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHBoxLayout, QDateEdit, QFileDialog, QMessageBox
)
from PyQt5.QtCore import QDate
from models import (
    get_sales_by_period, get_profit_by_period,
    get_ingredient_usage, get_top_products,
    get_detailed_sales, get_products, calculate_margin
)
from datetime import timedelta
from openpyxl import Workbook

class ReportViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Отчёты и аналитика")
        self.layout = QVBoxLayout()

        self.report_type = QComboBox()
        self.report_type.addItems([
            "Продажи", "Прибыль", "Списание ингредиентов",
            "Рентабельность", "Популярность", "Прибыльность", "Полный отчёт по продажам", "Отчёт по наценке"
        ])
        self.layout.addWidget(QLabel("Тип отчёта"))
        self.layout.addWidget(self.report_type)

        self.period_selector = QComboBox()
        self.period_selector.addItems(["Сегодня", "Неделя", "Месяц", "Выбрать вручную"])
        self.period_selector.currentIndexChanged.connect(self.toggle_manual_dates)
        self.layout.addWidget(QLabel("Период"))
        self.layout.addWidget(self.period_selector)

        date_row = QHBoxLayout()
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        date_row.addWidget(QLabel("С:"))
        date_row.addWidget(self.start_date)
        date_row.addWidget(QLabel("По:"))
        date_row.addWidget(self.end_date)
        self.layout.addLayout(date_row)

        self.generate_btn = QPushButton("Сформировать отчёт")
        self.generate_btn.clicked.connect(self.generate_report)
        self.layout.addWidget(self.generate_btn)

        self.table = QTableWidget()
        self.layout.addWidget(self.table)

        self.export_btn = QPushButton("Сохранить в Excel")
        self.export_btn.clicked.connect(self.export_to_excel)
        self.layout.addWidget(self.export_btn)

        self.setLayout(self.layout)
        self.toggle_manual_dates()

    def toggle_manual_dates(self):
        manual = self.period_selector.currentText() == "Выбрать вручную"
        self.start_date.setVisible(manual)
        self.end_date.setVisible(manual)

    def get_period(self):
        today = QDate.currentDate().toPyDate()
        option = self.period_selector.currentText()

        if option == "Сегодня":
            start = today
            end = today
        elif option == "Неделя":
            start = today - timedelta(days=7)
            end = today
        elif option == "Месяц":
            start = today - timedelta(days=30)
            end = today
        else:
            start = self.start_date.date().toPyDate()
            end = self.end_date.date().toPyDate()

        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

    def generate_report(self):
        report = self.report_type.currentText()
        start, end = self.get_period()

        if report == "Продажи":
            data = get_sales_by_period(start, end)
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["Дата", "Сумма", "Оплачено", "Метод", "Гость"])
            self.table.setRowCount(len(data))
            for i, (date, total, paid, method, guest) in enumerate(data):
                self.table.setItem(i, 0, QTableWidgetItem(date))
                self.table.setItem(i, 1, QTableWidgetItem(f"{total:.2f} BYN"))
                self.table.setItem(i, 2, QTableWidgetItem("Да" if paid else "Нет"))
                self.table.setItem(i, 3, QTableWidgetItem(method))
                self.table.setItem(i, 4, QTableWidgetItem(guest))

        elif report == "Прибыль":
            profit = get_profit_by_period(start, end)
            self.table.setColumnCount(1)
            self.table.setHorizontalHeaderLabels(["Прибыль"])
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem(f"{profit:.2f} BYN"))

        elif report == "Списание ингредиентов":
            usage = get_ingredient_usage(start, end)
            self.table.setColumnCount(3)
            self.table.setHorizontalHeaderLabels(["Ингредиент", "Кол-во", "Ед."])
            self.table.setRowCount(len(usage))
            for i, (name, qty, unit) in enumerate(usage):
                self.table.setItem(i, 0, QTableWidgetItem(name))
                self.table.setItem(i, 1, QTableWidgetItem(f"{qty:.2f}"))
                self.table.setItem(i, 2, QTableWidgetItem(unit))

        elif report in ["Популярность", "Прибыльность"]:
            by = "profit" if report == "Прибыльность" else "count"
            top = get_top_products(start, end, by=by)
            self.table.setColumnCount(2)
            self.table.setHorizontalHeaderLabels(["Напиток", "Значение"])
            self.table.setRowCount(len(top))
            for i, (name, value) in enumerate(top):
                val = f"{value:.2f} BYN" if by == "profit" else str(value)
                self.table.setItem(i, 0, QTableWidgetItem(name))
                self.table.setItem(i, 1, QTableWidgetItem(val))

        elif report == "Рентабельность":
            self.table.setColumnCount(2)
            self.table.setHorizontalHeaderLabels(["Напиток", "Рентабельность"])
            products = get_products()
            self.table.setRowCount(len(products))
            for i, (pid, name, price, _) in enumerate(products):
                margin = calculate_margin(pid)
                self.table.setItem(i, 0, QTableWidgetItem(name))
                self.table.setItem(i, 1, QTableWidgetItem(f"{margin:.1f}%"))

        elif report == "Полный отчёт по продажам":
            data = get_detailed_sales(start, end)
            self.table.setColumnCount(8)
            self.table.setHorizontalHeaderLabels([
                "Дата", "Гость", "Напиток", "Кол-во", "Цена",
                "Ингредиент", "Списано", "Ед."
            ])

            rows = []
            for sale in data:
                for product in sale["products"]:
                    for ing in product["ingredients"]:
                        rows.append([
                            sale["date"],
                            sale["guest"],
                            product["name"],
                            str(product["qty"]),
                            f"{product['price']:.2f}",
                            ing["name"],
                            f"{ing['used']:.2f}",
                            ing["unit"]
                        ])

            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, value in enumerate(row):
                    self.table.setItem(i, j, QTableWidgetItem(value))
        elif report == "Отчёт по наценке":
            import sys
            import os
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
            from models import get_margin_report

            data = get_margin_report()
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels(["Напиток", "Цена", "Себестоимость", "Наценка %"])
            self.table.setRowCount(len(data))
            for i, (name, price, cost, margin) in enumerate(data):
                    self.table.setItem(i, 0, QTableWidgetItem(name))
                    self.table.setItem(i, 1, QTableWidgetItem(f"{price:.2f} BYN"))
                    self.table.setItem(i, 2, QTableWidgetItem(f"{cost:.2f} BYN"))
                    self.table.setItem(i, 3, QTableWidgetItem(f"{margin:.1f}%"))


    def export_to_excel(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить отчёт", "", "Excel Files (*.xlsx)")
        if not path:
            return

        wb = Workbook()
        ws = wb.active
        ws.title = self.report_type.currentText()

        headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
        ws.append(headers)

        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            ws.append(row_data)

        try:
            wb.save(path)
            QMessageBox.information(self, "Готово", f"Отчёт сохранён:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
