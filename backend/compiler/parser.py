import ply.yacc as yacc
from .lexer import tokens, lexer
from .ast_nodes import SQLQuery, ConditionNode, JoinNode, OrderNode, BinOpNode
from .diagnostics import ParserError

precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'ASTERISK', 'DIVIDE'),
)

# Grammar rules
def p_query(p):
    '''query : SELECT columns FROM IDENTIFIER where_clause group_clause having_clause join_clause order_clause limit_clause
             | SELECT IDENTIFIER where_clause group_clause having_clause join_clause order_clause limit_clause'''
    q = SQLQuery()
    
    if len(p) == 11:
        q.columns = p[2]
        q.table = p[4]
        q.conditions = p[5]
        q.group_by = p[6]
        q.having = p[7]
        q.joins = p[8]
        q.order_by = p[9]
        q.limit = p[10]
    else:
        q.table = p[2]
        q.conditions = p[3]
        q.group_by = p[4]
        q.having = p[5]
        q.joins = p[6]
        q.order_by = p[7]
        q.limit = p[8]
        
    p[0] = q

def p_columns(p):
    '''columns : IDENTIFIER
               | ASTERISK
               | COUNT IDENTIFIER
               | AVG IDENTIFIER
               | COUNT ASTERISK
               | columns COMMA columns'''
    if len(p) == 2:
        p[0] = [p[1]]
    elif len(p) == 4:
        p[0] = p[1] + p[3]
    else:
        if p[1] == "COUNT":
            p[0] = [f"COUNT({p[2]})"]
        elif p[1] == "AVG":
            p[0] = [f"AVG({p[2]})"]

def p_where_clause(p):
    '''where_clause : WHERE conditions
                    | empty'''
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = []

def p_conditions(p):
    '''conditions : condition
                  | condition AND conditions
                  | condition OR conditions'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        # Note: simplistic AST flattens AND/OR, real compiler would use tree for expressions
        p[0] = [p[1]] + p[3]

def p_group_clause(p):
    '''group_clause : GROUP BY columns
                    | empty'''
    if len(p) > 2:
        p[0] = p[3]
    else:
        p[0] = []

def p_having_clause(p):
    '''having_clause : HAVING conditions
                     | empty'''
    if len(p) > 2:
        p[0] = p[2]
    else:
        p[0] = []

def p_expr(p):
    '''expr : NUMBER
            | expr PLUS expr
            | expr MINUS expr
            | expr ASTERISK expr
            | expr DIVIDE expr'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinOpNode(left=p[1], operator=p[2], right=p[3])

def p_condition(p):
    '''condition : IDENTIFIER OPERATOR expr
                 | IDENTIFIER OPERATOR STRING'''
    p[0] = ConditionNode(column=p[1], operator=p[2], value=p[3])

def p_join_clause(p):
    '''join_clause : JOIN IDENTIFIER ON IDENTIFIER OPERATOR IDENTIFIER
                   | empty'''
    if len(p) > 2:
        p[0] = [JoinNode(table=p[2], join_type="INNER", on_left=p[4], on_right=p[6])]
    else:
        p[0] = []

def p_order_clause(p):
    '''order_clause : ORDER BY IDENTIFIER direction
                    | empty'''
    if len(p) > 2:
        p[0] = OrderNode(column=p[3], direction=p[4])
    else:
        p[0] = None

def p_direction(p):
    '''direction : ASC
                 | DESC
                 | empty'''
    p[0] = "ASC" if p[1] in [None, "ASC"] else "DESC"

def p_limit_clause(p):
    '''limit_clause : LIMIT NUMBER
                    | empty'''
    if len(p) > 2:
        p[0] = p[2]
    else:
        p[0] = None

def p_empty(p):
    'empty :'
    pass

def p_error(p):
    if p:
        raise ParserError(f"Syntax error at '{p.value}'", p.lexpos, "Try rephrasing your sentence closer to SQL structure")
    else:
        raise ParserError("Syntax error at EOF", -1, "Incomplete statement")

parser = yacc.yacc()

def parse_to_ast(query_str: str) -> SQLQuery:
    from .lexer import preprocess_query
    processed = preprocess_query(query_str)
    try:
        ast = parser.parse(processed, lexer=lexer)
        if not ast:
            raise ParserError("Could not parse query structure", 0, "Sentence too vague")
        return ast
    except ParserError as e:
        raise e
    except Exception as e:
        raise ParserError(str(e), 0, "Parser failed")
