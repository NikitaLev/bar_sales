from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout
)
from db_init import get_connection
from ui.invoice_form import InvoiceForm

class InvoiceEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Приходные накладные")
        self.layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Поставщик", "Дата", "Позиций"])
        self.table.cellDoubleClicked.connect(self.edit_invoice)
        self.layout.addWidget(self.table)
        self.setMinimumSize(800, 600)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Добавить накладную")
        add_btn.clicked.connect(self.add_invoice)
        btn_row.addWidget(add_btn)

        self.layout.addLayout(btn_row)
        self.setLayout(self.layout)

        self.load_invoices()

    def load_invoices(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT invoices.id, suppliers.name, invoices.date,
            (SELECT COUNT(*) FROM invoice_items WHERE invoice_id = invoices.id)
            FROM invoices
            LEFT JOIN suppliers ON invoices.supplier_id = suppliers.id
            ORDER BY invoices.date DESC
        """)
        rows = cursor.fetchall()
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))
        conn.close()

    def add_invoice(self):
        dialog = InvoiceForm()
        dialog.exec_()
        self.load_invoices()

    def edit_invoice(self, row, column):
        invoice_id = int(self.table.item(row, 0).text())
        dialog = InvoiceForm(invoice_id=invoice_id)
        dialog.exec_()
        self.load_invoices()
