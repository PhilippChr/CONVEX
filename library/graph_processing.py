import networkx as nx
# import sys

# library
# sys.path.append("library")
# import string_conversions as string
# import wikidata as wd

# data
# used to distinguish between multiple predicate nodes with same label - next index for predicate
predicate_nodes = {}
qualifier_predicate_nodes = {}

#####################################################
###		Graphs
#####################################################

# def complete_statement(statement, offline=False):
# 	if not statement['entity'].get('label'):
# 		try:
# 			statement['entity']['label'] = wd.wikidata_id_to_label(statement['entity']['id'])
# 		except Exception as e:
# 			print(statement)
# 			print(str(e))
	
# 	if not statement['object'].get('label'):
# 		statement['object']['label'] = wd.wikidata_id_to_label(statement['object']['id'])

# 	if not statement['predicate'].get('label'):
# 		statement['predicate']['label'] = wd.wikidata_id_to_label(statement['predicate']['id'])

# 	# if there are no qualifiers in the statement, nothing to do
# 	if not statement.get('qualifiers'):
# 		return statement

# 	for qualifier in statement['qualifiers']:
# 		if not qualifier['qualifier_predicate'].get('label'):
# 			qualifier['qualifier_predicate']['label'] = wd.wikidata_id_to_label(qualifier['qualifier_predicate']['id'])

# 		if not qualifier['qualifier_object'].get('label'):
# 			qualifier['qualifier_object']['label'] = wd.wikidata_id_to_label(qualifier['qualifier_object']['id'])
# 	return statement


# one element of the answer_statements is a dictionary with 'entity', 'object', 'predicate' and 'qualifiers' attributes
# see statement_structure.json for details
def expand_context_with_statements(context, statements, turn = 1, qa=False):
	if not context:
		context = nx.Graph()

	# print statements
	for statement in statements:
		# add the entity and object node
		if not statement['entity']['id'] in context:
			context.add_node(statement['entity']['id'], type='entity', turn=turn, qa=qa)
		if not statement['object']['id'] in context:
			context.add_node(statement['object']['id'], type='entity', turn=turn, qa=qa)

		# get current index of predicate used
		if not predicate_nodes.get(statement['predicate']['id']):
			# the predicate did not occur yet => index 0 and new entry
			predicate_nodes[statement['predicate']['id']] = 1
			predicate_index = 0
		else:
			# the predicate already occured => fetch the next index available and increase the saved one
			predicate_index = predicate_nodes[statement['predicate']['id']]
			predicate_nodes[statement['predicate']['id']] += 1
		
		# add the predicate node
		predicate_node_id = (statement['predicate']['id'] + "-" + str(predicate_index))
		context.add_node(predicate_node_id, type='predicate', turn=turn)

		# add the two edges (entity->predicate->object)
		context.add_edge(statement['entity']['id'], predicate_node_id)
		context.add_edge(predicate_node_id, statement['object']['id'])

		# if there were qualifiers occuring in the statement
		if statement.get('qualifiers'):
			for qualifier_statement in statement['qualifiers']:
				# add the qualifier_statment object
				if not qualifier_statement['qualifier_object']['id'] in context:
					context.add_node(qualifier_statement['qualifier_object']['id'], type='entity', turn=turn, qa=qa)

				# get current index of qualifier_predicate used
				if not qualifier_predicate_nodes.get(qualifier_statement['qualifier_predicate']['id']):
					# the qualifier_predicate did not occur yet => index 0 and new entry
					qualifier_predicate_nodes[qualifier_statement['qualifier_predicate']['id']] = 1
					predicate_index = 0
				else:
					# the qualifier_predicate already occured => fetch the next index available and increase the saved one
					predicate_index = qualifier_predicate_nodes[qualifier_statement['qualifier_predicate']['id']]
					qualifier_predicate_nodes[qualifier_statement['qualifier_predicate']['id']] += 1

				# add the qualifier_predicate
				qualifier_predicate_node_id = qualifier_statement['qualifier_predicate']['id'] + "-" + str(predicate_index)
				context.add_node(qualifier_predicate_node_id, type='qualifier_predicate', turn=turn)

				# add the two edges (qualifier_entity->qualifier_predicate->qualifier_object)
				context.add_edge(predicate_node_id, qualifier_predicate_node_id)
				context.add_edge(qualifier_predicate_node_id, qualifier_statement['qualifier_object']['id'])
	return context

# one element of the answer_statements is a dictionary with 'entity', 'object', 'predicate' and 'qualifiers' attributes
# see statement_structure.json for details
def expand_context_with_frontier(context, frontier, frontier_statement, turn = 1):
	if not context:
		context = nx.Graph()
	# complete the statement with labels
	# statement = complete_statement(frontier_statement, True)
	statement = frontier_statement

	# add the entity and object node
	if not statement['entity']['id'] in context:
		context.add_node(statement['entity']['id'], type='entity', turn=turn, qa=False)
	if not statement['object']['id'] in context:
		context.add_node(statement['object']['id'], type='entity', turn=turn, qa=False)

	# get current index of predicate used
	if not predicate_nodes.get(statement['predicate']['id']):
		# the predicate did not occur yet => index 0 and new entry
		predicate_nodes[statement['predicate']['id']] = 1
		predicate_index = 0
	else:
		# the predicate already occured => fetch the next index available and increase the saved one
		predicate_index = predicate_nodes[statement['predicate']['id']]
		predicate_nodes[statement['predicate']['id']] += 1
	
	# add the predicate node
	predicate_node_id = (statement['predicate']['id'] + "-" + str(predicate_index))
	context.add_node(predicate_node_id, type='predicate', turn=turn)

	# if the frontier is the predicate node, set the label as frontier
	if frontier == statement['predicate']['id']:
		frontier = predicate_node_id

	# add the two edges (entity->predicate->object)
	context.add_edge(statement['entity']['id'], predicate_node_id)
	context.add_edge(predicate_node_id, statement['object']['id'])

	# if there were qualifiers occuring in the statement
	if statement.get('qualifiers'):
		for qualifier_statement in statement['qualifiers']:
			# add the qualfier_statment object
			if not qualifier_statement['qualifier_object']['id'] in context:
				context.add_node(qualifier_statement['qualifier_object']['id'], type='entity', turn=turn, qa=False)

			# get current index of qualifier_predicate used
			if not qualifier_predicate_nodes.get(qualifier_statement['qualifier_predicate']['id']):
				# the qualifier_predicate did not occur yet => index 0 and new entry
				qualifier_predicate_nodes[qualifier_statement['qualifier_predicate']['id']] = 1
				predicate_index = 0
			else:
				# the qualifier_predicate already occured => fetch the next index available and increase the saved one
				predicate_index = qualifier_predicate_nodes[qualifier_statement['qualifier_predicate']['id']]
				qualifier_predicate_nodes[qualifier_statement['qualifier_predicate']['id']] += 1

			# add the qualifier_predicate
			qualifier_predicate_node_id = qualifier_statement['qualifier_predicate']['id'] + "-" + str(predicate_index)
			context.add_node(qualifier_predicate_node_id, type='qualifier_predicate', turn=turn)

			# if the frontier is the predicate node, set the label as frontier
			if frontier == qualifier_statement['qualifier_predicate']['id']:
				frontier = qualifier_predicate_node_id

			# add the two edges (qualifier_entity->qualifier_predicate->qualifier_object)
			context.add_edge(predicate_node_id, qualifier_predicate_node_id)
			context.add_edge(qualifier_predicate_node_id, qualifier_statement['qualifier_object']['id'])

	return context, frontier


# expand the context by the top candidates
def expand_context_with_candidates(graph, candidates, turn=1):
	statements = []
	for candidate in candidates:
		statements.append(candidate['statement'])

	graph = expand_context_with_statements(graph, statements, turn)
	return graph

# set all nodes as qa nodes in the given graph
def set_all_nodes_as_qa_nodes(graph):
	for node in list(graph.nodes(data=True)):
		node[1]['qa'] = True

# return a list of all entity nodes which where question words or answers of the graph
def get_all_qa_nodes(graph):
	entity_nodes = [node for node in list(graph.nodes(data=True)) if node[1]['type'] == 'entity' and node[1]['qa']]
	return entity_nodes


# return a list of all entity nodes which could be answers
def get_all_answer_candidates(graph):
	entity_nodes = [node[0] for node in list(graph.nodes(data=True)) if node[1]['type'] == 'entity' and not node[1]['qa']]
	if entity_nodes:
		return entity_nodes
	else:
		return get_all_answer_candidates_with_qa(graph)

# return a list of all entity nodes which could be answers
def get_all_answer_candidates_with_qa(graph):
	entity_nodes = [node[0] for node in list(graph.nodes(data=True)) if node[1]['type'] == 'entity']
	return entity_nodes

def get_distance(graph, answer_candidate, entity_node):
	return float(nx.shortest_path_length(graph, source=answer_candidate, target=entity_node) + 1.0)

# graph to file
def write_graph(graph, file_path):
	nx.write_gpickle(graph, file_path)

# load graph from file
def load_graph(file_path):
	return nx.read_gpickle(file_path)

