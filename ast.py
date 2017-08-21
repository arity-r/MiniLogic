import re

class Node:
	def __init__(self, type, data, child=None):
		self.type = type
		self.data = data
		self.child = child

	@property
	def left(self):
		return self.child[0]

	@property
	def right(self):
		return self.child[1]

	@left.setter
	def left(self, value):
		if not self.child:
			self.child = []
		if len(self.child) == 0:
			self.child.append(value)
		else:
			self.child[0] = value

	@right.setter
	def right(self, value):
		if not self.child:
			self.child = []
		if len(self.child) == 0:
			self.child.append(None)
		if len(self.child) == 1:
			self.child.append(value)
		else:
			self.child[1] = value

	def __str__(self):
		return 'AstNode(' +\
		str(self.type) + ', ' + str(self.data) + ')'

	def __repr__(self):
		return str(self)

	def __deepcopy__(self, memo):
		copy = Node(self.type, self.data)
		if self.child:
			copy.child = list(c.__deepcopy__(memo) for c in self.child)
		return copy

def find_variables(node):
	variables = set()
	stack = [node]
	while len(stack) > 0:
		n = stack.pop()
		if n.type == 'VARIABLE':
			variables.add(n.data)
		elif n.child:
			stack.extend(n.child)
	return variables

def find_constants(node):
	variables = set()
	stack = [node]
	while len(stack) > 0:
		n = stack.pop()
		if n.type == 'CONSTANT':
			variables.add(n.data)
		elif n.child:
			stack.extend(n.child)
	return variables

def find_functions(node):
	variables = set()
	stack = [node]
	while len(stack) > 0:
		n = stack.pop()
		if n.type == 'FUNCTION':
			variables.add(n.data)
		if n.child:
			stack.extend(n.child)
	return variables

def resolve_variable_collisions(variables, used_variables):
	var_dict = dict((v, v)
		for v in variables.difference(used_variables))
	for v in variables.intersection(used_variables):
		m = re.match(r'(?P<base>.)(?P<suffix>[0-9]*)', v)
		assert(m)
		base, suffix = m.group('base'), m.group('suffix')
		suffix = int(suffix) if len(suffix) > 0 else 1
		while '%s%d'%(base, suffix) in used_variables:
			suffix += 1
		var_dict[v] = '%s%d'%(base, suffix)
	return var_dict	

def ast_to_string(node):
	op_order = {
	'LOR'    : 1,
	'LAND'   : 2,
	'NEG'    : 3,
	'EXISTS' : 3,
	'FORALL' : 3,
	'IMPLIES': 0,
	'IFF'    : 0
	}
	if node.type in ('LOR', 'LAND', 'IMPLIES', 'IFF'):
		left_needs_par =\
		op_order[node.type] > op_order.get(node.left.type, 4)
		right_needs_par =\
		op_order[node.type] > op_order.get(node.right.type, 4)
		
		left = ast_to_string(node.left)
		if left_needs_par:
			left = '(' + left + ')'
		right = ast_to_string(node.right)
		if right_needs_par:
			right = '(' + right + ')'
		
		return '%s %s %s'%(left, node.data, right)
	
	elif node.type in ('NEG',):
		child_needs_par =\
		op_order[node.type] > op_order.get(node.child[0].type, 4)
			
		child = ast_to_string(node.child[0])
		if child_needs_par:
			child = '(' + child + ')'
			
		return '%s %s'%(node.data, child)

	elif node.type in ('EXISTS', 'FORALL'):
		right_needs_par =\
		op_order[node.type] > op_order.get(node.right.type, 4)

		right = ast_to_string(node.right)
		if right_needs_par:
			right = '[' + right + ']'

		left = ast_to_string(node.left)

		return '(' + node.data + ' ' + left + ')' + right

	elif node.type in ('PREDICATE', 'FUNCTION'):
		var_needs_par = node.child and len(node.child) > 0
		variables = '(' +\
			', '.join(map(ast_to_string, node.child)) +\
		')' if var_needs_par else ''
		return node.data + variables

	elif node.type in ('VARIABLE', 'CONSTANT'):
		return node.data

	else:
		raise Exception('error: no type')