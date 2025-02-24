from ast_nodes import (
    Num, String, BinaryOp, Identifier, ListNode, 
    GeneratorExpression, LambdaExpression, ReturnStatement,
    FunctionCall, DictNode, ImportStatement,
    IfStatement, ForStatement, WhileStatement,
    ListComprehension
)

from standard_library_mapping import STANDARD_LIBRARY_MAPPING

class TypeInference:
    def __init__(self):
        self.scope_stack = [{}]
        self.functions = {}  # Для хранения определений функций
        self.current_scope = self.scope_stack[-1] if self.scope_stack else {}
        self.currently_analyzing = set()  # Для отслеживания функций в процессе анализа
    
    def enter_scope(self):
        self.scope_stack.append({})
        self.current_scope = self.scope_stack[-1]
    
    def exit_scope(self):
        self.scope_stack.pop()
        self.current_scope = self.scope_stack[-1] if self.scope_stack else {}
    
    def update_type(self, name, type_):
        self.current_scope[name] = type_
    
    def is_reference(self, type_):
        # Простой пример проверки, является ли тип ссылкой
        return type_.startswith('&')
    
    def register_function(self, name, node):
        self.functions[name] = node
    
    def find_function_definition(self, func_name):
        return self.functions.get(func_name, None)
    
    def analyze_function_body(self, function_def):
        self.currently_analyzing.add(function_def.name)
        return_types = self.collect_return_types(function_def.body)
        if not return_types:
            return_type = '()'  # Если нет явных return, возвращаем unit type
        else:
            unique_types = set(return_types)
            if len(unique_types) == 1:
                return_type = unique_types.pop()
            else:
                # Если есть несколько типов, выбираем наиболее подходящий
                if 'i32' in unique_types:
                    return_type = 'i32'
                else:
                    return_type = list(unique_types)[0]
        self.currently_analyzing.remove(function_def.name)
        return return_type
    
    def collect_return_types(self, statements):
        return_types = []
        for statement in statements:
            if isinstance(statement, ReturnStatement):
                return_types.append(self.infer_type(statement.expr))
            elif hasattr(statement, 'body') and isinstance(statement.body, list):
                # Рекурсивный вызов для вложенных блоков (например, if, for)
                return_types.extend(self.collect_return_types(statement.body))
            elif isinstance(statement, IfStatement):
                return_types.extend(self.collect_return_types(statement.true_body))
                if statement.false_body:
                    return_types.extend(self.collect_return_types(statement.false_body))
            elif isinstance(statement, ForStatement) or isinstance(statement, WhileStatement):
                return_types.extend(self.collect_return_types(statement.body))
            # Добавьте другие конструкции по мере необходимости
        return return_types
    
    def infer_function_return_type(self, node):
        if isinstance(node, FunctionCall):
            if node.name in self.functions:
                if node.name in self.currently_analyzing:
                    # Рекурсивный вызов, предполагаем тип возвращаемого значения
                    return 'i32'  # Измените на нужный тип, если требуется
                function_def = self.functions[node.name]
                return self.analyze_function_body(function_def)
            elif node.name in STANDARD_LIBRARY_MAPPING:
                return self.infer_standard_library_return_type(node.name)
        return 'unknown'
    
    def infer_standard_library_return_type(self, func_name):
        # Здесь можно определить возвращаемые типы для стандартных функций
        standard_types = {
            'len': 'usize',
            'range': 'std::ops::Range<i32>',
            'print': '()',
            'println!': '()',
            # Добавьте другие стандартные функции по мере необходимости
        }
        return standard_types.get(func_name, 'unknown')
    
    def infer_type(self, node):
        if isinstance(node, Num):
            return 'i32'  # Предполагаем, что все числа - целые 32-битные
        elif isinstance(node, GeneratorExpression):
            elem_type = self.infer_type(node.expression)
            return f'impl Iterator<Item = {elem_type}>'
        elif isinstance(node, LambdaExpression):
            param_types = [self.infer_type(param) for param in node.params]
            return_type = self.infer_type(node.body)
            return f'impl Fn({", ".join(param_types)}) -> {return_type}'
        elif isinstance(node, String):
            return 'String'  # В Rust строки - это String, а не &str
        elif isinstance(node, BinaryOp):
            left_type = self.infer_type(node.left)
            right_type = self.infer_type(node.right)
            if left_type == right_type:
                return left_type
            else:
                return 'unknown'
        elif isinstance(node, Identifier):
            for scope in reversed(self.scope_stack):
                if node.name in scope:
                    return scope[node.name]
            return 'unknown'
        elif isinstance(node, ListNode):
            if node.elements:
                elem_type = self.infer_type(node.elements[0])
                return f'Vec<{elem_type}>'
            else:
                return 'Vec<String>'  # Предполагаем тип по умолчанию
        elif isinstance(node, ListComprehension):
            # Предполагаем, что тип списка соответствует типу выражения
            elem_type = self.infer_type(node.expression)
            return f'Vec<{elem_type}>'
        elif isinstance(node, FunctionCall):
            return self.infer_function_return_type(node)
        else:
            return 'unknown'
