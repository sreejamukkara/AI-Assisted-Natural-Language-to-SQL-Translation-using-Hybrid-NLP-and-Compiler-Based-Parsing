import ply.lex as lex
import re
from .diagnostics import LexerError

# Reserved words / Keywords mapping English tokens to SQL concepts
reserved = {
    'show': 'SELECT',
    'get': 'SELECT',
    'find': 'SELECT',
    'list': 'SELECT',
    'display': 'SELECT',
    'fetch': 'SELECT',
    
    'give': 'SELECT',
    'retrieve': 'SELECT',
    
    'in': 'FROM',
    'from': 'FROM',
    
    'where': 'WHERE',
    'with': 'WHERE',
    'who': 'WHERE',
    'that': 'WHERE',
    
    'and': 'AND',
    'or': 'OR',
    'join': 'JOIN',
    'on': 'ON',
    'order': 'ORDER',
    'by': 'BY',
    'group': 'GROUP',
    'limit': 'LIMIT',
    'asc': 'ASC',
    'desc': 'DESC',
    
    'count': 'COUNT',
    'avg': 'AVG',
    'having': 'HAVING',
}

tokens = [
    'IDENTIFIER',
    'NUMBER',
    'OPERATOR',
    'COMMA',
    'ASTERISK',
    'STRING',
    'PLUS',
    'MINUS',
    'DIVIDE'
] + list(set(reserved.values()))

t_COMMA = r','
t_ASTERISK = r'\*'
t_PLUS = r'\+'
t_MINUS = r'-'
t_DIVIDE = r'/'

# Operators
def t_OPERATOR(t):
    r'>=|<=|!=|!|>|<|='
    return t

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_STRING(t):
    r'(\'[^\']*\')|("[^"]*")'
    t.value = t.value[1:-1]
    return t

def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t_lower = t.value.lower()
    t.type = reserved.get(t_lower, 'IDENTIFIER')
    return t

t_ignore = ' \t\n'

def t_error(t):
    # Depending on how strict we are, we can just skip unknown chars or throw.
    # For a fuzzy NL compiler, it's safer to skip unknown punctuation.
    if t.value[0] in ['.', '?', '!']:
        t.lexer.skip(1)
    else:
        raise LexerError(f"Illegal character '{t.value[0]}'", t.lexpos)

lexer = lex.lex()

stopwords = [
    "please", "me", "all", "the", "details", "who", "is", "are", "a", "an", 
    "there", "their", "they", "info", "information", "of", "about", "data", 
    "records", "members", "earn", "earns", "earning", "having", "has", "have"
]

def preprocess_query(query: str) -> str:
    original_query = query
    q = query.lower()
    
    # Preprocess NL operators
    q = re.sub(r'greater than or equal to|at least', '>=', q)
    q = re.sub(r'less than or equal to|at most', '<=', q)
    q = re.sub(r'not equal to|different from', '!=', q)
    q = re.sub(r'greater than|more than|higher than|above', '>', q)
    q = re.sub(r'less than|smaller than|fewer than|under', '<', q)
    q = re.sub(r'equal to|equals|exactly', '=', q)
    
    # Strip stopwords
    words = q.split()
    words = [w for w in words if w not in stopwords]
    
    # Synonym resolution for baseline table entities
    syns = {
        "workers": "employees", "worker": "employees", 
        "staff": "employees", "team": "employees",
        "dept": "departments", "department": "departments"
    }
    words = [syns.get(w, w) for w in words]
    
    return " ".join(words)

def tokenize(query: str):
    processed = preprocess_query(query)
    lexer.input(processed)
    
    toks = []
    while True:
        tok = lexer.token()
        if not tok: 
            break
        toks.append({
            "type": tok.type,
            "value": tok.value,
            "line": tok.lineno,
            "pos": tok.lexpos
        })
    return toks
