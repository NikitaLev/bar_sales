from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGridLayout, QTableWidget, QTableWidgetItem, QComboBox, QCheckBox,
    QMessageBox, QScrollArea, QTabWidget, QLineEdit
)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QSize
from models import get_categories, get_products_by_category, create_sale, get_last_sale_id
from db_init import clear_all_tables
from ui.product_editor import ProductEditor
from ui.ingredient_editor import IngredientEditor
from ui.supplier_editor import SupplierEditor
from ui.invoice_editor import InvoiceEditor
from ui.sale_editor import SaleEditor
from ui.category_editor import CategoryEditor
from ui.stock_manager import StockManager
from ui.report_viewer import ReportViewer
import shutil
import os
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from receipt_printer import print_receipt

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Бар: Продажа")
        self.setMinimumSize(1000, 700)
        self.sale_items = []

        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_sale_tab(), "Продажа")
        self.tabs.addTab(self.create_sales_tab(), "Счета")      
        self.tabs.addTab(self.create_admin_tab(), "Управление")
        self.tabs.addTab(self.create_report_tab(), "Отчёты")   
        self.tabs.currentChanged.connect(self.on_tab_changed) 

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    
    def create_sale_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.category_grid = QGridLayout()
        layout.addWidget(QLabel("Категории"))
        layout.addLayout(self.category_grid)
        self.load_categories()

        self.product_grid = QGridLayout()
        self.product_widget = QWidget()
        self.product_widget.setLayout(self.product_grid)
        self.product_scroll = QScrollArea()
        self.product_scroll.setWidgetResizable(True)
        self.product_scroll.setWidget(self.product_widget)
        layout.addWidget(QLabel("Напитки"))
        layout.addWidget(self.product_scroll)

        self.sale_table = QTableWidget()
        self.sale_table.setColumnCount(3)
        self.sale_table.setHorizontalHeaderLabels(["Название", "Цена", "Кол-во"])
        layout.addWidget(QLabel("Текущий счёт"))
        layout.addWidget(self.sale_table)

        self.guest_name_input = QLineEdit()
        self.guest_name_input.setPlaceholderText("Имя гостя (по умолчанию: Гость)")
        layout.addWidget(QLabel("Гость"))
        layout.addWidget(self.guest_name_input)

        payment_row = QHBoxLayout()
        self.payment_method = QComboBox()
        self.payment_method.addItems(["Нал", "Безнал"])
        self.paid_checkbox = QCheckBox("Оплачено")
        payment_row.addWidget(QLabel("Метод оплаты:"))
        payment_row.addWidget(self.payment_method)
        payment_row.addWidget(self.paid_checkbox)
        layout.addLayout(payment_row)

        action_row = QHBoxLayout()
        print_btn = QPushButton("Напечатать счёт")
        print_btn.clicked.connect(self.on_print)
        action_row.addWidget(print_btn)

        finish_btn = QPushButton("Завершить продажу")
        finish_btn.clicked.connect(self.finish_sale)
        action_row.addWidget(finish_btn)

        layout.addLayout(action_row)
        tab.setLayout(layout)
        return tab
    
    def create_report_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.report_viewer = ReportViewer()
        layout.addWidget(self.report_viewer)

        tab.setLayout(layout)
        return tab


    def create_admin_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        admin_buttons = [
            ("Категории", self.open_category_editor),
            ("Напитки", self.open_product_editor),
            ("Ингредиенты", self.open_ingredient_editor),
            ("Поставщики", self.open_supplier_editor),
            ("Накладные", self.open_invoice_editor),
            ("Склад", self.open_stock_manager),
            ("Очистить базу", self.confirm_clear),
            ("Резервная копия", self.backup_database),
            ("Восстановить", self.restore_database)


        ]

        btn_row = QHBoxLayout()
        for label, handler in admin_buttons:
            btn = QPushButton(label)
            btn.clicked.connect(handler)
            btn_row.addWidget(btn)

        layout.addLayout(btn_row)
        tab.setLayout(layout)
        return tab

    def create_sales_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.sale_editor = SaleEditor()
        layout.addWidget(self.sale_editor)

        tab.setLayout(layout)
        return tab

    def load_categories(self):
        categories = get_categories()
        for i, (cid, name) in enumerate(categories):
            btn = QPushButton(name)
            btn.setFixedSize(120, 40)
            btn.clicked.connect(lambda _, c=cid: self.load_products(c))
            self.category_grid.addWidget(btn, i // 4, i % 4)

    def load_products(self, category_id):
        for i in reversed(range(self.product_grid.count())):
            widget = self.product_grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        products = get_products_by_category(category_id)
        for i, (pid, name, price, image_path) in enumerate(products):
            btn = QPushButton()
            btn.setFixedSize(150, 120)
            btn.setText(f"{name}\n{price:.2f} BYN")
            if image_path:
                pixmap = QPixmap(image_path).scaled(64, 64)
                icon = QIcon(pixmap)
                btn.setIcon(icon)
                btn.setIconSize(QSize(64, 64))
            btn.clicked.connect(lambda _, p=(pid, name, price): self.add_to_sale(p))
            self.product_grid.addWidget(btn, i // 4, i % 4)

    def add_to_sale(self, product):
        pid, name, price = product
        for i, item in enumerate(self.sale_items):
            if item[0] == pid:
                self.sale_items[i] = (pid, name, price, item[3] + 1)
                self.refresh_sale_table()
                return
        self.sale_items.append((pid, name, price, 1))
        self.refresh_sale_table()

    def refresh_sale_table(self):
        self.sale_table.setRowCount(len(self.sale_items))
        for i, (_, name, price, qty) in enumerate(self.sale_items):
            self.sale_table.setItem(i, 0, QTableWidgetItem(name))
            self.sale_table.setItem(i, 1, QTableWidgetItem(f"{price:.2f}"))
            self.sale_table.setItem(i, 2, QTableWidgetItem(str(qty)))

    def finish_sale(self):
        if not self.sale_items:
            QMessageBox.warning(self, "Ошибка", "Счёт пуст.")
            return
        paid = self.paid_checkbox.isChecked()
        method = self.payment_method.currentText()
        guest_name = self.guest_name_input.text().strip() or "Гость"
        items_for_db = [(pid, price, qty) for pid, _, price, qty in self.sale_items]
        try:
            create_sale(items_for_db, paid, method, guest_name)
            QMessageBox.information(self, "Готово", "Продажа завершена.")
            self.sale_items = []
            self.refresh_sale_table()
            self.guest_name_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def on_print(self):
        # 1) собираем данные из текущей продажи
        items = []
        for row in range(self.sale_table.rowCount()):
            name = self.sale_table.item(row, 0).text()
            price = float(self.sale_table.item(row, 1).text())
            qty   = float(self.sale_table.item(row, 2).text())
            items.append((name, qty, price))

        guest  = self.guest_name_input.text().strip() or "Гость"
        paid   = bool(self.paid_checkbox.isChecked())
        method = self.payment_method.currentText()

        sale_id = get_last_sale_id() + 1
        print_receipt(self, sale_id, guest, paid, method, items)

    def open_product_editor(self):
        self.editor = ProductEditor()
        self.editor.show()

    def open_ingredient_editor(self):
        self.editor = IngredientEditor()
        self.editor.show()

    def open_supplier_editor(self):
        self.editor = SupplierEditor()
        self.editor.show()

    def open_invoice_editor(self):
        self.editor = InvoiceEditor()
        self.editor.show()

    def open_sale_editor(self):
        self.editor = SaleEditor()
        self.editor.show()

    def open_category_editor(self):
        self.editor = CategoryEditor()
        self.editor.show()

    def open_stock_manager(self):
        self.editor = StockManager()
        self.editor.show()

    def confirm_clear(self):
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить все данные из базы?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            clear_all_tables()
            QMessageBox.information(self, "Готово", "База данных очищена.")

    def on_tab_changed(self, index):  # ✅ автообновление вкладок
        tab_text = self.tabs.tabText(index)

        if tab_text == "Счета":
            if hasattr(self, "sale_editor"):
                self.sale_editor.load_sales()

        elif tab_text == "Продажа":
            self.refresh_sale_table()
            self.load_categories()
        elif tab_text == "Отчёты":
            if hasattr(self, "report_viewer"):
                self.report_viewer.generate_report()    

    def backup_database(self):
        path, _ = QFileDialog.getSaveFileName(
        self,
        "Сохранить резервную копию",
        "backup_bar_sales.db",
        "SQLite Database (*.db)"
        )
        if not path:
            return

        try:
            shutil.copy("bar_sales.db", path)
            QMessageBox.information(self, "Готово", f"Резервная копия сохранена:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить:\n{str(e)}")

    def restore_database(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выбрать резервную копию",
            "",
            "SQLite Database (*.db)"
        )
        if not path:
            return

        try:
         shutil.copy(path, "bar_sales.db")
         QMessageBox.information(
                self,
             "Готово",
             "База данных успешно восстановлена.\nПерезапустите приложение для применения изменений."
            )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось восстановить:\n{str(e)}")
