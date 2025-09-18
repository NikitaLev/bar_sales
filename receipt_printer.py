from PyQt5.QtPrintSupport import QPrinter, QPrinterInfo
from PyQt5.QtGui import QTextDocument, QPainter
from PyQt5.QtCore import QSizeF
from PyQt5.QtWidgets import QMessageBox
import datetime, os

def print_receipt(self, sale_id, guest, paid, method, items):
    paid_status = "Оплачено" if paid else "Не оплачено"
    total_sum = sum(qty * price for name, qty, price in items)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{
          font-family: sans-serif;
          font-size: 10pt;
          margin: 0;
          padding: 0;
        }}
        h4 {{
          text-align: center;
          margin: 4px 0;
          font-size: 12pt;
        }}
        table {{
          width: 100%;
          border-collapse: collapse;
        }}
        th, td {{
          padding: 2px;
          border-bottom: 1px dashed #444;
        }}
        th {{
          font-weight: normal;
          text-align: left;
        }}
        td {{
          font-weight: bold;
        }}
        .right {{
          text-align: right;
        }}
        .center {{
          text-align: center;
        }}
      </style>
    </head>
    <body>
      <h4>БАР «КОММУНА»</h4>
      <h4>Счёт №{sale_id}</h4>
      <p>
        Дата: {now}<br>
        Гость: {guest}<br>
        Статус: {paid_status}, {method}
      </p>
      <table>
        <tr>
          <th>Товар</th>
          <th class="center">Кол-во</th>
          <th class="right">Цена</th>
          <th class="right">Сумма</th>
        </tr>
    """

    for name, qty, price in items:
        line_sum = qty * price
        html += f"""
        <tr>
          <td>{name}</td>
          <td class="center">{qty:.3f}</td>
          <td class="right">{price:.2f}</td>
          <td class="right">{line_sum:.2f}</td>
        </tr>
        """

    html += f"""
      </table>
      <h4 class="right">Итого: {total_sum:.2f} BYN</h4>
      <p style="font-size:8pt; color:#555;">
        Документ не является платёжным документом
      </p>
      <p class="center" style="margin-top:10px;">
        Спасибо за покупку!
      </p>
    </body>
    </html>
    """

    # Сохраняем HTML
    filename = f"cheque_{sale_id}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    # Настройка принтера
    desired_name = "G80(1)"
    printers = QPrinterInfo.availablePrinters()
    printer_info = next((p for p in printers if p.printerName() == desired_name), None)
    if not printer_info:
        printer_info = QPrinterInfo.defaultPrinter()

    printer = QPrinter(printer_info)
    printer.setPageSize(QPrinter.Custom)
    printer.setPageMargins(0, 0, 0, 0, QPrinter.Millimeter)
    printer.setOrientation(QPrinter.Portrait)

    # Создаём QTextDocument
    doc = QTextDocument()
    doc.setHtml(html)
    doc.setTextWidth(printer.pageRect().width())  # важно!

    # Печатаем через QPainter — без масштабирования
    painter = QPainter(printer)
    doc.drawContents(painter)
    painter.end()
