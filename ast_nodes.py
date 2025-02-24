class ASTNode:
    pass

class Program(ASTNode):
    def __init__(self, statements):
        self.statements = statements

class FunctionDef(ASTNode):
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class IfStatement(ASTNode):
    def __init__(self, condition, true_body, false_body=None):
        self.condition = condition
        self.true_body = true_body
        self.false_body = false_body

class BinaryOp(ASTNode):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class UnaryOp(ASTNode):
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

class Num(ASTNode):
    def __init__(self, value):
        self.value = value

class String(ASTNode):
    def __init__(self, value):
        self.value = value

class Identifier(ASTNode):
    def __init__(self, name):
        self.name = name

class Assignment(ASTNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right

class FunctionCall(ASTNode):
    def __init__(self, name, args):
        self.name = name
        self.args = args

class ReturnStatement(ASTNode):
    def __init__(self, expr):
        self.expr = expr

class WhileStatement(ASTNode):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class ForStatement(ASTNode):
    def __init__(self, target, iterable, body):
        self.target = target
        self.iterable = iterable
        self.body = body

class ListNode(ASTNode):
    def __init__(self, elements):
        self.elements = elements

class DictNode(ASTNode):
    def __init__(self, pairs):
        self.pairs = pairs

class TryExcept(ASTNode):
    def __init__(self, try_body, except_handlers, else_body=None, finally_body=None):
        self.try_body = try_body
        self.except_handlers = except_handlers
        self.else_body = else_body
        self.finally_body = finally_body

class ExceptHandler(ASTNode):
    def __init__(self, exc_type, exc_name, body):
        self.exc_type = exc_type
        self.exc_name = exc_name
        self.body = body

class ImportStatement(ASTNode):
    def __init__(self, module, names=None, alias=None):
        self.module = module
        self.names = names
        self.alias = alias

class ClassDef(ASTNode):
    def __init__(self, name, base_class, body):
        self.name = name
        self.base_class = base_class
        self.body = body

class MethodDef(ASTNode):
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class Decorator(ASTNode):
    def __init__(self, name, args=None):
        self.name = name
        self.args = args or []

class DecoratedDef(ASTNode):
    def __init__(self, decorators, definition):
        self.decorators = decorators
        self.definition = definition

class WithStatement(ASTNode):
    def __init__(self, context_expr, optional_vars, body):
        self.context_expr = context_expr
        self.optional_vars = optional_vars
        self.body = body

class GeneratorExpression(ASTNode):
    def __init__(self, expression, variables, iterables):
        self.expression = expression
        self.variables = variables
        self.iterables = iterables

class PrintStatement(ASTNode):
    def __init__(self, expressions):
        self.expressions = expressions

class LambdaExpression(ASTNode):
    def __init__(self, params, body):
        self.params = params
        self.body = body

class MethodCall:
    def __init__(self, obj, method_name, args):
        self.obj = obj
        self.method_name = method_name
        self.args = args

class Attribute:
    def __init__(self, obj, attr_name):
        self.obj = obj
        self.attr_name = attr_name

class MainBlock(ASTNode):
    def __init__(self, body):
        self.body = body

class ListComprehension(ASTNode):
    def __init__(self, expression, target, iterable, condition=None):
        self.expression = expression  # Выражение для каждого элемента
        self.target = target           # Целевая переменная
        self.iterable = iterable       # Итерируемый объект
        self.condition = condition     # Условие фильтрации (опционально)

class Compare(ASTNode):
    def __init__(self, left, ops, comparators):
        """
        Инициализирует узел сравнения.

        :param left: Левый операнд (например, переменная или выражение)
        :param ops: Список операторов сравнения (например, ['==', '<'])
        :param comparators: Список правых операндов
        """
        self.left = left
        self.ops = ops  # Список операторов, например, ['==']
        self.comparators = comparators  # Список правых операндов

# class ListComprehensionNode:
#     def __init__(self, expression, target, iterable, condition=None):
#         self.expression = expression
#         self.target = target
#         self.iterable = iterable
#         self.condition = condition
