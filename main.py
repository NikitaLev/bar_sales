from PyQt5.QtWidgets import QApplication
from db_init import init_db  # Импорт из переименованного файла database.py
from ui.main_window import MainWindow  # Главное окно с плитками напитков
from ui.product_editor import ProductEditor

def main():
    init_db()

    # Запуск GUI-приложения
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
    editor = ProductEditor()
    editor.show()

if __name__ == "__main__":
    main()
