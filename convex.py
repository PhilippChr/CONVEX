# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# modules
import sys
import json
import warnings
import requests
import time

# library 
sys.path.append("library")
import string_conversions as string
import graph_processing as gp
import glove_similarity as spacy 
import wikidata as wd
import telegram_api as telegram

#####################################################
###		Candidate queue creation
#####################################################

# fetching data from offline wikidata dump
def build_candidate_priority_queue_one_entity(entity_id):
	candidate_priority_queue_one_entity = []
	statements = wd.get_all_statements_of_entity(entity_id)
	# error handling
	if not statements:
		return []
	for statement in statements:
		# entity is the object of the statement
		if entity_id == statement['object']['id']:
			entity_label = wd.wikidata_id_to_label(statement['entity']['id'])
			predicate_label = wd.wikidata_id_to_label(statement['predicate']['id'])
			candidate_priority_queue_one_entity.append({'type': 'predicate', 'predicate': statement['predicate']['id'], 'label': predicate_label,  'statement': statement})
			candidate_priority_queue_one_entity.append({'type': 'entity', 'entity': statement['entity']['id'], 'label': entity_label, 'statement': statement})
		# entity is the subject of the statement
		else:
			object_label = wd.wikidata_id_to_label(statement['object']['id'])
			predicate_label = wd.wikidata_id_to_label(statement['predicate']['id'])
			candidate_priority_queue_one_entity.append({'type': 'predicate', 'predicate': statement['predicate']['id'], 'label': predicate_label,  'statement': statement})
			candidate_priority_queue_one_entity.append({'type': 'entity', 'entity': statement['object']['id'], 'label': object_label, 'statement': statement})
		# include the qualifiers
		if statement['qualifiers']:
			for qualifier in statement['qualifiers']:
				qualifier_object_label = wd.wikidata_id_to_label(qualifier['qualifier_object']['id'])
				qualifier_predicate_label = wd.wikidata_id_to_label(qualifier['qualifier_predicate']['id'])
				candidate_priority_queue_one_entity.append({'type': 'qualifier_object', 'qualifier_object': qualifier['qualifier_object']['id'], 'label': qualifier_object_label, 'statement': statement})
				candidate_priority_queue_one_entity.append({'type': 'qualifier_predicate', 'qualifier_predicate': qualifier['qualifier_predicate']['id'], 'label': qualifier_predicate_label,  'statement': statement})
	return candidate_priority_queue_one_entity

# fetch all statements of an entity
def build_candidate_queue(graph):
	candidate_priority_queue = []
	for node in list(graph.nodes(data=True)):
		#do not expand predicates
		if node[1]['type'] == 'predicate':
			continue
		res = build_candidate_priority_queue_one_entity(node[0])
		candidate_priority_queue = res + candidate_priority_queue
	return candidate_priority_queue

#####################################################
###		Other functions
#####################################################

# create the question words list
def create_question_words_list(question):
	question_words = []
	# remove symbols
	question = question.replace(',', '').replace('!', '').replace('?', '').replace('.', '').replace('\'', '').replace('"', '').replace(':','').replace('’', '')
	# expand the question by whitespaces to be able to find the stopwords
	question = (" " + question + " ").lower()
	# replace w-words by type asked for
	question = question.replace(" where ", " location ")
	question = question.replace(" wheres ", " location ")
	question = question.replace(" when ", " date ")
	question = question.replace(" whens ", " date ")
	question = question.replace(" who ", " person ")
	question = question.replace(" whos ", " person ")
	question = question.replace(" why ", " cause ")
	question = question.replace(" whys ", " cause ")
	# remove stopwords
	for stopword in stopwords:
		question = question.replace(" "+stopword+" ", " ")
	# remove remaining s from plural or possesive expressions
	question = question.replace(' s ', ' ')
	# remove whitespaces
	while "  " in question:
		question = question.replace("  ", " ")
	# remove the whitespace(s) at the front and end
	question = question.strip()
	# get all question words
	question_words += question.split(" ")
	return question_words


# remove all unnecessary words of the question to avoid noise in the similarity-computation
def shorten_question_for_predicate_similarity(question, entity_spot):
	# remove the spot of the entity
	question = question.replace(entity_spot, "")
	# remove symbols
	question = question.replace(',', '').replace('!', '').replace('?', '').replace('.', '').replace("'", '').replace('"', '').replace(':','').replace('’', '')
	# expand the question by whitespaces to be able to find the stopwords
	question = (" " + question + " ").lower()
	# remove stopwords
	for stopword in stopwords:
		question = question.replace(" "+stopword+" ", " ")
	# replace w words, but still keep the information in the question
	question = question.replace(" where ", " location ")
	question = question.replace(" wheres ", " location ")
	question = question.replace(" when ", " date ")
	question = question.replace(" whens ", " date ")
	question = question.replace(" who ", " person ")
	question = question.replace(" whos ", " person ")
	question = question.replace(" why ", " cause ")
	question = question.replace(" whys ", " cause ")
	# wikidata does not give the accuracy of the date (year, month, ...)
	question = question.replace('year', 'date')
	# remove remaining s from plural or possesive expressions
	question = question.replace(' s ', ' ')
	# remove whitespaces
	while "  " in question:
		question = question.replace("  ", " ")
	return question.strip()
	
# return all found entities 
def tagme_get_all_entities(utterance, tagmeToken):
	request_successfull = False
	while not request_successfull:
		try:
			results = json.loads(requests.get('https://tagme.d4science.org/tagme/tag?lang=en&gcube-token=' + tagmeToken + '&text=' + utterance).content)
			request_successfull = True
		except:
			print utterance
			time.sleep(5)
	entities = []
	for result in results["annotations"]:
		try:
			wikidata_ids = wd.name_to_wikidata_ids(result['title'])
		except:
			continue
		for wikidata_id in wikidata_ids:
			entities.append({'title': result['title'], 'spot': result['spot'], 'link_probability': result['link_probability'], 'wikidata_id': wikidata_id})
	return entities

def question_is_existential(question):
	existential_keywords	= ['is', 'are', 'was', 'were', 'am', 'be', 'being', 'been', 'did', 'do', 'does', 'done', 'doing', 'has', 'have', 'had', 'having']
	try:
		lowercase_question 	= question.lower()
	except:
		return False
	for keyword in existential_keywords:
		if lowercase_question.startswith(keyword):
			return True	
	return False

def turn_rating_lower_better(turn, current_turn):
	# prioritize the first turn
	if turn == 1:
		return float(1.0/(float(current_turn)-1.0))
	else:
		return float(1.0/(float(turn)))

def turn_rating_higher_better(turn, current_turn):
	# prioritize the first turn
	if turn == 1:
		return float(1.0)
	else:
		return float(turn) / (current_turn-1) 

# get the priors for the given predicate
def priors_of_predicate(predicate, max_predicate_priors=18608694):
	predicate = predicate.split('-')[0]
	# do not consider these frequencies (instance_of, cites, author_name_string)
	if predicate in ['P31', 'P2860', 'P2093']:
		return 0
	predicate_frequency = wd.predicate_frequency(predicate)
	return float(predicate_frequency)/float(max_predicate_priors)

# get the priors for the given entity
def priors_of_entity(entity, max_entity_priors=10292):
	entity_frequency = wd.entity_frequency(entity)
	return float(entity_frequency)/float(max_entity_priors)

#####################################################
###		Fagins algorithm
#####################################################

def fagins_algorithm(queue1, queue2, queue3, hyperparameters, k=3):
	h1, h2, h3 = hyperparameters
	queue1_seen_ids = []
	queue2_seen_ids = []
	queue3_seen_ids = []
	length = len(queue1)

	for i in xrange(length):
		queue1_seen_ids.append(queue1[i]['id'])
		queue2_seen_ids.append(queue2[i]['id'])
		queue3_seen_ids.append(queue3[i]['id'])
		if k_items_shared(queue1_seen_ids, queue2_seen_ids, queue3_seen_ids, k=k):
			break
	candidates = []
	seen_ids = list(set(queue1_seen_ids + queue2_seen_ids + queue3_seen_ids))
	for item_id in seen_ids:
		candidate = random_access(queue1, item_id)
		prop1 = random_access(queue1, item_id)['score']
		prop2 = random_access(queue2, item_id)['score']
		prop3 = random_access(queue3, item_id)['score']
		score = h1 * prop1 + h2 * prop2 + h3 * prop3
		candidates.append({'statement': candidate['statement'], 'candidate': candidate['candidate'], 'type': candidate['type'], 'score': score})

	top_candidates = sorted(candidates, key = lambda j: j['score'], reverse=True)
	top_candidates = top_candidates[:k]
	return top_candidates

# random access of an id in a queue
def random_access(queue, item_id):
	return next((x for x in queue if x['id'] == item_id), None)

# returns true if k items are shared among all queues
def k_items_shared(queue1_seen_ids, queue2_seen_ids, queue3_seen_ids, k=3):
	shared_count = 0
	for item_id in queue1_seen_ids:
		if item_id in queue2_seen_ids and item_id in queue3_seen_ids:
			shared_count += 1
	if shared_count >= k:
		return True
	else:
		return False

#####################################################
###		Determine frontiers
#####################################################

# for the given question word, determine the top k matching candidates
def determine_attributes(candidates, context, turn):
	for candidate in candidates:
		# create a temporal context and include the candidates' statement there
		temp_context = context.copy()
		temp_context = gp.expand_context_with_statements(temp_context, [candidate['statement']])
		entity_nodes = gp.get_all_qa_nodes(temp_context)
		if candidate['type'] == 'entity':
			total_weighted_distance = 0
			for entity_node in entity_nodes:
				# increase distance by 1 to avoid zero division
				distance = gp.get_distance(temp_context, candidate['entity'], entity_node[0])
				total_weighted_distance += float(1/float(distance)) * turn_rating_higher_better(entity_node[1]['turn'], turn)
			context_relevance = total_weighted_distance / float(len(entity_nodes))
			priors = priors_of_entity(candidate['entity'])
		elif candidate['type'] == 'qualifier_object':
			total_weighted_distance = 0
			for entity_node in entity_nodes:
				# increase distance by 1 to avoid zero division
				distance = gp.get_distance(temp_context, candidate['qualifier_object'], entity_node[0]) 
				total_weighted_distance += float(1/float(distance)) * turn_rating_higher_better(entity_node[1]['turn'], turn)
			context_relevance = total_weighted_distance / float(len(entity_nodes))
			priors = priors_of_entity(candidate['qualifier_object'])
		elif candidate['type'] == 'predicate':
			# priors = priors_of_predicate(candidate['predicate'])
			total_weighted_distance = 0
			for entity_node in entity_nodes:
				# every predicate label should be unique (to differ between them in the graph); predicate should already be in as in context
				predicate_label = candidate['predicate'] + "-" + str(gp.predicate_nodes[candidate['predicate']]-1)
				distance = gp.get_distance(temp_context, predicate_label, entity_node[0]) 		
				total_weighted_distance += float(1/float(distance)) * turn_rating_higher_better(entity_node[1]['turn'], turn)
			context_relevance = total_weighted_distance / float(len(entity_nodes))
			priors = priors_of_predicate(candidate['predicate'])
		elif candidate['type'] == 'qualifier_predicate':
			# priors = priors_of_predicate(candidate['qualifier_predicate'])
			total_weighted_distance = 0
			for entity_node in entity_nodes:
				# every predicate label should be unique (to differ between them in the graph); predicate should already be in as in context
				predicate_label = candidate['qualifier_predicate'] + "-" + str(gp.qualifier_predicate_nodes[candidate['qualifier_predicate']]-1)
				distance = gp.get_distance(temp_context, predicate_label, entity_node[0]) 
				total_weighted_distance += float(1/float(distance)) * turn_rating_higher_better(entity_node[1]['turn'], turn)
			context_relevance = total_weighted_distance / float(len(entity_nodes))
			priors = priors_of_predicate(candidate['qualifier_predicate'])
		candidate['score'] = {'context_relevance': context_relevance , 'priors': priors}
	return candidates

def determine_matching_similarity(question_word, candidate, is_question_entity=False):
	if is_question_entity:
		matching_similarity = question_word['link_probability']
		return matching_similarity
	else:
		matching_similarity = spacy.similarity_word2vec(question_word, candidate['label'])
		return matching_similarity

def determine_top_candidates(candidates_with_scores, frontier_hyperparameters, k=3):
	h1, h2, h3 = frontier_hyperparameters
	matching_similarity_queue = []
	for counter, candidate in enumerate(candidates_with_scores):
		matching_similarity_queue.append({'id': counter, 'candidate': candidate[candidate['type']], 'score': candidate['score']['matching_similarity'], 'type': candidate['type'], 'statement': candidate['statement']})
	matching_similarity_queue = sorted(matching_similarity_queue, key = lambda j: j['score'], reverse=True)

	context_distances_queue = []
	for counter, candidate in enumerate(candidates_with_scores):
		context_distances_queue.append({'id': counter, 'candidate': candidate[candidate['type']], 'score': candidate['score']['context_relevance'], 'statement': candidate['statement'] })
	context_distances_queue = sorted(context_distances_queue, key = lambda j: j['score'], reverse=True)

	kg_priors_queue = []
	for counter, candidate in enumerate(candidates_with_scores):
		kg_priors_queue.append({'id': counter, 'candidate': candidate[candidate['type']], 'score': candidate['score']['priors'], 'statement': candidate['statement'] })
	kg_priors_queue = sorted(kg_priors_queue, key = lambda j: j['score'], reverse=True)

	top_candidates =  fagins_algorithm(matching_similarity_queue, context_distances_queue, kg_priors_queue, frontier_hyperparameters, k=3)
	return top_candidates

#####################################################
###		Funnctions for evaluation
#####################################################

# print to specified file
def print_results(text):
	with open( "results.txt", "a+") as file:
		try:
			file.write(str(text) + "\n")
		except Exception as e:
			file.write("Exception occured\n")

# print to specified file
def print_temp_results(text):
	with open( "results_temp.txt", "a+") as file:
		try:
			file.write(str(text) + "\n")
		except Exception as e:
			file.write("Exception occured\n")

# fetch the top k best ranked answers from the answer set
def get_top_k_answers_ranked(answers, k=5):
	ranked_answers = []
	answers = sorted(answers, key = lambda j: j['answer_score'], reverse=False)
	last_answer_score = -1
	rank = 0
	same_ranked = 0
	for answer in answers:
		if answer['answer_score'] == last_answer_score:
			ranked_answers.append({'answer': answer['answer'], 'answer_score': answer['answer_score'], 'rank': rank})
			same_ranked += 1
		else:
			rank += (1 + same_ranked)
			# done
			if k and rank > k:
				break
			last_answer_score = answer['answer_score']
			same_ranked = 0
			ranked_answers.append({'answer': answer['answer'], 'answer_score': answer['answer_score'], 'rank': rank})
	return ranked_answers

def MRR_score(answers, golden_answers):
	# check if any answer was given
	if not answers:
		return 0.0
	for answer in answers:
		if answer['answer'] in golden_answers:
			return (1.0/float(answer['rank']))
		elif answer['answer'] in [golden_answer.lower().strip() for golden_answer in golden_answers]:
			return (1.0/float(answer['rank']))
	return 0.0

def precision_at_1(answers, golden_answers):
	# check if any answer was given
	if not answers:
		return 0.0
	for answer in answers:
		if float(answer['rank']) > float(1.0):
			break
		elif answer['answer'] in golden_answers:
			return 1.0
		elif answer['answer'] in [golden_answer.lower().strip() for golden_answer in golden_answers]:
			return 1.0
	return 0.0

def hit_at_5(answers, golden_answers):
	# check if any answer was given
	if not answers:
		return 0.0
	for answer in answers:
		if float(answer['rank']) > float(5.0):
			break
		elif (answer['answer'] in golden_answers):
			return 1.0
		elif answer['answer'] in [golden_answer.lower().strip() for golden_answer in golden_answers]:
			return 1.0
	return 0.0

#####################################################
###		CONVEX method
#####################################################

# answer the given question
def answer_complete_question(question, tagmeToken):
	entities = tagme_get_all_entities(question, tagmeToken) 
	highest_matching_similarity = -1
	for entity in entities:
		shortened_question = shorten_question_for_predicate_similarity(question, entity['spot'])
		statements = wd.get_all_statements_of_entity(entity['wikidata_id'])
		for statement in statements:
			# no identifier predicates
			if statement['predicate']['id'] in identifier_predicates:
				continue
			predicate_label 	= wd.wikidata_id_to_label(statement['predicate']['id'])
			matching_similarity = spacy.similarity_word2vec(predicate_label, shortened_question) * entity['link_probability']
			if highest_matching_similarity == -1 or matching_similarity > highest_matching_similarity:
				answer 		= statement['entity']['id'] if statement['object']['id'] == entity['wikidata_id'] else statement['object']['id']
				context 	= {'entity': {'id': entity['wikidata_id']}, 'predicate': {'id': statement['predicate']['id']}, 'object': {'id': answer}}
				result 		= {'context': context, 'answers': [{'answer': answer, 'rank': 1}] }
				highest_matching_similarity = matching_similarity
	return result

# answer a follow-up question at a given turn with a given context
def answer_follow_up_question(question, turn, graph, hyperparameters, number_of_frontier_nodes):
	question_words = create_question_words_list(question)
	candidates = build_candidate_queue(graph)
	# distance and priors are the same for all question words
	candidates = determine_attributes(candidates, graph, turn)
	for candidate in candidates:
		candidate['score']['matching_similarity'] = 0
		for question_word in question_words:
			matching_score = determine_matching_similarity(question_word, candidate, is_question_entity=False)
			if matching_score > candidate['score']['matching_similarity']:
				candidate['score']['matching_similarity'] = matching_score

	frontiers = [(frontier['candidate'], frontier['statement'], frontier['score']) for frontier in determine_top_candidates(candidates, hyperparameters[:3], number_of_frontier_nodes)]
	integrated_frontiers = []
	for frontier, frontier_statement, score in frontiers:
		# expand the graph
		graph, frontier = gp.expand_context_with_frontier(graph, frontier, frontier_statement, turn)
		# integrated frontiers to receive exact graph representation of predicate
		integrated_frontiers.append((frontier, frontier_statement, score))

	answer_candidates = gp.get_all_answer_candidates(graph)
	h4, h5 = hyperparameters[3:5]
	answers = []
	# determine the answer scores
	for answer_candidate in answer_candidates:
		total_distance_frontiers = 0
		# add up distances to all frontiers
		for (frontier, frontier_statement, score) in integrated_frontiers:
			distance = gp.get_distance(graph, answer_candidate, frontier) 
			total_distance_frontiers +=  distance * float(score)
		total_distance_frontiers = total_distance_frontiers / float(len(integrated_frontiers) if len(integrated_frontiers) else 1)
		total_distance_qa_nodes = 0
		# add up weighted distance to all qa nodes
		for node in gp.get_all_qa_nodes(graph):
			distance = gp.get_distance(graph, answer_candidate, node[0]) 
			total_distance_qa_nodes += distance * turn_rating_lower_better(node[1]['turn'], turn)
		total_distance_qa_nodes = total_distance_qa_nodes / float(len(gp.get_all_qa_nodes(graph)))
		total_distance = h4 * total_distance_qa_nodes + h5 * total_distance_frontiers
		answers.append({'answer': answer_candidate, 'answer_score': total_distance})
	ranked_answers = get_top_k_answers_ranked(answers, k=False)
	top_1 = get_top_k_answers_ranked(answers, k=1)	
	gp.set_all_nodes_as_qa_nodes(graph)
	
	if question_is_existential(question):
		ranked_answers = [{'answer': "yes", 'answer_score': 1.0, 'rank': 1}, {'answer': "no", 'answer_score': 0.5, 'rank': 2}]
	return ranked_answers, graph

# answer a complete conversation 
def answer_conversation(questions, tagmeToken, hyperparameters, number_of_frontier_nodes):
	answers = []
	result 	= answer_complete_question(questions[0], tagmeToken)
	graph 	= gp.expand_context_with_statements(None, [result['context']], qa=True) 
	answers.append(result['answers'])
	for counter, question in enumerate(questions[1:]):
		turn = counter + 2
		answer, graph 	= answer_follow_up_question(question, turn, graph, hyperparameters, number_of_frontier_nodes)
		answers.append(answer)
	return answers

#####################################################
###		Load data
#####################################################

# open the stopwords
with open( "data/stopwords.txt", "r") as data:
	stopwords = data.read().split('\n')

# open the identifier predicates
with open( "data/identifier_predicates.json", "r") as data:
	identifier_predicates = json.load(data)

# open the settings
with open( "settings.json", "r") as data:
	settings 					= json.load(data)
	hyperparameters 			= settings['hyperparameters_frontier_detection'] + settings['hyperparameters_answer_detection']
	number_of_frontier_nodes 	= settings['number_of_frontier_nodes']
	tagmeToken 					= settings['tagMe_token']
	domain 						= settings['domain']
	conversations_path			= settings['conversations_path']
	telegram_chat_id			= settings['telegram_chat_id']
	telegram_active 			= isinstance(telegram_chat_id, int):

if __name__ == '__main__':
	# open the conversations
	with open(conversations_path, "r") as data:
		conversations = json.load(data)

	question_counter = 0
	total_mrr_score = 0.0
	total_precision_at_1_score = 0.0
	total_hit_at_5_score = 0.0
	
	for conversation in conversations:
		if domain != "ALL" and (not conversation['domain'] == domain):
			continue
		questions 		= [turn['question'] for turn in conversation['questions']]
		answers 		= answer_conversation(questions, tagmeToken, hyperparameters, number_of_frontier_nodes)
		golden_answers	= [string.parse_answers(turn['answer']) for turn in conversation['questions']]

		for index, answer in enumerate(answers[1:]):
			total_mrr_score				+= MRR_score(answer, golden_answers[1:][index])
			total_precision_at_1_score 	+= precision_at_1(answer, golden_answers[1:][index])
			total_hit_at_5_score 		+= hit_at_5(answer, golden_answers[1:][index])
			question_counter 			+= 1

	print_results( domain )
	print_results( "MRR_score: 	" + str((question_counter, (total_mrr_score/float(question_counter)), total_mrr_score)))
	print_results( "P@1: 		" + str((question_counter, (total_precision_at_1_score/float(question_counter)), total_precision_at_1_score)))
	print_results( "H@5: 		" + str((question_counter, (total_hit_at_5_score/float(question_counter)), total_hit_at_5_score)))
	print_results("\n")

	wd.save_cached_data()
	spacy.save_cached_data()
	
	if telegram_active:
		telegram.send_message("MRR_score: 	" + str((question_counter, (total_mrr_score/float(question_counter)), total_mrr_score)), telegram_chat_id)
		telegram.send_message("P@1: 		" + str((question_counter, (total_precision_at_1_score/float(question_counter)), total_precision_at_1_score)), telegram_chat_id)
		telegram.send_message("H@5: 		" + str((question_counter, (total_hit_at_5_score/float(question_counter)), total_hit_at_5_score)), telegram_chat_id)


