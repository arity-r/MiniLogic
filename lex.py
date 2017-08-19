import ply.lex as lex
from ast import Node

reserved = {
	'or'     : 'LOR',
	'and'    : 'LAND',
	'neg'    : 'NEG',
	'exists' : 'EXISTS',
	'forall' : 'FORALL',
	'implies': 'IMPLIES',
	'iff'    : 'IFF'
}

tokens = tuple(
	[
	'WORD',
	'VARIABLE',
	'CONSTANT',
	'FUNCTION',
	'PREDICATE',
	'COMMA',
	'LPAREN',
	'RPAREN',
	'LBRACKET',
	'RBRACKET',
	] + list(reserved.values())
)

t_COMMA     = r','
t_LPAREN    = r'\('
t_RPAREN    = r'\)'
t_LBRACKET  = r'\['
t_RBRACKET  = r'\]'

def t_WORD(t):
	r'[a-zA-Z][a-zA-Z]+' # HACK no reserved word has len < 2
	type = reserved.get(t.value)
	if not type:
		t_error(t)
	t.type = type
	t.value = Node(type, t.value)
	return t

def t_VARIABLE(t):
	r'[u-z]'
	t.value = Node('VARIABLE', t.value)
	return t

def t_CONSTANT(t):
	r'[a-e]'
	t.value = Node('CONSTANT', t.value)
	return t

def t_FUNCTION(t):
	r'[f-j]'
	t.value = Node('FUNCTION', t.value)
	return t

def t_PREDICATE(t):
	r'[P-U]'
	t.value = Node('PREDICATE', t.value)
	return t

def t_newline(t):
	r'\n+'
	t.lexer.lineno += len(t.value)

t_ignore = ' \t'

def t_error(t):
	print("Illegal character '%s'" % t.value[0])
	t.lexer.skip(1)

lexer = lex.lex()
#lexer = lex.lex(optimize=1, debug=1)

if __name__ == '__main__':
	data = '''neg (exists x)(forall y)[P(x,y) iff neg Q(y, x, y)]'''
	lexer.input(data)
	for tok in lexer:
		print(tok)
