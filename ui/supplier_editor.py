from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QDialog, QLabel, QLineEdit, QMessageBox
)
from db_init import get_connection

class SupplierEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Поставщики")
        self.layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["ID", "Название"])
        self.table.cellDoubleClicked.connect(self.edit_supplier)
        self.table.setColumnWidth(1, 200)
        self.layout.addWidget(self.table)
        self.setMinimumSize(600, 400)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(self.add_supplier)
        btn_row.addWidget(add_btn)

        delete_btn = QPushButton("Удалить выбранного")
        delete_btn.clicked.connect(self.delete_supplier)
        btn_row.addWidget(delete_btn)

        self.layout.addLayout(btn_row)
        self.setLayout(self.layout)

        self.load_suppliers()

    def load_suppliers(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM suppliers")
        rows = cursor.fetchall()
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))
        conn.close()

    def add_supplier(self):
        dialog = SupplierForm()
        dialog.exec_()
        self.load_suppliers()

    def edit_supplier(self, row, column):
        supplier_id = int(self.table.item(row, 0).text())
        dialog = SupplierForm(supplier_id)
        dialog.exec_()
        self.load_suppliers()

    def delete_supplier(self):
        selected = self.table.currentRow()
        if selected < 0:
            return
        supplier_id = int(self.table.item(selected, 0).text())
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
        conn.commit()
        conn.close()
        self.load_suppliers()


class SupplierForm(QDialog):
    def __init__(self, supplier_id=None):
        super().__init__()
        self.setWindowTitle("Редактировать поставщика" if supplier_id else "Добавить поставщика")
        self.supplier_id = supplier_id
        self.layout = QVBoxLayout()

        self.name_input = QLineEdit()
        self.layout.addWidget(QLabel("Название"))
        self.layout.addWidget(self.name_input)

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save)
        self.layout.addWidget(save_btn)

        self.setLayout(self.layout)

        if supplier_id:
            self.load()

    def load(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM suppliers WHERE id = ?", (self.supplier_id,))
        name = cursor.fetchone()[0]
        self.name_input.setText(name)
        conn.close()

    def save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Название не может быть пустым")
            return

        conn = get_connection()
        cursor = conn.cursor()
        if self.supplier_id:
            cursor.execute("UPDATE suppliers SET name=? WHERE id=?", (name, self.supplier_id))
        else:
            cursor.execute("INSERT INTO suppliers (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        self.accept()
