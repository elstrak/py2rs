import re

class Token:
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, {self.line}, {self.column})"

class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.current_char = self.text[self.pos] if self.text else None
        self.indent_stack = [0]  # Стек для отслеживания уровней отступов
        self.tokens = []  # Буфер для хранения токенов
        self.single_char_tokens = {
            '==': 'EQUALS_EQUALS',
            '!=': 'NOT_EQUALS',
            '<=': 'LESS_THAN_OR_EQUAL_TO',
            '>=': 'GREATER_THAN_OR_EQUAL_TO',
            '=': 'EQUALS',
            '<': 'LESS_THAN',
            '>': 'GREATER_THAN',
            '+': 'PLUS',
            '-': 'MINUS',
            '*': 'TIMES',
            '/': 'DIVIDE',
            '%': 'MODULO',
            '&': 'BITWISE_AND',
            '|': 'BITWISE_OR',
            '^': 'BITWISE_XOR',
            '~': 'BITWISE_NOT',
            '@': 'AT',
            '(': 'LPAREN',
            ')': 'RPAREN',
            '{': 'LBRACE',
            '}': 'RBRACE',
            '[': 'LBRACKET',
            ']': 'RBRACKET',
            ',': 'COMMA',
            '.': 'DOT',
            ':': 'COLON',
            ';': 'SEMICOLON',
            # Добавьте другие операторы по необходимости
        }

    def advance(self):
        if self.current_char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        
        self.pos += 1
        if self.pos < len(self.text):
            self.current_char = self.text[self.pos]
        else:
            self.current_char = None

    def process_indent(self, indent_size):
        current_indent = self.indent_stack[-1]
        
        if indent_size > current_indent:
            # Увеличение отступа
            self.indent_stack.append(indent_size)
            return Token('INDENT', None, self.line, self.column)
        
        tokens = []
        while indent_size < current_indent:
            # Уменьшение отступа
            self.indent_stack.pop()
            tokens.append(Token('DEDENT', None, self.line, self.column))
            if self.indent_stack:  # Проверяем, не пустой ли стек
                current_indent = self.indent_stack[-1]
            else:
                self.indent_stack = [0]  # Сброс к начальному состоянию
                break
        
        if indent_size != self.indent_stack[-1]:
            raise Exception(f"Неправильный отступ в строке {self.line}")
        
        return tokens if tokens else None

    def skip_whitespace(self):
        result = None
        if self.current_char == '\n':
            self.advance()
            # Подсчитываем отступ после новой строки
            indent_size = 0
            while self.current_char is not None and self.current_char in ' \t':
                if self.current_char == ' ':
                    indent_size += 1
                else:  # self.current_char == '\t'
                    indent_size += 4  # Считаем tab как 4 пробела
                self.advance()
            
            if self.current_char is not None and self.current_char != '\n':
                result = self.process_indent(indent_size)
        else:
            while self.current_char is not None and self.current_char.isspace():
                self.advance()
        return result

    def skip_comment(self):
        if self.current_char == '#':
            while self.current_char != '\n' and self.current_char is not None:
                self.advance()
        elif self.current_char == '/' and self.peek() == '*':
            self.advance()
            self.advance()
            while not (self.current_char == '*' and self.peek() == '/'):
                self.advance()
                if self.current_char is None:
                    raise Exception("Незакрытый многострочный комментарий")
            self.advance()
            self.advance()

    def single_char_token(self, char=None, column=None):
        if char is None:
            char = self.current_char
            column = self.column
            self.advance()
        token_type = self.single_char_tokens.get(char)
        if token_type:
            return Token(token_type, char, self.line, column)
        elif char == '&':
            return Token('BITWISE_AND', '&', self.line, column)
        elif char == '|':
            return Token('BITWISE_OR', '|', self.line, column)
        elif char == '^':
            return Token('BITWISE_XOR', '^', self.line, column)
        elif char == '~':
            return Token('BITWISE_NOT', '~', self.line, column)
        elif char == '@':
            return Token('AT', '@', self.line, column)
        elif char == '[':
            self.advance()
            return Token('LBRACKET', '[', self.line, column)
        elif char == ']':
            self.advance()
            return Token('RBRACKET', ']', self.line, column)
        else:
            raise Exception(f'Неизвестный символ: {char} на строке {self.line}, столбце {column}')

    def peek(self, n=1):
        peek_pos = self.pos + n
        if peek_pos < len(self.text):
            return self.text[peek_pos]
        return None

    def compound_token(self):
        column = self.column
        char = self.current_char
        self.advance()
        if self.current_char == '=':
            compound = char + self.current_char
            self.advance()
            compound_tokens = {
                '+=': 'PLUS_EQUALS',
                '-=': 'MINUS_EQUALS',
                '*=': 'TIMES_EQUALS',
                '/=': 'DIVIDE_EQUALS',
                '%=': 'MOD_EQUALS',
                '&=': 'AND_EQUALS',
                '|=': 'OR_EQUALS',
                '^=': 'XOR_EQUALS',
            }
            token_type = compound_tokens.get(compound)
            if token_type:
                return Token(token_type, compound, self.line, column)
        # Handle other compound tokens
        if char == '/' and self.current_char == '/':
            self.advance()
            return Token('FLOOR_DIVIDE', '//', self.line, column)
        elif char == '*' and self.current_char == '*':
            self.advance()
            return Token('POWER', '**', self.line, column)
        elif char == '<' and self.current_char == '<':
            self.advance()
            return Token('LEFT_SHIFT', '<<', self.line, column)
        elif char == '>' and self.current_char == '>':
            self.advance()
            return Token('RIGHT_SHIFT', '>>', self.line, column)
        else:
            return self.single_char_token(char, column)

    def identifier(self):
        result = ''
        column = self.column
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        
        token_type = 'IDENTIFIER'
        keywords = [
            'def', 'if', 'else', 'return', 'for', 'while', 'print', 'input',
            'True', 'False', 'None', 'and', 'or', 'not', 'in', 'import',
            'class', 'try', 'except', 'finally', 'async', 'await', 'lambda'
        ]
        if result in keywords:
            token_type = result.upper()
        
        return Token(token_type, result, self.line, column)

    def number(self):
        result = ''
        column = self.column
        
        # Проверяем, является ли число шестнадцатеричным, восьмеричным или двоичным
        if self.current_char == '0':
            result += self.current_char
            self.advance()
            if self.current_char in ['x', 'X']:
                result += self.current_char
                self.advance()
                while self.current_char is not None and (self.current_char in '0123456789abcdefABCDEF' or self.current_char == '_'):
                    if self.current_char != '_':
                        result += self.current_char
                    self.advance()
                return Token('NUMBER', int(result, 16), self.line, column)
            elif self.current_char in ['b', 'B']:
                result += self.current_char
                self.advance()
                while self.current_char in '01_':
                    if self.current_char != '_':
                        result += self.current_char
                    self.advance()
                return Token('NUMBER', int(result, 2), self.line, column)
            elif self.current_char in '01234567':
                while self.current_char in '01234567_':
                    if self.current_char != '_':
                        result += self.current_char
                    self.advance()
                return Token('NUMBER', int(result, 8), self.line, column)
        
        # Обычное десятичное число (целое или с плавающей точкой)
        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == '_'):
            if self.current_char != '_':
                result += self.current_char
            self.advance()
        
        if self.current_char == '.':
            result += self.current_char
            self.advance()
            while self.current_char is not None and (self.current_char.isdigit() or self.current_char == '_'):
                if self.current_char != '_':
                    result += self.current_char
                self.advance()
            return Token('NUMBER', float(result), self.line, column)
        else:
            return Token('NUMBER', int(result), self.line, column)

    def string(self):
        quote_char = self.current_char
        self.advance()  # Пропустить начальную кавычку
        result = ''
        while self.current_char != quote_char:
            if self.current_char is None:
                raise Exception("Незакрытая строка")
            if self.current_char == '\\':
                self.advance()
                if self.current_char in ['n', 't', '\\', quote_char]:
                    escape_dict = {
                        'n': '\n',
                        't': '\t',
                        '\\': '\\',
                        quote_char: quote_char
                    }
                    result += escape_dict.get(self.current_char, self.current_char)
                else:
                    result += self.current_char
            else:
                result += self.current_char
            self.advance()
        self.advance()  # Пропустить закрывающую кавычку
        return Token('STRING', result, self.line, self.column)

    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char.isspace():
                indent_tokens = self.skip_whitespace()
                if indent_tokens:
                    return indent_tokens
                continue

            if self.current_char == '#' or (self.current_char == '/' and self.peek() == '*'):
                self.skip_comment()
                continue

            if self.current_char.isalpha() or self.current_char == '_':
                return self.identifier()

            if self.current_char.isdigit():
                return self.number()

            if self.current_char in ['"', "'"]:
                return self.string()
            
            if self.current_char in ['+', '-', '*', '/', '%', '&', '|', '^', '<', '>']:
                return self.compound_token()

            # Single character tokens
            return self.single_char_token()

        return Token('EOF', None, self.line, self.column)

    def tokenize(self):
        tokens = []
        self.indent_stack = [0]  # Инициализируем стек отступов
        
        while self.current_char is not None:
            if self.current_char.isspace():
                indent_token = self.skip_whitespace()
                if indent_token:
                    if isinstance(indent_token, list):
                        tokens.extend(indent_token)
                    else:
                        tokens.append(indent_token)
                continue
            
            if self.current_char == '#':
                self.skip_comment()
                continue
            
            if self.current_char.isdigit():
                tokens.append(self.number())
                continue
            
            if self.current_char.isalpha() or self.current_char == '_':
                tokens.append(self.identifier())
                continue
            
            if self.current_char in ['"', "'"]:
                tokens.append(self.string())
                continue
            
            # Обработка операторов и других символов
            two_char = self.current_char + (self.peek() or '')
            if two_char in self.single_char_tokens:
                tokens.append(Token(self.single_char_tokens[two_char], two_char, self.line, self.column))
                self.advance()
                self.advance()
                continue
            
            if self.current_char in self.single_char_tokens:
                tokens.append(Token(self.single_char_tokens[self.current_char], self.current_char, self.line, self.column))
                self.advance()
                continue
            
            raise Exception(f'Неизвестный символ: {self.current_char} на строке {self.line}, столбце {self.column}')
        
        # Добавляем DEDENT токены в конце файла
        while len(self.indent_stack) > 1:
            tokens.append(Token('DEDENT', None, self.line, self.column))
            self.indent_stack.pop()
        
        tokens.append(Token('EOF', None, self.line, self.column))
        return tokens

# Тестовый код (lexer.py)

if __name__ == "__main__":
    text = '''
def example(x):
    # This is a single-line comment
    if x > 0:
        return x * 2
    else:
        return x + 1
/* This is a
   multi-line
   comment */
print("Result:", example(5))
multiline = """This is a
multiline
string"""
raw_string = r"This is a raw string with \\n"
formatted_string = f"The result is {example(10)}"
'''
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    for token in tokens:
        print(token)

