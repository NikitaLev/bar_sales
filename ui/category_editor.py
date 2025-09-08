from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QDialog, QLabel, QLineEdit, QMessageBox
)
from db_init import get_connection

class CategoryEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Категории напитков")
        self.layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["ID", "Название"])
        self.table.cellDoubleClicked.connect(self.edit_category)
        self.layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Добавить категорию")
        add_btn.clicked.connect(self.add_category)
        btn_row.addWidget(add_btn)

        delete_btn = QPushButton("Удалить выбранную")
        delete_btn.clicked.connect(self.delete_category)
        btn_row.addWidget(delete_btn)

        self.layout.addLayout(btn_row)
        self.setLayout(self.layout)

        self.load_categories()

    def load_categories(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM categories")
        rows = cursor.fetchall()
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))
        conn.close()

    def add_category(self):
        dialog = CategoryForm()
        dialog.exec_()
        self.load_categories()

    def edit_category(self, row, column):
        cat_id = int(self.table.item(row, 0).text())
        dialog = CategoryForm(cat_id)
        dialog.exec_()
        self.load_categories()

    def delete_category(self):
        selected = self.table.currentRow()
        if selected < 0:
            return
        cat_id = int(self.table.item(selected, 0).text())
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
        conn.commit()
        conn.close()
        self.load_categories()


class CategoryForm(QDialog):
    def __init__(self, category_id=None):
        super().__init__()
        self.setWindowTitle("Редактировать категорию" if category_id else "Добавить категорию")
        self.category_id = category_id
        self.layout = QVBoxLayout()

        self.name_input = QLineEdit()
        self.layout.addWidget(QLabel("Название категории"))
        self.layout.addWidget(self.name_input)

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save)
        self.layout.addWidget(save_btn)

        self.setLayout(self.layout)

        if category_id:
            self.load()

    def load(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM categories WHERE id = ?", (self.category_id,))
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
        if self.category_id:
            cursor.execute("UPDATE categories SET name=? WHERE id=?", (name, self.category_id))
        else:
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        self.accept()
