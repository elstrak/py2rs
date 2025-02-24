from ast_nodes import *
from type_inference import TypeInference
from standard_library_mapping import METHOD_MAPPING

class CodeGenerator:
    def __init__(self):
        self.code = []  # Список для хранения сгенерированного кода
        self.indent_level = 0  # Уровень отступа
        self.type_inference = TypeInference()

    def generate(self, node):
        # Динамически вызывает соответствующий метод генерации для каждого типа узла
        method_name = f'generate_{type(node).__name__}'
        generator = getattr(self, method_name, self.generic_generate)
        return generator(node)

    def generic_generate(self, node):
        # Вызывается, если нет специального метода для данного типа узла
        raise Exception(f'Нет генератора для типа узла: {type(node).__name__}')

    def indent(self):
        # Возвращае строку с текущим уровнем отступа
        return '    ' * self.indent_level

    def generate_Program(self, node):
        imports = []
        functions = []
        main_statements = []
        
        for statement in node.statements:
            if isinstance(statement, ImportStatement):
                imports.append(self.generate(statement))
            elif isinstance(statement, FunctionDef):
                functions.append(self.generate(statement))
            elif isinstance(statement, MainBlock):
                # Если это MainBlock, добавляем его содержимое в main_statements
                main_statements.extend(self.generate_statements(statement.body))
            else:
                stmt = self.generate(statement)
                if stmt:
                    main_statements.append(stmt)
        
        code = []
        if imports:
            code.extend(imports)
            code.append('')
        
        if functions:
            code.extend(functions)
            code.append('')
        
        if main_statements:
            code.append('fn main() {')
            for stmt in main_statements:
                code.append(f'    {stmt}')
            code.append('}')
        
        return '\n'.join(filter(None, code))

    def is_main_block(self, if_statement):
        if isinstance(if_statement.condition, BinaryOp):
            left = if_statement.condition.left
            right = if_statement.condition.right
            return (isinstance(left, Identifier) and 
                    left.name == '__name__' and 
                    isinstance(right, String) and 
                    right.value == '__main__')
        return False

    def generate_FunctionDef(self, node):
        self.type_inference.enter_scope()
        
        # Регистрируем функцию для анализа рекурсивных вызовов
        self.type_inference.register_function(node.name, node)
        
        for param in node.params:
            self.type_inference.update_type(param, 'unknown')
        
        params = []
        for param in node.params:
            param_type = self.type_inference.infer_type(Identifier(param))
            if param == 'self':
                params.append('&self')
            elif self.type_inference.is_reference(param_type):
                params.append(f'{param}: {param_type}')
            elif param_type == 'unknown':
                param_type = 'i32'  # Предполагаем тип по умолчанию
                params.append(f'{param}: {param_type}')
                self.type_inference.update_type(param, param_type)
            else:
                params.append(f'{param}: {param_type}')
        
        params_str = ', '.join(params)
        
        # Анализируем тело функции для определения возвращаемого типа
        return_type = 'i32'  # Для рекурсивных функций предполагаем i32
        for statement in node.body:
            if isinstance(statement, ReturnStatement):
                expr_type = self.type_inference.infer_type(statement.expr)
                if expr_type != 'unknown':
                    return_type = expr_type
                break
        
        function_code = f'{self.indent()}fn {node.name}({params_str}) -> {return_type} {{\n'
        self.indent_level += 1
        for statement in node.body:
            stmt_code = self.generate(statement)
            function_code += f'{stmt_code}\n'
        self.indent_level -= 1
        function_code += f'{self.indent()}}}'
        
        self.type_inference.exit_scope()
        
        return function_code

    def generate_IfStatement(self, node):
        condition = self.generate(node.condition)
        code = f'{self.indent()}if {condition} {{\n'
        self.indent_level += 1
        for statement in node.true_body:
            stmt_code = self.generate(statement)
            code += f'{stmt_code}\n'
        self.indent_level -= 1
        code += f'{self.indent()}}}'
        
        if node.false_body:
            code += ' else {\n'
            self.indent_level += 1
            for statement in node.false_body:
                stmt_code = self.generate(statement)
                code += f'{stmt_code}\n'
            self.indent_level -= 1
            code += f'{self.indent()}}}'
        
        return code

    def generate_BinaryOp(self, node):
        left = self.generate(node.left)
        right = self.generate(node.right)
        
        # Для строковых сравнений не добавляем .to_string()
        if node.op == '==' and (isinstance(node.left, String) or isinstance(node.right, String)):
            return f'({left} == {right})'
        return f'({left} {node.op} {right})'

    def generate_UnaryOp(self, node):
        # Генерирует код для унарных операий
        expr = self.generate(node.expr)
        return f'({node.op}{expr})'

    def generate_Num(self, node):
        # Генерирует код для числовых литералов
        return str(node.value)

    def generate_String(self, node):
        return f'"{node.value}"'

    def generate_Identifier(self, node):
        # Генериует код для идентификаторов
        return node.name

    def generate_Assignment(self, node):
        left = self.generate(node.left)
        right = self.generate(node.right)
        inferred_type = self.type_inference.infer_type(node.right)
        
        # Если это первое присваивание (инициализация)
        if isinstance(node.left, Identifier):
            if isinstance(node.right, ListNode) and not isinstance(node.right, ListComprehension):
                # Обработка обычных списков
                if node.right.elements:
                    elem_type = self.type_inference.infer_type(node.right.elements[0])
                    return f'{self.indent()}let mut {left}: Vec<{elem_type}> = {right};'
                else:
                    return f'{self.indent()}let mut {left}: Vec<String> = Vec::new();'
            elif isinstance(node.right, ListComprehension):
                # Обработка списковых включений
                elem_type = self.type_inference.infer_type(node.right)
                return f'{self.indent()}let mut {left}: Vec<{elem_type}> = {right};'
            else:
                # Обработка остальных случаев
                return f'{self.indent()}let mut {left} = {right};'
        else:
            return f'{self.indent()}{left} = {right};'

    def generate_FunctionCall(self, node):
        from standard_library_mapping import STANDARD_LIBRARY_MAPPING

        if node.name in STANDARD_LIBRARY_MAPPING:
            rust_func = STANDARD_LIBRARY_MAPPING[node.name]
            
            if rust_func == 'println!':
                return self.generate_PrintStatement(node)
            
            elif rust_func == 'map':
                if len(node.args) == 2:
                    lambda_expr = self.generate(node.args[0])
                    collection = self.generate(node.args[1])
                    return f'{collection}.iter().map({lambda_expr}).collect::<Vec<_>>()'
            
            else:
                args = ', '.join(self.generate(arg) for arg in node.args)
                return f'{rust_func}({args})'
        else:
            args = ', '.join(self.generate(arg) for arg in node.args)
            return f'{node.name}({args})'

    def generate_WhileStatement(self, node):
        # Генерирует код для цикла while
        condition = self.generate(node.condition)
        self.code.append(f'{self.indent()}while {condition} {{')
        self.indent_level += 1
        for statement in node.body:
            self.code.append(self.generate(statement))
        self.indent_level -= 1
        self.code.append(f'{self.indent()}}}')
        return ''

    def generate_ForStatement(self, node):
        target = self.generate(node.target)
        if isinstance(node.iterable, FunctionCall) and node.iterable.name == 'range':
            # Специальная обработка для range()
            if len(node.iterable.args) == 1:
                end = self.generate(node.iterable.args[0])
                for_header = f'for {target} in 0..{end} {{'
            elif len(node.iterable.args) == 2:
                start = self.generate(node.iterable.args[0])
                end = self.generate(node.iterable.args[1])
                for_header = f'for {target} in {start}..{end} {{'
            elif len(node.iterable.args) == 3:
                start, end, step = node.iterable.args
                for_header = f'for {target} in ({self.generate(start)}..{self.generate(end)}).step_by({self.generate(step)}) {{'
        else:
            iterable = self.generate(node.iterable)
            for_header = f'for {target} in {iterable} {{'
        
        # Генерация тела цикла
        self.indent_level += 1
        body = '\n'.join(self.generate(statement) for statement in node.body)
        self.indent_level -= 1
        for_footer = f'{self.indent()}}}'
        
        return f'{self.indent()}{for_header}\n{body}\n{for_footer}'

    def generate_ReturnStatement(self, node):
        # Генерирует код для операора return
        expr = self.generate(node.expr)
        return f'{self.indent()}return {expr};'

    def generate_ListNode(self, node):
        if not node.elements:
            return 'Vec::new()'
        
        elements = []
        for elem in node.elements:
            if isinstance(elem, String):
                elements.append(f'"{elem.value}".to_string()')
            else:
                elements.append(self.generate(elem))
        
        elements_str = ', '.join(elements)
        return f'vec![{elements_str}]'

    def generate_DictNode(self, node):
        pairs = [f'{self.generate(k)}: {self.generate(v)}' for k, v in node.pairs]
        return f'HashMap::from([{", ".join(pairs)}])'

    def generate_TryExcept(self, node):
        self.code.append(f'{self.indent()}match (|| -> Result<(), Box<dyn std::error::Error>> {{')
        self.indent_level += 1
        for statement in node.try_body:
            self.code.append(self.generate(statement))
        self.indent_level -= 1
        self.code.append(f'{self.indent()}}})() {{')
        self.indent_level += 1
        self.code.append(f'{self.indent()}Ok(_) => {{')
        if node.else_body:
            self.indent_level += 1
            for statement in node.else_body:
                self.code.append(self.generate(statement))
            self.indent_level -= 1
        self.code.append(f'{self.indent()}}},')
        for handler in node.except_handlers:
            if handler.exc_type:
                exc_type = self.generate(handler.exc_type)
                self.code.append(f'{self.indent()}Err(e) if e.is::<{exc_type}>() => {{')
            else:
                self.code.append(f'{self.indent()}Err(e) => {{')
            self.indent_level += 1
            if handler.exc_name:
                self.code.append(f'{self.indent()}let {handler.exc_name} = e.downcast::<{exc_type}>().unwrap();')
            for statement in handler.body:
                self.code.append(self.generate(statement))
            self.indent_level -= 1
            self.code.append(f'{self.indent()}}},')
        self.indent_level -= 1
        self.code.append(f'{self.indent()}}}')
        if node.finally_body:
            self.code.append(f'{self.indent()}// Finally block')
            for statement in node.finally_body:
                self.code.append(self.generate(statement))
        return ''

    def generate_ImportStatement(self, node):
        if node.alias:
            return f'{self.indent()}use {node.module_name} as {node.alias};'
        else:
            return f'{self.indent()}use {node.module_name};'

    def generate_ClassDef(self, node):
        base_class = f': {node.base_class}' if node.base_class else ''
        self.code.append(f'{self.indent()}struct {node.name}{base_class} {{')
        self.indent_level += 1
        
        # Генерируем поля структуры
        for statement in node.body:
            if isinstance(statement, Assignment):
                field_name = self.generate(statement.left)
                field_type = self.type_inference.infer_type(statement.right)
                self.code.append(f'{self.indent()}{field_name}: {field_type},')
        
        self.indent_level -= 1
        self.code.append(f'{self.indent()}}}')
        
        # Генерируем реализацию методов
        self.code.append(f'{self.indent()}impl {node.name} {{')
        self.indent_level += 1
        
        for statement in node.body:
            if isinstance(statement, FunctionDef):
                self.code.append(self.generate(statement))
        
        self.indent_level -= 1
        self.code.append(f'{self.indent()}}}')
        
        # Генерируем реазацю трейтов
        if node.traits:
            for trait in node.traits:
                self.code.append(f'{self.indent()}impl {trait} for {node.name} {{')
                self.indent_level += 1
                
                for method in [m for m in node.body if isinstance(m, FunctionDef) and m.name in trait.methods]:
                    self.code.append(self.generate(method))
                
                self.indent_level -= 1
                self.code.append(f'{self.indent()}}}')
        
        return ''

    def generate_MethodDef(self, node):
        params = []
        for param in node.params:
            if param == 'self':
                params.append('&self')
            else:
                param_type = self.type_inference.infer_type(Identifier(param))
                params.append(f'{param}: {param_type}')
        params_str = ', '.join(params)
        
        return_type = 'unknown'
        for statement in node.body:
            if isinstance(statement, ReturnStatement):
                return_type = self.type_inference.infer_type(statement.expr)
                break
        
        if return_type == 'unknown':
            return_type = '()'
        
        method_code = f'{self.indent()}fn {node.name}({params_str}) -> {return_type} {{\n'
        self.indent_level += 1
        for statement in node.body:
            stmt_code = self.generate(statement)
            method_code += f'{stmt_code}\n'
        self.indent_level -= 1
        method_code += f'{self.indent()}}}'
        
        return method_code

    def generate_MethodCall(self, node):
        obj = self.generate(node.obj)
        method = node.method_name
        args = ', '.join(self.generate(arg) for arg in node.args)
        if method in METHOD_MAPPING:
            rust_method = METHOD_MAPPING[method]
            return f'{self.indent()}{obj}.{rust_method}({args});'
        else:
            return f'{self.indent()}{obj}.{method}({args});'

    def generate_Attribute(self, node):
        obj = self.generate(node.obj)
        return f"{obj}.{node.attr_name}"

    def generate_AsyncFunctionDef(self, node):
        params = []
        for param in node.params:
            param_type = self.type_inference.infer_type(Identifier(param))
            params.append(f'{param}: {param_type}')
        params_str = ', '.join(params)
        
        return_type = 'unknown'
        for statement in node.body:
            if isinstance(statement, ReturnStatement):
                return_type = self.type_inference.infer_type(statement.expr)
                break
        
        if return_type == 'unknown':
            return_type = '()'
        
        self.code.append(f'{self.indent()}async fn {node.name}({params_str}) -> {return_type} {{')
        self.indent_level += 1
        for statement in node.body:
            self.code.append(self.generate(statement))
        self.indent_level -= 1
        self.code.append(f'{self.indent()}}}')
        return ''

    def generate_AwaitExpr(self, node):
        expr = self.generate(node.expr)
        return f'{expr}.await'

    def generate_Decorator(self, node):
        if node.name in DECORATOR_MAPPING:
            return f'{self.indent()}#[{DECORATOR_MAPPING[node.name]}]'
        else:
            args = ', '.join(self.generate(arg) for arg in node.args)
            return f'{self.indent()}#[{node.name}({args})]'

    def generate_DecoratedDef(self, node):
        for decorator in node.decorators:
            self.code.append(self.generate(decorator))
        return self.generate(node.definition)

    def generate_GeneratorExpression(self, node):
        iterable = self.generate(node.iterable)
        target = self.generate(node.target)
        expression = self.generate(node.expression)
        return f'{iterable}.iter().map(|{target}| {expression})'

    def generate_PrintStatement(self, node):
        expressions = node.expressions

        if not expressions:
            return f'{self.indent()}println!();'

        format_string = ""
        args = []

        if isinstance(expressions[0], String):
            format_string += expressions[0].value
            for expr in expressions[1:]:
                format_string += " {:?}"
                args.append(self.generate(expr))
        else:
            format_string = " ".join(["{:?}"] * len(expressions))
            args = [self.generate(expr) for expr in expressions]

        if args:
            args_string = ', '.join(args)
            return f'{self.indent()}println!("{format_string}", {args_string});'
        else:
            return f'{self.indent()}println!("{format_string}");'

    def generate_MainBlock(self, node):
        code = ['fn main() {']
        self.indent_level += 1
        for statement in node.body:
            stmt_code = self.generate(statement)
            if stmt_code:  # роверяем, что statement не пустой
                code.append(stmt_code)
        self.indent_level -= 1
        code.append('}')
        return '\n'.join(code)

    def generate_ListComprehension(self, node):
        iterable = self.generate(node.iterable)
        target = self.generate(node.target)
        expression = self.generate(node.expression)
        
        # Генерация метода filter, если есть условие
        if node.condition:
            condition = self.generate(node.condition)
            filter_part = f'.filter(|&{target}| {condition})'
        else:
            filter_part = ''
        
        # Генерация метода map
        map_expression = f'.map(|{target}| {expression})'
        
        # Сборка полного выражения и преобразование в Vec
        return f'{iterable}.iter(){filter_part}{map_expression}.collect::<Vec<_>>()'

    def generate_LambdaExpression(self, node):
        # Для лямбда-выражений в Python параметр приходят как строки
        params = node.params if isinstance(node.params, list) else [node.params]
        params_str = ', '.join(param if isinstance(param, str) else self.generate(param) for param in params)
        body = self.generate(node.body)
        return f'|{params_str}| {body}'

def generate_code(ast):
    # Создает экземпляр генератора кода и запускает генерацию
    generator = CodeGenerator()
    return generator.generate(ast)

