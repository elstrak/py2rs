from ast_nodes import *

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens  # список токенов для разбора
        self.current_token = None  # текущий обрабатываемый токен
        self.token_index = -1  # индекс текущего токена
        self.advance()  # переход к первому токену

    def advance(self):
        self.token_index += 1
        if self.token_index < len(self.tokens):
            self.current_token = self.tokens[self.token_index]
        else:
            self.current_token = Token('EOF', None, self.tokens[-1].line, self.tokens[-1].column)

    def parse(self):
        # Начало разбора программы
        return self.program()

    def program(self):
        statements = []
        while self.current_token is not None and self.current_token.type != 'EOF':
            statements.append(self.statement())
        return Program(statements)

    def statement(self):
        if self.current_token.type == 'DEF':
            return self.function_definition()
        elif self.current_token.type == 'IF':
            return self.if_statement()
        elif self.current_token.type == 'WHILE':
            return self.while_statement()
        elif self.current_token.type == 'FOR':
            return self.for_statement()
        elif self.current_token.type == 'RETURN':
            return self.return_statement()
        elif self.current_token.type == 'TRY':
            return self.try_except_statement()
        elif self.current_token.type == 'IMPORT':
            return self.import_statement()
        elif self.current_token.type == 'CLASS':
            return self.class_definition()
        elif self.current_token.type == 'ASYNC':
            return self.async_function_definition()
        elif self.current_token.type == 'WITH':
            return self.with_statement()
        elif self.current_token.type == 'PRINT':
            return self.print_statement()
        elif self.current_token.type == 'IDENTIFIER':
            return self.assignment_or_expression()
        else:
            return self.expression_statement()

    def function_definition(self):
        decorators = self.decorator_list()
        self.eat('DEF')
        name = self.current_token.value
        self.eat('IDENTIFIER')
        self.eat('LPAREN')
        params = self.parameter_list()
        self.eat('RPAREN')
        self.eat('COLON')
        body = self.block()
        func_def = FunctionDef(name, params, body)
        if decorators:
            return DecoratedDef(decorators, func_def)
        return func_def

    def identifier(self):
        if self.current_token.type == 'IDENTIFIER':
            token = self.current_token
            self.eat('IDENTIFIER')
            return token.value
        self.error("Expected identifier")

    def parameter_list(self):
        params = []
        if self.current_token.type == 'IDENTIFIER':
            params.append(self.identifier())
            while self.current_token.type == 'COMMA':
                self.eat('COMMA')
                if self.current_token.type == 'IDENTIFIER':
                    params.append(self.identifier())
                else:
                    self.error("Expected identifier after comma in parameter list")
        return params

    def block(self):
        statements = []
        self.eat('INDENT')
        while self.current_token is not None and self.current_token.type not in ['DEDENT', 'EOF']:
            statements.append(self.statement())
        if self.current_token is not None and self.current_token.type == 'DEDENT':
            self.eat('DEDENT')
        return statements

    def if_statement(self):
        # Разбор условного оператора
        self.eat('IF')
        condition = self.expression()
        self.eat('COLON')
        true_body = self.block()
        false_body = None
        if self.current_token.type == 'ELSE':
            self.eat('ELSE')
            self.eat('COLON')
            false_body = self.block()
        
        # Проверяем, является ли условие "__name__ == "__main__""
        if isinstance(condition, BinaryOp):
            if (isinstance(condition.left, Identifier) and condition.left.name == '__name__' and
                isinstance(condition.right, String) and condition.right.value == '__main__'):
                # Это основной блок, возвращаем его как специальный тип
                return MainBlock(true_body)
        
        return IfStatement(condition, true_body, false_body)

    def return_statement(self):
        # Разбор оператора return
        self.eat('RETURN')
        expr = self.expression()
        return ReturnStatement(expr)
        

    def expression_statement(self):
        # Разбор выражения как отдльного оператора
        expr = self.expression()
        return expr

    def expression(self):
        if self.current_token.type == 'AWAIT':
            return self.await_expression()
        elif self.current_token.type == 'LPAREN' and self.peek_next_token().type == 'FOR':
            return self.generator_expression()
        elif self.current_token.type == 'LAMBDA':
            return self.lambda_expression()
        return self.logical_or()  # Убрали вызов assignment()

    def assignment(self):
        # Разбор операции присваивания
        left = self.logical_or()
        if self.current_token.type == 'EQUALS':
            self.eat('EQUALS')
            right = self.assignment()
            return Assignment(left, right)
        return left

    def logical_or(self):
        # Разбор логического ИЛИ
        node = self.logical_and()
        while self.current_token.type == 'OR':
            token = self.current_token
            self.eat('OR')
            node = BinaryOp(left=node, op=token.value, right=self.logical_and())
        return node

    def logical_and(self):
        # Разбор логического И
        node = self.equality()
        while self.current_token.type == 'AND':
            token = self.current_token
            self.eat('AND')
            node = BinaryOp(left=node, op=token.value, right=self.equality())
        return node

    def equality(self):
        # Разбор операций равенства и неравенства
        node = self.comparison()
        while self.current_token.type in ('EQUALS_EQUALS', 'NOT_EQUALS'):
            token = self.current_token
            self.eat(token.type)
            node = BinaryOp(left=node, op=token.value, right=self.comparison())
        return node

    def comparison(self):
        # Разбор операций сравнения
        node = self.term()
        while self.current_token.type in ('LESS_THAN', 'GREATER_THAN', 'LESS_THAN_OR_EQUAL_TO', 'GREATER_THAN_OR_EQUAL_TO'):
            token = self.current_token
            self.eat(token.type)
            node = BinaryOp(left=node, op=token.value, right=self.term())
        return node

    def term(self):
        # Разбор сложения и вычитания
        node = self.factor()
        while self.current_token.type in ('PLUS', 'MINUS'):
            token = self.current_token
            self.eat(token.type)
            node = BinaryOp(left=node, op=token.value, right=self.factor())
        return node

    def factor(self):
        # Разбор умножения и деления
        node = self.unary()
        while self.current_token.type in ('TIMES', 'DIVIDE'):
            token = self.current_token
            self.eat(token.type)
            node = BinaryOp(left=node, op=token.value, right=self.unary())
        return node

    def unary(self):
        # Разбор унарных операторов
        if self.current_token.type in ('PLUS', 'MINUS', 'NOT'):
            token = self.current_token
            self.eat(token.type)
            return UnaryOp(op=token.value, expr=self.unary())
        return self.primary()

    def primary(self):
        token = self.current_token
        if token.type == 'NUMBER':
            self.eat('NUMBER')
            return Num(token.value)
        elif token.type in ('STRING', 'RAW_STRING', 'FORMATTED_STRING'):
            self.eat(token.type)
            return String(token.value)
        elif token.type == 'IDENTIFIER':
            self.eat('IDENTIFIER')
            node = Identifier(token.value)
            while self.current_token.type == 'DOT':
                self.eat('DOT')
                method_name = self.current_token.value
                self.eat('IDENTIFIER')
                self.eat('LPAREN')
                args = []
                if self.current_token.type != 'RPAREN':
                    args = self.argument_list()
                self.eat('RPAREN')
                node = MethodCall(obj=node, method_name=method_name, args=args)
            # Обрабатываем вызовы функций только для простых идентификаторов
            if isinstance(node, Identifier) and self.current_token.type == 'LPAREN':
                return self.function_call(node.name)
            return node
        elif token.type == 'LPAREN':
            self.eat('LPAREN')
            node = self.expression()
            self.eat('RPAREN')
            return node
        elif token.type == 'LBRACKET':
            return self.list_expression()
        elif token.type == 'LBRACE':
            return self.dict_expression()
        self.error(f"Unexpected token: {token}")

    def function_call(self, name):
        # Разбор вызова функци
        self.eat('LPAREN')
        args = []
        if self.current_token.type != 'RPAREN':
            args = self.argument_list()
        self.eat('RPAREN')
        return FunctionCall(name, args)

    def argument_list(self):
        # Разбор списка аргументов функции
        args = [self.expression()]
        while self.current_token.type == 'COMMA':
            self.eat('COMMA')
            args.append(self.expression())
        return args

    def error(self, message):
        # Обработка ошибок парсера
        raise Exception(f"Parser error at line {self.current_token.line}, column {self.current_token.column}: {message}")

    def eat(self, token_type):
        # Проверка типа текущего токена и переход к следующему
        if self.current_token.type == token_type:
            self.advance()
        else:
            self.error(f"Expected {token_type}, but got {self.current_token.type}")

    def while_statement(self):
        # Разбор цикла while
        self.eat('WHILE')
        condition = self.expression()
        self.eat('COLON')
        body = self.block()
        return WhileStatement(condition, body)

    def for_statement(self):
        # Разбор цикла for
        self.eat('FOR')
        target = self.expression()
        self.eat('IN')
        iterable = self.expression()
        self.eat('COLON')
        body = self.block()
        return ForStatement(target, iterable, body)

    def list_expression(self):
        self.eat('LBRACKET')
        
        # Проверяем, является ли список пустым
        if self.current_token.type == 'RBRACKET':
            self.eat('RBRACKET')
            return ListNode(elements=[])
        
        # Иначе продолжаем разбор списка или спискового включения
        expr = self.expression()
        
        # Проверяем, является ли это списковым включением
        if self.current_token.type == 'FOR':
            self.eat('FOR')
            target = self.expression()
            self.eat('IN')
            iterable = self.expression()
            
            condition = None
            if self.current_token.type == 'IF':
                self.eat('IF')
                condition = self.expression()
            
            self.eat('RBRACKET')
            return ListComprehension(expression=expr, target=target, iterable=iterable, condition=condition)
        else:
            # Это обычный список с элементами
            elements = [expr]
            while self.current_token.type == 'COMMA':
                self.eat('COMMA')
                elements.append(self.expression())
            self.eat('RBRACKET')
            return ListNode(elements)

    def dict_expression(self):
        pairs = []
        self.eat('LBRACE')
        if self.current_token.type != 'RBRACE':
            key = self.expression()
            self.eat('COLON')
            value = self.expression()
            pairs.append((key, value))
            while self.current_token.type == 'COMMA':
                self.eat('COMMA')
                key = self.expression()
                self.eat('COLON')
                value = self.expression()
                pairs.append((key, value))
        self.eat('RBRACE')
        return DictNode(pairs)

    def try_except_statement(self):
        self.eat('TRY')
        self.eat('COLON')
        try_body = self.block()
        except_handlers = []
        else_body = None
        finally_body = None

        while self.current_token.type == 'EXCEPT':
            self.eat('EXCEPT')
            if self.current_token.type != 'COLON':
                exc_type = self.expression()
                if self.current_token.type == 'AS':
                    self.eat('AS')
                    exc_name = self.current_token.value
                    self.eat('IDENTIFIER')
                else:
                    exc_name = None
            else:
                exc_type = None
                exc_name = None
            self.eat('COLON')
            except_body = self.block()
            except_handlers.append(ExceptHandler(exc_type, exc_name, except_body))

        if self.current_token.type == 'ELSE':
            self.eat('ELSE')
            self.eat('COLON')
            else_body = self.block()

        if self.current_token.type == 'FINALLY':
            self.eat('FINALLY')
            self.eat('COLON')
            finally_body = self.block()

        return TryExcept(try_body, except_handlers, else_body, finally_body)

    def import_statement(self):
        self.eat('IMPORT')
        module_name = self.current_token.value
        self.eat('IDENTIFIER')
        alias = None
        if self.current_token.type == 'AS':
            self.eat('AS')
            alias = self.current_token.value
            self.eat('IDENTIFIER')
        return ImportStatement(module_name, alias)

    def class_definition(self):
        self.eat('CLASS')
        name = self.current_token.value
        self.eat('IDENTIFIER')
        
        base_class = None
        if self.current_token.type == 'LPAREN':
            self.eat('LPAREN')
            base_class = self.current_token.value
            self.eat('IDENTIFIER')
            self.eat('RPAREN')
        
        self.eat('COLON')
        body = self.block()
        return ClassDef(name, base_class, body)

    def method_definition(self):
        self.eat('DEF')
        name = self.current_token.value
        self.eat('IDENTIFIER')
        self.eat('LPAREN')
        params = self.parameter_list()
        self.eat('RPAREN')
        self.eat('COLON')
        body = self.block()
        return MethodDef(name, params, body)

    def method_call(self, obj):
        self.eat('DOT')
        method = self.current_token.value
        self.eat('IDENTIFIER')
        self.eat('LPAREN')
        args = self.argument_list()
        self.eat('RPAREN')
        return MethodCall(obj, method, args)

    def async_function_definition(self):
        self.eat('ASYNC')
        self.eat('DEF')
        name = self.current_token.value
        self.eat('IDENTIFIER')
        self.eat('LPAREN')
        params = self.parameter_list()
        self.eat('RPAREN')
        self.eat('COLON')
        body = self.block()
        return AsyncFunctionDef(name, params, body)

    def await_expression(self):
        self.eat('AWAIT')
        expr = self.expression()
        return AwaitExpr(expr)

    def decorator_list(self):
        decorators = []
        while self.current_token.type == 'AT':
            self.eat('AT')
            name = self.current_token.value
            self.eat('IDENTIFIER')
            args = []
            if self.current_token.type == 'LPAREN':
                self.eat('LPAREN')
                if self.current_token.type != 'RPAREN':
                    args = self.argument_list()
                self.eat('RPAREN')
            decorators.append(Decorator(name, args))
        return decorators

    def with_statement(self):
        self.eat('WITH')
        context_expr = self.expression()
        optional_vars = None
        if self.current_token.type == 'AS':
            self.eat('AS')
            optional_vars = self.expression()
        self.eat('COLON')
        body = self.block()
        return WithStatement(context_expr, optional_vars, body)

    def generator_expression(self):
        self.eat('LPAREN')
        expression = self.expression()
        self.eat('FOR')
        target = self.expression()
        self.eat('IN')
        iterable = self.expression()
        self.eat('RPAREN')
        return GeneratorExpression(expression, target, iterable)

    def lambda_expression(self):
        self.eat('LAMBDA')
        params = []
        if self.current_token.type != 'COLON':
            params = self.parameter_list()
        self.eat('COLON')
        body = self.expression()
        return LambdaExpression(params, body)

    def print_statement(self):
        self.eat('PRINT')
        self.eat('LPAREN')
        expressions = []
        
        if self.current_token.type != 'RPAREN':
            expressions.append(self.expression())
            while self.current_token.type == 'COMMA':
                self.eat('COMMA')
                expressions.append(self.expression())
        
        self.eat('RPAREN')
        return PrintStatement(expressions)

    def assignment_statement(self):
        left = self.primary()
        if self.current_token.type == 'EQUALS':
            self.eat('EQUALS')
            right = self.expression()
            return Assignment(left, right)
        self.error(f"Expected assignment operator, got {self.current_token.type}")

    def assignment_or_expression(self):
        expr = self.expression()  # Парсим выражение
        if self.current_token.type == 'EQUALS':
            self.eat('EQUALS')
            rhs = self.expression()
            return Assignment(expr, rhs)
        else:
            return expr  # Возвращаем выражение без присваивания

def parse(tokens):
    parser = Parser(tokens)
    return parser.parse()

