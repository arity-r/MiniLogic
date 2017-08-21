import re
from copy import deepcopy
from ast import Node
from ast import ast_to_string, find_constants, find_functions
from ast import resolve_variable_collisions
from petrick import petrick_method

def eliminate_implication_and_iff(node):
	if node.type == 'IMPLIES':
		node.type = 'LOR'
		node.data = 'or'
		node.left = Node('NEG', 'neg', [node.left])

	elif node.type == 'IFF':
		left = node.left
		right = node.right
		leftcp = deepcopy(left)
		rightcp = deepcopy(right)
		node.type = 'LAND'
		node.data = 'and'
		node.left = Node('LOR', 'or', (left, right))
		node.right = Node('LOR', 'or', (
			Node('NEG', 'neg', [leftcp]),
			Node('NEG', 'neg', [rightcp])
			)
		)

	if node.type == 'EXISTS' or node.type == 'FORALL':
		eliminate_implication_and_iff(node.right)

	elif node.type != 'PREDICATE':
		for c in node.child:
			eliminate_implication_and_iff(c)

	return node

def move_negation(node, parent=None):
	node_node = node if parent == None else None
	if node.type == 'NEG':
		child = node.child[0]
		if child.type == 'LOR' or child.type == 'LAND':
			left = child.left
			right = child.right
			node.type = 'LOR' if child.type == 'LAND' else 'LAND'
			node.data = 'or' if node.type == 'LOR' else 'and'
			node.left = Node('NEG', 'neg', [left])
			node.right = Node('NEG', 'neg', [right])

		elif child.type == 'EXISTS' or child.type == 'FORALL':
			variable = child.left
			formula = child.right
			node.type = 'EXISTS' if child.type == 'FORALL' else 'FORALL'
			node.data = 'exists' if node.type == 'EXISTS' else 'forall'
			node.left = variable
			node.right = Node('NEG', 'neg', [formula])

		elif child.type == 'NEG':
			if parent:
				index = parent.child.index(node)
				parent.child[index] = child.child[0]
			top_node = move_negation(child.child[0], parent)
			if top_node: node_node = top_node
			return top_node

	if node.type == 'EXISTS' or node.type == 'FORALL':
		move_negation(node.right, node)
	elif node.type != 'PREDICATE':
		for c in node.child:
			move_negation(c, node)

	return node_node

def standarize_variables(node):
	used_variables = set()
	variable_map = dict()
	variable_map_from = dict()
	stack = [(node, 0)]
	while len(stack) > 0:
		n, i = stack.pop()
		if n.type in ('EXISTS', 'FORALL') and i == 0:
			v = n.left.data
			v_map = resolve_variable_collisions(
				{v}, used_variables)
			used_variables.add(v)
			used_variables.add(v_map[v])
			prev_v = variable_map.get(v, None)
			variable_map[v] = v_map[v]
			variable_map_from[v_map[v]] = prev_v
			#n.left.data = v_map[v]
			stack.append((n, 1))
			stack.append((n.right, 0))
		elif n.type in ('EXISTS', 'FORALL') and i == 1:
			v = n.left.data
			n.left.data = variable_map[v]
			variable_map[v] = variable_map_from[variable_map[v]]
		elif n.type == 'VARIABLE' and n.data in variable_map:
			n.data = variable_map[n.data]
		elif n.child:
			stack.extend([(c, 0) for c in reversed(n.child)])
	return node

#TODO: use global used alphabet set
def eliminate_existential_quantifiers(node):
	constants = find_constants(node)
	functions = find_functions(node)
	skolem_map = dict()

	node_stack = [(node, None, 0)]
	variable_stack = []
	while len(node_stack) > 0:
		n, p, i = node_stack.pop()
		if n.type == 'FORALL' and i == 0:
			variable_stack.append(n.left.data)
			node_stack.append((n, p, 1))
			if n.child:
				node_stack.extend([(c, n, 0) for c in n.child])
		elif n.type == 'FORALL' and i == 1:
			variable_stack.pop()
		elif n.type == 'EXISTS':
			if len(variable_stack) == 0:
				alphs = set('abcde').difference(constants)
				if len(alphs) == 0:
					raise RuntimeError('too many constants')
				alph = sorted(list(alphs))[0]
				constants.add(alph)
				skolem_map[n.left.data] = Node('CONSTANT', alph)
			else:
				alphs = set('fghij').difference(functions)
				if len(alphs) == 0:
					raise RuntimeError('too many functions')
				alph = sorted(list(alphs))[0]
				functions.add(alph)
				skolem_map[n.left.data] = Node('FUNCTION', alph,
					[Node('VARIABLE', v) for v in variable_stack])
			if p == None:
				node = n.right
			else:
				idx = p.child.index(n)
				p.child[idx] = n.right
			node_stack.append((n.right, p, 0))
		elif n.type == 'VARIABLE' and n.data in skolem_map:
			idx = p.child.index(n)
			p.child[idx] = deepcopy(skolem_map[n.data])
		elif n.child:
			node_stack.extend([(c, n, 0) 
				for c in reversed(n.child)])
		pass
	return node

def move_quantifiers(node):
	node = node
	node_stack = [(node, None)]
	quantifier_list = []
	while len(node_stack) > 0:
		n, p = node_stack.pop()
		if n.type == 'FORALL' or n.type == 'EXISTS':
			quantifier_list.append(Node(n.type, n.data, [n.left]))
			if p:
				index = p.child.index(n)
				p.child[index] = n.right
			else:
				node = n.right
			node_stack.append((n.right, n))
		elif n.child:
			node_stack.extend([(c, n) for c in n.child])

	if len(quantifier_list) == 0:
		return node

	quantifier_list.sort(key=lambda n: n.left.data)
	quantifiers = None
	current_quantifier = None
	while len(quantifier_list) > 0:
		quantifier = quantifier_list.pop(0)
		if not quantifiers:
			quantifiers = current_quantifier = quantifier
		else:
			current_quantifier.right = quantifier
			current_quantifier = quantifier
	current_quantifier.right = node

	return quantifiers

def conjunctive_normal_form(node):
	matrix_parent, matrix = None, node
	while matrix.type == 'FORALL' or matrix.type == 'EXISTS':
		matrix_parent, matrix = matrix, matrix.right
	matrix_tmp = deepcopy(matrix)

	str_to_predicate = {}
	stack = [matrix_tmp]
	while stack:
		n = stack.pop()
		if n.type == 'PREDICATE':
			ast_str = ast_to_string(n)
			str_to_predicate[ast_str] = deepcopy(n)
			n.data = ast_str
			n.child = []
		elif n.child:
			stack.extend(n.child)

	matrix_tmp = petrick_method(matrix_tmp)

	stack = [matrix_tmp]
	while len(stack) > 0:
		n = stack.pop()
		if n.type == 'PREDICATE':
			m = str_to_predicate[n.data]
			n.data = m.data
			n.child = m.child
		elif n.child:
			stack.extend(n.child)

	if matrix_parent:
		matrix_parent.right = matrix_tmp
	else:
		node = matrix_tmp

	return node

def wff_to_cnf(node, dump_func=None):
	if dump_func: print(dump_func(node))
	node = eliminate_implication_and_iff(node)
	if dump_func: print(dump_func(node))
	node = move_negation(node)
	if dump_func: print(dump_func(node))
	node = standarize_variables(node)
	if dump_func: print(dump_func(node))
	node = eliminate_existential_quantifiers(node)
	if dump_func: print(dump_func(node))
	node = move_quantifiers(node)
	if dump_func: print(dump_func(node))
	node = conjunctive_normal_form(node)
	if dump_func: print(dump_func(node))
	return node
