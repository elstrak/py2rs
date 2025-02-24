import sys
import traceback
from lexer import Lexer
from parser import Parser
from code_generator import generate_code
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton
from PyQt6.QtGui import QFont

class TranslatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python to Rust Translator")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        editor_layout = QHBoxLayout()
        layout.addLayout(editor_layout)

        self.python_editor = QTextEdit()
        self.python_editor.setFont(QFont("Courier", 12))
        self.python_editor.setPlaceholderText("Enter Python code here")
        editor_layout.addWidget(self.python_editor)

        self.rust_editor = QTextEdit()
        self.rust_editor.setFont(QFont("Courier", 12))
        self.rust_editor.setPlaceholderText("Translated Rust code will appear here")
        self.rust_editor.setReadOnly(True)
        editor_layout.addWidget(self.rust_editor)

        translate_button = QPushButton("Translate")
        translate_button.clicked.connect(self.translate_code)
        layout.addWidget(translate_button)

        self.debug_console = QTextEdit()
        self.debug_console.setFont(QFont("Courier", 10))
        self.debug_console.setPlaceholderText("Debug information will appear here")
        self.debug_console.setReadOnly(True)
        layout.addWidget(self.debug_console)

    def translate_code(self):
        python_code = self.python_editor.toPlainText()
        try:
            lexer = Lexer(python_code)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            rust_code = generate_code(ast)
            self.rust_editor.setPlainText(rust_code)
            self.debug_console.setPlainText("Трансляция успешно завершена!")
        except Exception as e:
            error_message = f"Ошибка при трансляции: {str(e)}\n"
            error_message += f"Тип ошибки: {type(e).__name__}\n"
            error_message += f"Трассировка стека:\n{traceback.format_exc()}"
            self.debug_console.setPlainText(error_message)

def translate_python_to_rust(python_code):
    try:
        lexer = Lexer(python_code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        code_generator = CodeGenerator()
        rust_code = code_generator.generate(ast)
        return rust_code
    except Exception as e:
        raise Exception(f"Ошибка при трансляции: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = TranslatorWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
