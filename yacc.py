import ply.yacc as yacc
from lex import tokens
from ast import Node

def p_binop(p):
	'''formula : expression IMPLIES formula
	           | expression IFF    formula
	   expression : expression LOR term
	   term : term LAND factor
	'''
	p[2].child = [p[1], p[3]]
	p[0] = p[2]

def p_uniop(p):
	'''factor : NEG factor
	'''
	p[1].child = [p[2]]
	p[0] = p[1]

def p_quantifier(p):
	'''factor : FORALL VARIABLE factor
	          | EXISTS VARIABLE factor
	'''
	p[1].child = [p[2], p[3]]
	p[0] = p[1]

def p_quantifier_group(p):
	'''factor : LPAREN FORALL VARIABLE RPAREN factor
	          | LPAREN EXISTS VARIABLE RPAREN factor
	'''
	p[2].child = [p[3], p[5]]
	p[0] = p[2]

def p_atomic(p):
	'''atomic : PREDICATE LPAREN lterms RPAREN
	'''
	if type(p[3]) == list:
		p[1].child = p[3]
	else:
		p[1].child = [p[3]]
	p[0] = p[1]

def p_atomic_group(p):
	'''atomic : LPAREN   formula RPAREN
	          | LBRACKET formula RBRACKET 
	'''
	p[0] = p[2]

def p_lterms(p):
	'''lterms : lterm COMMA lterms
	'''
	if type(p[3]) == list:
		p[0] = [p[1], *p[3]]
	else:
		p[0] = [p[1], p[3]]

def p_lterm_function(p):
	'''lterm : FUNCTION LPAREN lterms RPAREN
	'''
	if type(p[3]) == list:
		p[1].child = p[3]
	else:
		p[1].child = [p[3]]
	p[0] = p[1]

def p_pass(p):
	'''formula : expression
	   expression : term
	   term : factor
	   factor : atomic
	   atomic : PREDICATE
	   lterms : lterm
	   lterm : VARIABLE
	         | CONSTANT
	'''
	p[0] = p[1]

def p_error(p):
	print("Syntax error in input!")

#parser = yacc.yacc()
parser = yacc.yacc(
	write_tables=False,
	debug=False,
	errorlog=yacc.NullLogger()
)

if __name__ == '__main__':
	from ast import ast_to_string
	data = '''neg (exists x)(forall y)[P(x,y) iff neg Q(y, x, y)]'''
	#data = '(P(x) or P(y)) and (P(z) or P(w))'
	result = parser.parse(data)
	print(result)
	print(ast_to_string(result))
