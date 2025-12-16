from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGridLayout, QTableWidget, QTableWidgetItem, QComboBox, QCheckBox,
    QMessageBox, QScrollArea, QTabWidget, QLineEdit, QHeaderView

)

from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtCore import QSize, Qt
from models import get_categories, get_products_by_category, create_sale, get_last_sale_id
from db_init import clear_all_tables
from ui.product_editor import ProductEditor
from ui.ingredient_editor import IngredientEditor
from ui.report_viewer1C import Report1CViewer
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
from functools import partial

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        font = QFont()
        font.setPointSize(10)
        self.setFont(font)

        self.setWindowTitle("Бар: Продажа")
        self.setMinimumSize(1000, 700)
        self.sale_items = []

        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_sale_tab(), "Продажа")
        self.tabs.addTab(self.create_sales_tab(), "Счета")      
        self.tabs.addTab(self.create_admin_tab(), "Управление")
        self.tabs.addTab(self.create_report_tab(), "Отчёты")   
        self.tabs.addTab(self.create_report1C_tab(), "Отчёт 1С")   
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
        self.sale_table.setColumnCount(4)
        self.sale_table.setHorizontalHeaderLabels(
            ["Название", "Цена", "Кол-во", ""]
        )
        self.sale_table.setMaximumSize(2000, 200)
        self.sale_table.setColumnWidth(0, 300)
        # чтобы колонка с кнопками не растягивалась
        self.sale_table.horizontalHeader().setSectionResizeMode(3, 
            QHeaderView.ResizeToContents
        )

        layout.addWidget(QLabel("Текущий счёт"))
        layout.addWidget(self.sale_table)

        self.guest_name_input = QLineEdit()
        self.guest_name_input.setPlaceholderText("Имя гостя (по умолчанию: Гость)")

        payment_row = QHBoxLayout()
        self.payment_method = QComboBox()
        self.payment_method.addItems(["Нал", "Безнал"])

        self.paid_checkbox = QCheckBox("Оплачено")
        self.C1_checkbox = QCheckBox("Ч")
        self.C1_checkbox.setChecked(True)

        paid_container = QWidget()
        paid_vbox = QVBoxLayout(paid_container)
        paid_vbox.setContentsMargins(0, 0, 0, 0)
        paid_vbox.setSpacing(4)
        paid_vbox.addWidget(self.paid_checkbox)
        paid_vbox.addWidget(self.C1_checkbox)
        paid_vbox.addWidget(self.C1_checkbox)
        paid_vbox.setAlignment(self.paid_checkbox, Qt.AlignTop)

        payment_row.addWidget(QLabel("Гость"))
        payment_row.addWidget(self.guest_name_input)

        self.open_checkbox = QCheckBox("Открытый чек")
        self.open_checkbox.setChecked(False)  # по умолчанию выключен
        payment_row.addWidget(self.open_checkbox)

        payment_row.addWidget(QLabel("Метод оплаты:"))
        payment_row.addWidget(self.payment_method)

        payment_row.addWidget(paid_container)


        # Итоговая сумма по товарам
        total_row = QHBoxLayout()
        total_row.addStretch()  # отодвигаем лейбл вправо

        self.total_label = QLabel("Итого: 0.00 BYN")
        # делаем крупным и жирным, как на кассе
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self.total_label.setFont(font)
        # подсветка (фон и паддинги)
        self.total_label.setStyleSheet("""
            background-color: #f0f0f0;
            padding: 6px 12px;
            border-radius: 4px;
        """)
        self.total_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        payment_row.addWidget(self.total_label)
        layout.addLayout(payment_row)

        action_row = QHBoxLayout()
        clear_btn = QPushButton("Очистить счёт")
        clear_btn.setFixedHeight(40)  # высота в пикселях
        clear_btn.clicked.connect(self.clear_sale)
        action_row.addWidget(clear_btn)

        finish_btn = QPushButton("Завершить продажу")
        finish_btn.setFixedHeight(40)
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
    
    def create_report1C_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.report_viewer = Report1CViewer()
        layout.addWidget(self.report_viewer)

        tab.setLayout(layout)
        return tab

    def update_total(self):
        total = 0.0
        for row in range(self.sale_table.rowCount()):
            price_item = self.sale_table.item(row, 1)
            qty_item   = self.sale_table.item(row, 2)
            if price_item and qty_item:
                try:
                    price = float(price_item.text())
                    qty   = float(qty_item.text())
                    total += price * qty
                except ValueError:
                    pass
        self.total_label.setText(f"Итого: {total:.2f} BYN")

    def clear_sale(self):
        self.sale_table.setRowCount(0)
        self.sale_items.clear() 

        self.guest_name_input.clear()

        self.payment_method.setCurrentIndex(0)
        self.paid_checkbox.setChecked(False)
        self.C1_checkbox.setChecked(True)

        self.update_total() 

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

            # 🖋️ Устанавливаем текст
            btn.setText(f"{name}\n{price:.2f} BYN")

            # 🔠 Настройка шрифта: размер 16, жирный
            font = QFont()
            font.setPointSize(14)
            font.setBold(True)
            btn.setFont(font)

            # 🎨 Стиль: перенос по словам и выравнивание по центру
            btn.setStyleSheet("""
                QPushButton {
                    qproperty-wordWrap: true;
                    text-align: center;
                    padding: 5px;
                }
            """)

            # 🖼️ Иконка, если есть изображение
            if image_path:
                pixmap = QPixmap(image_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon = QIcon(pixmap)
                btn.setIcon(icon)
                btn.setIconSize(QSize(64, 64))

            btn.clicked.connect(lambda _, p=(pid, name, price): self.add_to_sale(p))
            self.product_grid.addWidget(btn, i // 9, i % 9)

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

            # Контейнер для кнопки
            cell_widget = QWidget()
            cell_layout = QHBoxLayout(cell_widget)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            cell_layout.setSpacing(0)
            cell_layout.setAlignment(Qt.AlignCenter)

            # Кнопка «Удалить»
            btn = QPushButton("Удалить")
            btn.setFixedSize(80, 24)
            btn.setFlat(True)
            btn.setStyleSheet("""
                color: #c0392b;
                font-size: 14px;
                background: transparent;
            """)    
            btn.clicked.connect(partial(self.remove_from_sale, i))
            self.sale_table.setCellWidget(i, 3, btn)

        self.update_total()

    def remove_from_sale(self, row_index):
        pid, name, price, qty = self.sale_items[row_index]

        if qty > 1:
            self.sale_items[row_index] = (pid, name, price, qty - 1)
        else:
            # удаляем всю позицию
            self.sale_items.pop(row_index)

        self.refresh_sale_table()

    def finish_sale(self):
        if not self.sale_items:
            QMessageBox.warning(self, "Ошибка", "Счёт пуст.")
            return
        
        paid = self.paid_checkbox.isChecked()
        c1 = self.C1_checkbox.isChecked()
        method = self.payment_method.currentText()
        guest_name = self.guest_name_input.text().strip() or "Гость"

        # определяем статус
        status = "open" if self.open_checkbox.isChecked() else "closed"

        items_for_db = [(pid, price, qty) for pid, _, price, qty in self.sale_items]

        try:
            create_sale(items_for_db, paid, method, guest_name, c1, status)
            self.on_print()
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
