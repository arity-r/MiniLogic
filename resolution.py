import re
from copy import deepcopy
from itertools import combinations
from ast import Node, ast_to_string, find_variables, resolve_variable_collisions

class RNode:
	def __init__(self, clause, 
		left=None, right=None, unifier=None):
		self.clause = clause
		self.left = left
		self.right = right
		self.unifier = unifier
		self.ancestors = set((self,))
		if left and right:
			self.ancestors.update(left.ancestors)
			self.ancestors.update(right.ancestors)

def rnode_to_string(node, n_to_s=ast_to_string):
	stack = [(node, 0)]
	ret = ''
	while len(stack) > 0:
		n, i = stack.pop()
		if not n.left and not n.right:
			pass
		elif i == 0:
			stack.append((n, 1))
			stack.append((n.right, 0))
			stack.append((n.left, 0))
		else:
			ret += ' or '.join(map(n_to_s, n.left.clause)) + '\n' +\
				' or '.join(map(n_to_s, n.right.clause)) + '\n' +\
				'-> ' + ' or '.join(map(n_to_s, n.clause)) + '\t' +\
				''.join(map(
					lambda u: '(' + n_to_s(u[1]) + '/' + u[0] + ')',
					n.unifier
					)) + '\n\n'

	return ret[:-2]

def _alpha_conversion(C, var_dict):
	ret = []
	for l in C:
		l = deepcopy(l)
		stack = [p for p in (l.child if l.type == 'PREDICATE'\
			else l.child[0].child)]
		while len(stack) > 0:
			n = stack.pop()
			if n.type == 'VARIABLE' and n.data in var_dict:
				n.data = var_dict[n.data]
			elif n.type == 'FUNCTION':
				stack.extend(n.child)
		ret.append(l)
	return ret

def _substitute(C, x, t):
	ret = []
	for l in C:
		stack = [p for p in (
			l.child if l.type == 'PREDICATE'\
			else l.child[0].child if l.type == 'NEG'\
			else l.child if l.type == 'FUNCTION'\
			else [l])]
		while len(stack) > 0:
			n = stack.pop()
			if n.type == 'VARIABLE' and n.data == x:
				tmp_t = deepcopy(t)
				n.type = tmp_t.type
				n.data = tmp_t.data
				n.child = tmp_t.child
			if n.type == 'FUNCTION':
				stack.extend(n.child)
	return ret

def get_clauses(node, used_variables=set()):
	# go down to matrix
	# TODO error check to reject unbound variable
	matrix = node
	while matrix.type == 'FORALL' or matrix.type == 'EXISTS':
		matrix = matrix.right
	# collect clauses as list of list of predicate

	clauses = []
	def add_clause(node):
		# find literal and variables
		literals = []
		if node.type != 'LOR':
			literals.append(node)
		else:
			while node.type == 'LOR':
				literals.append(node.left)
				node = node.right
			literals.append(node)
		atomics = [
			p if p.type == 'PREDICATE' else p.left
			for p in literals
		]
		variables = find_variables(node)
		# resolve variable collision
		var_dict = resolve_variable_collisions(
			variables, used_variables)
		used_variables.update(var_dict.keys())
		clauses.append(_alpha_conversion(literals, var_dict))

	if matrix.type != 'LAND':
		add_clause(matrix)
	else:
		while matrix.type == 'LAND':
			add_clause(matrix.left)
			matrix = matrix.right
		add_clause(matrix)
	return clauses

def _unify(C1, C2):
	if len(C1.ancestors.intersection(C2.ancestors)) > 0:
		return None
	opposite = lambda L1, L2:\
		L1.type == 'PREDICATE' and\
		L2.type == 'NEG' and\
		L1.data == L2.child[0].data
	literals = [
		(l.child[0], m) if l.type == 'NEG' else (l, m.child[0])
		for l in C1.clause for m in C2.clause\
		if opposite(l, m) or opposite(m, l)
	]
	if len(literals) != 1:
		return None

	L1, L2 = map(deepcopy, literals[0])
	if len(L1.child) != len(L2.child):
		return None
	unifier = dict()
	substitution = []
	stack = list(zip(L1.child, L2.child))

	def replace(n, x):
		n1.type = x.type
		n1.data = x.data
		n1.child = x.child
	while stack:
		n1, n2 = stack.pop()
		if n1.type == 'VARIABLE' and n1.data in unifier:
			replace(n2, deepcopy(unifier[n1.data]))
		if n2.type == 'VARIABLE' and n2.data in unifier:
			replace(n1, deepcopy(unifier[n2.data]))

		if n1.type == 'CONSTANT' and n2.type == 'CONSTANT' and\
			n1.data == n2.data:
			pass
		elif n1.type == 'VARIABLE' and n2.type == 'VARIABLE' and\
			n1.data != n2.data:
			if n1.data < n2.data:
				unifier[n2.data] = deepcopy(n1)
				substitution.append((n2.data, n1))
				n2.data = n1.data
			else:
				unifier[n1.data] = deepcopy(n2)
				substitution.append((n1.data, n2))
				n1.data = n2.data
		elif n1.type == 'VARIABLE':
			u = deepcopy(n2)
			for x, t in substitution:
				_substitute([u], x, t) # HACK
			unifier[n1.data] = u
			substitution.append((n1.data, u))
			replace(n1, deepcopy(u))
		elif n2.type == 'VARIABLE':
			u = deepcopy(n1)
			for x, t in substitution:
				_substitute([u], x, t) # HACK
			unifier[n2.data] = u
			substitution.append((n2.data, u))
			replace(n2, deepcopy(u))
		elif n1.type == 'FUNCTION' and n2.type == 'FUNCTION' and\
			n1.data == n2.data: # TODO: more conditions
			stack.extend(zip(n1.child, n2.child))
		else:
			return None

	clause = []
	predicate_name = L1.data if L1.type == 'PREDICATE' else L2.data
	for literal in C1.clause + C2.clause:
		atomic = literal if literal.type == 'PREDICATE' else\
			literal.child[0]
		if atomic.data != predicate_name:
			clause.append(deepcopy(literal))
	clause = sorted(clause,
		key=lambda l: l.data if l.type == 'PREDICATE' else\
		l.child[0].data)

	for x, t in substitution:
		_substitute(clause, x, t)

	return RNode(clause, C1, C2, substitution)

def build_resolution_tree(clauses):
	clause_set = set(map(RNode, clauses))
	while True:
		new_clause = set()
		for C1, C2 in combinations(clause_set, 2):
			C = _unify(C1, C2)
			if C is None:
				continue
			if len(C.clause) == 0:
				return C
			new_clause.add(C)
		if len(new_clause) == 0:
			break
		clause_set.update(new_clause)
	return None