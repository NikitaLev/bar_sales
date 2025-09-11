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
      <title>Счёт №{sale_id}</title>
      <style>
        body {{
          font-family: sans-serif;
          max-width: 300px;
        }}
        h4 {{
          text-align: center;
          margin: 0;
          font-weight: normal;
        }}
        table {{
          width: 100%;
          border-collapse: collapse;
          font-size: 14px;
        }}
        /* Заголовки таблицы — обычный вес */
        th {{
          padding: 4px;
          border-bottom: 1px dashed #444;
          text-align: left;
          font-weight: normal;
        }}
        /* Ячейки с данными — жирные */
        td {{
          padding: 4px;
          border-bottom: 1px dashed #444;
          font-weight: bold;
        }}
        /* Выравнивание колонок */
          .col-item       {{ text-align: left; }}
          .col-qty        {{ text-align: center; }}
          .col-unit-price {{ text-align: right; }}
          .col-price      {{ text-align: right; }}
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
          <th class="col-item">Товар</th>
          <th class="col-qty">Кол-во</th>
          <th class="col-unit-price">Цена/ед.</th>
          <th class="col-price">Сумма</th>
        </tr>
    """
    # Строки таблицы с товарами
    for name, qty, price in items:
        line_sum = qty * price
        html += (
            f"<tr>"
              f"<td class='col-item'>{name}</td>"
              f"<td class='col-qty'>{qty:.3f}</td>"
              f"<td class='col-unit-price'>{price:.2f}</td>"
              f"<td class='col-price'>{line_sum:.2f}</td>"
            f"</tr>"
        )

    # Вывод итоговой суммы
    html += f"""
      </table>
      <h3 class="right">Итого: {total_sum:.2f} BYN</h3>
        <p style="text-align:left; margin-top:0px; font-size:10px; color:#555;">
          Документ не является платёжным документом
        </p>
      <p style="text-align:center; margin-top:10px;">
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
