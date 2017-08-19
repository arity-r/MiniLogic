from copy import deepcopy
from yacc import parser

from ast import ast_to_string
from cnf import *

data = 'neg (exists x)(forall y)[P(x,y) iff neg Q(y,x,y)]'
#data = 'neg (exists x)(forall y)[P(f(x), y) and forall x exists y forall z[Q(x, y) and R(w, x, z)]]'
#data = 'neg neg neg neg P'
#data = '(exists x)(exists y)[forall z P(x, y, z)]'
"""
data = 'neg P and     Q and neg R and neg S or' +\
       '    P and neg Q and neg R and neg S or' +\
       '    P and neg Q and neg R and     S or' +\
       '    P and neg Q and     R and neg S or' +\
       '    P and neg Q and     R and     S or' +\
       '    P and     Q and neg R and neg S or' +\
       '    P and     Q and     R and neg S or' +\
       '    P and     Q and     R and     S'
"""
"""
data = 'neg P and neg Q and neg R or ' +\
       'neg P and neg Q and     R or ' +\
       'neg P and     Q and neg R or ' +\
       '    P and neg Q and     R or ' +\
       '    P and     Q and neg R or ' +\
       '    P and     Q and     R'
"""
"""
data = 'neg P and neg Q and neg R and neg S or ' +\
       'neg P and neg Q and     R and neg S or ' +\
       'neg P and     Q and neg R and     S or ' +\
       'neg P and     Q and     R and neg S or ' +\
       'neg P and     Q and     R and     S or ' +\
       '    P and neg Q and neg R and neg S or ' +\
       '    P and neg Q and     R and neg S or ' +\
       '    P and     Q and neg R and neg S or ' +\
       '    P and     Q and neg R and     S or ' +\
       '    P and     Q and     R and neg S or ' +\
       '    P and     Q and     R and     S'
"""
#data = 'P and neg R or P and neg Q or Q and S and neg T'

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
