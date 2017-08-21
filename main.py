from copy import deepcopy
from yacc import parser

from ast import Node, ast_to_string
from cnf import *
from resolution import *

#data = 'neg (exists x)(forall y)[P(x,y) iff neg Q(y,x,y)]'
#data = 'neg (exists x)[P(f(x)) and exists x forall y [Q(g(x), y)] and R(x, w)]'
#data = '(forall x)[(forall x)[(forall x)P(x) or Q(x)] or R(x)]'
#data = 'neg neg neg neg P'
#data = '(exists x)(exists y)[forall z P(x, y, z)]'
#data = 'P and neg R or P and neg Q or Q and S and neg T'

"""
root = parser.parse(data)
print(ast_to_string(root))
root = eliminate_implication_and_iff(root)
print(ast_to_string(root))
root = move_negation(root)
print(ast_to_string(root))
root = standarize_variables(root)
print(ast_to_string(root))
root = eliminate_existential_quantifiers(root)
print(ast_to_string(root))
root = move_quantifiers(root)
print(ast_to_string(root))
root = conjunctive_normal_form(root)
print(ast_to_string(root))
"""

A = 'neg (exists z)R(z,a) and (forall x)(exists y)[P(x,y) implies Q(x)] and (forall x)(exists y)[Q(x) implies R(y,x)]'
B = '(exists w)[neg P(a,w)]'

A = parser.parse(A)
B = parser.parse(B)
B = Node('NEG', 'neg', [B])

A = wff_to_cnf(A)
B = wff_to_cnf(B)

print('    A = ' + ast_to_string(A))
print('neg B = ' + ast_to_string(B))

CA = get_clauses(A)
CB = get_clauses(B)
clauses = CA + CB

empty_clause = build_resolution_tree(CA+CB)
print()
print(rnode_to_string(empty_clause))
