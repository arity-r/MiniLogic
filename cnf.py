from copy import deepcopy
from ast import Node, ast_to_string
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
	root_node = node if parent == None else None
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
			if top_node: root_node = top_node
			return top_node

	if node.type == 'EXISTS' or node.type == 'FORALL':
		move_negation(node.right, node)
	elif node.type != 'PREDICATE':
		for c in node.child:
			move_negation(c, node)

	return root_node

def standarize_variables(node, var_stack=[], var_map={}):
	if node.type == 'EXISTS' or node.type == 'FORALL':
		var_str = node.left.data
		if var_str in var_stack:
			n_found = 1
			var_str_tmp = '%s%d' % (var_str, n_found)
			while var_str_tmp in var_stack:
				n_found += 1
				var_str_tmp = '%s%d' % (var_str, n_found)
			var_str = var_str_tmp
		var_stack.append(var_str)
		var_tmp = var_map.get(node.left.data, None)
		var_map[node.left.data] = var_str
		node.left.data = var_str
		standarize_variables(node.right, var_stack, var_map)
	elif node.type == 'VARIABLE':
		node.data = var_map.get(node.data, node.data)
	elif node.child:
		for c in node.child:
			standarize_variables(c, var_stack)

	if node.type == 'EXISTS' or node.type == 'FORALL':
		var_stack.pop()
		if var_tmp:
			var_map[node.left.data] = var_tmp
		else:
			del var_map[node.left.data]

	return node

def _find_alphabet_set(node, const_alphs=set(), func_alphs=set()):
	if node.type == 'CONST':
		const_alphs.add(node.data)
	if node.type == 'FUNCTION':
		func_alphs.add(node.data)
	if node.child:
		for c in node.child:
			_find_alphabet_set(c, const_alphs, func_alphs)
	return (const_alphs, func_alphs)

def eliminate_existential_quantifiers(node, parent=None,
	vars=[], const_alphs=None, func_alphs=None, skolem_map={}):

	root_node = node if not parent else None

	if not const_alphs or not func_alphs: # called by root
		const_alphs, func_alphs = _find_alphabet_set(node)

	if node.type == 'FORALL':
		vars.append(node.left.data)
		vars.sort()
		eliminate_existential_quantifiers(
			node.right, node,
			vars, const_alphs, func_alphs, skolem_map
		)

	elif node.type == 'EXISTS':
		if len(vars) == 0:
			alphs = sorted(list(set('abcde').difference(const_alphs)))
			if len(alphs) == 0: raise RuntimeError('too many constants')
			skolem_map[node.left.data] = Node('CONSTANT', alphs[0])
			const_alphs.add(alphs[0])
		else:
			alphs = sorted(list(set('fghij').difference(func_alphs)))
			if len(alphs) == 0: raise RuntimeError('too many functions')
			skolem_map[node.left.data] = Node('FUNCTION', alphs[0])
			skolem_map[node.left.data].child = [Node('VARIABLE', x) for x in vars]
			func_alphs.add(alphs[0])

		right = node.right
		if parent:
			index = parent.child.index(node)
			parent.child[index] = right

		top_node = eliminate_existential_quantifiers(
			right, parent,
			vars, const_alphs, func_alphs, skolem_map
		)
		if top_node: root_node = top_node
		#return root_node

	elif node.type == 'VARIABLE' and node.data in skolem_map:
		parent.child[parent.child.index(node)] = deepcopy(skolem_map[node.data])

	elif node.child:
		for c in node.child:
			eliminate_existential_quantifiers(
				c, node,
				vars, const_alphs, func_alphs, skolem_map
			)

	if node.type == 'FORALL':
		vars.remove(node.left.data)

	return root_node

def move_quantifiers(node):
	root = node
	node_stack = [(None, node)]
	quantifier_list = []
	while len(node_stack) > 0:
		parent, node = node_stack.pop()
		if node.type == 'FORALL' or node.type == 'EXISTS':
			quantifier_list.append(Node(node.type, node.data, [node.left]))
			if parent:
				index = parent.child.index(node)
				parent.child[index] = node.right
			else:
				root = node.right
			node_stack.append((parent, node.right))
		elif node.child:
			node_stack.extend([(node, c) for c in node.child])

	if len(quantifier_list) == 0:
		return root

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
	current_quantifier.right = root

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
