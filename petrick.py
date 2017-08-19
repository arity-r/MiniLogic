from itertools import combinations, product
import numpy as np
from ast import Node

def _find_predicates(node):
	predicates = set()
	stack = [node]
	while stack:
		node = stack.pop()
		if node.type == 'PREDICATE':
			predicates.add(node.data)
		elif node.child:
			stack.extend(node.child)
	return sorted(list(predicates))

def _value_of(node, assignment):
	if node.type == 'LOR':
		return _value_of(node.left, assignment) or\
		_value_of(node.right, assignment)
	elif node.type == 'LAND':
		return _value_of(node.left, assignment) and\
		_value_of(node.right, assignment)
	elif node.type == 'NEG':
		return not _value_of(node.child[0], assignment)
	elif node.type == 'PREDICATE':
		if not node.data in assignment:
			raise RuntimeError('predicate %s not in assignment'%node.data)
		return assignment[node.data]

def _build_truth_table(node):
	predicates = tuple(_find_predicates(node))
	truth_table = dict()
	for bin_pattern in product(*(((0,1),)*len(predicates))):
		assignment = dict(zip(predicates, bin_pattern))
		value = _value_of(node, assignment)
		truth_table[bin_pattern] = int(value)
	return predicates, truth_table

def _build_cnf_tree(predicates, values):
	def build_or_tree(assignment):
		if len(values) == 0: return None
		if len(assignment) == 1:
			a = assignment[0]
			node = Node('PREDICATE', a[0])
			if a[1] == '1':
				node = Node('NEG', 'neg', [node])
			return node
		assignment = list(assignment)
		root = node = Node('LOR', 'or')
		while len(assignment) > 1:
			a = assignment.pop(0)
			node.left = Node('PREDICATE', a[0])
			if a[1] == '1':
				node.left = Node('NEG', 'neg', [node.left])
			if len(assignment) > 1:
				node.right = Node('LOR', 'or')
				node = node.right
		a = assignment[0]
		node.right = Node('PREDICATE', a[0])
		if a[1] == '1':
			node.right = Node('NEG', 'neg', [node.right])
		return root

	assignments = list(
		tuple(
			filter(lambda t: t[1] != '-', zip(predicates, value))
			)
		for value in values
		)
	assignments.sort()

	if len(assignments) == 0: return None
	elif len(assignments) == 1:
		return build_or_tree(assignments[0])
	root = node = Node('LAND', 'and')
	while len(assignments) > 1:
		node.left = build_or_tree(assignments.pop(0))
		if len(assignments) > 1:
			node.right = Node('LAND', 'and')
			node = node.right
	node.right = build_or_tree(assignments[0])
	return root

def petrick_method(node):
	predicates, truth_table = _build_truth_table(node)
	max_terms = [
		''.join(map(str, k)) for k, v in truth_table.items()
		if v == 0
	]
	implicants = list(max_terms)
	prime_implicants = set()
	combine_pattern =\
		lambda s: ''.join(map(
			lambda t: t[0] if t[0] == t[1] else '-',
			zip(s[0], s[1])
			))
	valid_combination = lambda s: sum(map(
		lambda t: t[0] != t[1], zip(s[0], s[1]))
	) == 1

	while len(implicants) > 0:
		next_implicants = list(
			map(combine_pattern,
				filter(
					valid_combination,
					combinations(implicants, 2)
					)
				)
			)
		prime_implicants.update([i for i in implicants
			if not any(map(
				lambda j: valid_combination((i, j)),
				next_implicants))
			])
		implicants = next_implicants

	prime_implicants = sorted(list(prime_implicants))
	pi_chart = np.zeros(
		(len(prime_implicants), len(max_terms)),
		dtype=int
		)
	for (i, pi), (j, mt) in product(
		enumerate(prime_implicants),
		enumerate(max_terms)):

		if all(map(
			lambda t: t[0]=='-' or t[0]==t[1],
			zip(pi, mt))):
			pi_chart[i, j] = 1
	
	expression = [
	frozenset([prime_implicants[i] for i in pi_chart[:,j].nonzero()[0]])
	for j in range(len(max_terms))
	]
	reduced_expression = set(frozenset((t,)) for t in expression[0])
	for term in expression[1:]:
		reduced_expression = set(
			[e.union((f,)) for e, f in
			product(reduced_expression, term)])
		# apply X + XY = X
		reduced_expression = set(filter(
			lambda s: not any([s.issuperset(t) for t in reduced_expression if s != t]),
			reduced_expression
			))

	expression = reduced_expression
	expression = [tuple(sorted(list(t))) for t in expression]
	expression.sort(key=lambda t: (len(t), t))
	values = expression[0]

	return _build_cnf_tree(predicates, values)
