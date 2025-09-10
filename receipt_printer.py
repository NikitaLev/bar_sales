from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QTextDocument
import datetime, os
from PyQt5.QtWidgets import ( QMessageBox
)
from string import Template

def print_receipt(self, sale_id, guest, paid, method, items):
    paid_status = "Оплачено" if paid else "Не оплачено"
    total_sum = sum(qty * price for name, qty, price in items)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Шаблон HTML
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
      <meta charset="utf-8">
      <title>Чек #{sale_id}</title>
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
      <h3>Чек №{sale_id}</h3>
      <p>
        Адрес: Тот самый адрес<br>
        УНП: 123456789<br>
        Касса: 01<br>
        Дата: {now}<br>
        Гость: {guest}<br>
        Статус: {paid_status}, {method}
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

    # Сохраняем HTML-файл (опционально)
    filename = f"cheque_{sale_id}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    # Открываем системный диалог печати
    printer = QPrinter(QPrinter.HighResolution)
    dlg = QPrintDialog(printer, self)
    if dlg.exec_() == QPrintDialog.Accepted:
        doc = QTextDocument()
        doc.setHtml(html)
        doc.print_(printer)

    # Уведомляем о сохранении/печати
    QMessageBox.information(
        self,
        "Чек",
        f"Чек сохранён: {os.path.abspath(filename)}\n"
        "И/или отправлен на печать"
    )
