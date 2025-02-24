STANDARD_LIBRARY_MAPPING = {
    'print': 'println!',
    'len': 'len',
    'range': '0..', # Нужно будет обработать аргументы отдельно
    'list': 'Vec',
    'dict': 'HashMap',
    'set': 'HashSet',
    'str': 'String',
    'int': 'i32',
    'float': 'f64',
    'bool': 'bool',
    'max': 'std::cmp::max',
    'min': 'std::cmp::min',
    'sum': 'iter().sum()',
    'sorted': 'sorted',
    'enumerate': 'enumerate',
    'zip': 'zip',
    'map': 'map',
    'filter': 'filter',
    'any': 'any',
    'all': 'all',
}

METHOD_MAPPING = {
    'append': 'push',
    'extend': 'extend',
    'insert': 'insert',
    'remove': 'remove',
    'pop': 'pop',
    'clear': 'clear',
    'index': 'iter().position',
    'count': 'iter().filter(|&x| x == value).count()',
    'sort': 'sort',
    'reverse': 'reverse',
    'join': 'join',
    'split': 'split',
    'strip': 'trim',
    'lstrip': 'trim_start',
    'rstrip': 'trim_end',
    'upper': 'to_uppercase',
    'lower': 'to_lowercase',
    'startswith': 'starts_with',
    'endswith': 'ends_with',
    'replace': 'replace',
    # Добавьте другие методы по необходимости
}

DECORATOR_MAPPING = {
    'staticmethod': 'allow(dead_code)',
    'classmethod': 'allow(dead_code)',
    'property': 'derive(Debug)',
    'abstractmethod': 'derive(Default)',
    'dataclass': 'derive(Debug, Clone, PartialEq)',
}

CONTEXT_MANAGER_MAPPING = {
    'open': 'File::open',
    'threading.Lock': 'std::sync::Mutex::new',
    'multiprocessing.Lock': 'std::sync::Mutex::new',
    'tempfile.NamedTemporaryFile': 'tempfile::NamedTempFile::new',
}
