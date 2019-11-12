# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re
from hdt import HDTDocument
import json
import time
import requests

# identifier_predicates
with open( "data/identifier_predicates.json", "r") as data:
	identifier_predicates = json.load(data)
# label_dict
with open( "data/label_dict.json", "r") as data:
	label_dict = json.load(data)
# predicate_frequencies_dict
with open( "data/predicate_frequencies_dict.json", "r") as data:
	predicate_frequencies_dict = json.load(data)
# entity_frequencies_dict
with open( "data/entity_frequencies_dict.json", "r") as data:
	entity_frequencies_dict = json.load(data)
# statements_dict
with open( "data/statements_dict.json", "r") as data:
	statements_dict = json.load(data)
# open the settings
with open( "settings.json", "r") as data:
	settings 		 	= json.load(data)
	wikidata_dump_path 	= settings['wikidata_dump_path']
# Load an HDT file. Missing indexes are generated automatically, add False as the second argument to disable them
document = HDTDocument(wikidata_dump_path)

# word pattern
predicate_pattern 	= re.compile('^P[0-9]*$')
entity_pattern 		= re.compile('^Q[0-9]*$')

#####################################################
###		Store cached data
#####################################################

def save_cached_data():
	# save the label_dict
	with open( 'data/label_dict.json', 'wb') as outfile:
		outfile.write(json.dumps(label_dict, separators=(',',':')).encode('utf8'))
	# save the predicate_frequencies_dict
	with open( 'data/predicate_frequencies_dict.json', 'wb') as outfile:
		outfile.write(json.dumps(predicate_frequencies_dict, separators=(',',':')).encode('utf8'))
	# save the entity_frequencies_dict
	with open( 'data/entity_frequencies_dict.json', 'wb') as outfile:
		outfile.write(json.dumps(entity_frequencies_dict, separators=(',',':')).encode('utf8'))
	# save the statements_dict
	with open( 'data/statements_dict.json', 'wb') as outfile:
		outfile.write(json.dumps(statements_dict, separators=(',',':')).encode('utf8'))

#####################################################
###		Data fetching
#####################################################

# returns all statements that involve the given entity
def get_all_statements_of_entity(entity_id):
	# check entity pattern
	if not entity_pattern.match(entity_id.strip()):
		return False
	if statements_dict.get(entity_id) != None:
		return statements_dict[entity_id]
	entity = "http://www.wikidata.org/entity/"+entity_id
	statements = []
	# entity as subject
	triples_sub, cardinality_sub = document.search_triples(entity, "", "")
	# entity as object
	triples_obj, cardinality_obj = document.search_triples("", "", entity)
	if cardinality_sub + cardinality_obj > 5000:
		statements_dict[entity_id] = []
		return []
	# iterate through all triples in which the entity occurs as the subject
	for triple in triples_sub:
		sub, pre, obj = triple
		# only consider triples with a wikidata-predicate or if it is an identifier predicate
		if not pre.startswith("http://www.wikidata.org/") or (wikidata_url_to_wikidata_id(pre) in identifier_predicates):
			continue
		# object is statement
		if obj.startswith("http://www.wikidata.org/entity/statement/"):
			qualifier_statements = get_all_statements_with_qualifier_as_subject(obj)
			qualifiers = []
			for qualifier_statement in qualifier_statements:
				if qualifier_statement['predicate'] == "http://www.wikidata.org/prop/statement/" + wikidata_url_to_wikidata_id(pre):
						obj = qualifier_statement['object']
				elif is_entity_or_literal(wikidata_url_to_wikidata_id(qualifier_statement['object'])):
					qualifiers.append({
						"qualifier_predicate":{
							"id": wikidata_url_to_wikidata_id(qualifier_statement['predicate'])
						}, 
						"qualifier_object":{	
							"id": wikidata_url_to_wikidata_id(qualifier_statement['object'])
						}})
			statements.append({'entity': {'id': wikidata_url_to_wikidata_id(sub)}, 'predicate': {'id': wikidata_url_to_wikidata_id(pre)}, 'object': {'id': wikidata_url_to_wikidata_id(obj)}, 'qualifiers': qualifiers})
		else:
			statements.append({'entity': {'id': wikidata_url_to_wikidata_id(sub)}, 'predicate': {'id': wikidata_url_to_wikidata_id(pre)}, 'object': {'id': wikidata_url_to_wikidata_id(obj)}, 'qualifiers': []})
	# iterate through all triples in which the entity occurs as the object
	for triple in triples_obj:
		sub, pre, obj = triple
		# only consider triples with an entity as subject and a wikidata-predicate or if it is an identifier predicate
		if not sub.startswith("http://www.wikidata.org/entity/Q") or not pre.startswith("http://www.wikidata.org/") or wikidata_url_to_wikidata_id(pre) in identifier_predicates:
			continue
		if sub.startswith("http://www.wikidata.org/entity/statement/"):
			statements_with_qualifier_as_object =  get_statement_with_qualifier_as_object(sub, process)
			# if no statement was found continue
			if not statements_with_qualifier_as_object:
				continue
			main_sub, main_pred, main_obj = statements_with_qualifier_as_object
			qualifier_statements = get_all_statements_with_qualifier_as_subject(sub)
			qualifiers = []
			for qualifier_statement in qualifier_statements:
				if wikidata_url_to_wikidata_id(qualifier_statement['predicate']) == wikidata_url_to_wikidata_id(main_pred):
					main_obj = qualifier_statement['object']
				elif is_entity_or_literal(wikidata_url_to_wikidata_id(qualifier_statement['object'])):
					qualifiers.append({
						"qualifier_predicate":{
							"id": wikidata_url_to_wikidata_id(qualifier_statement['predicate'])
						}, 
						"qualifier_object":{	
							"id": wikidata_url_to_wikidata_id(qualifier_statement['object'])
						}})
			statements.append({'entity': {'id': wikidata_url_to_wikidata_id(main_sub)}, 'predicate': {'id': wikidata_url_to_wikidata_id(main_pred)}, 'object': {'id': wikidata_url_to_wikidata_id(main_obj)}, 'qualifiers': qualifiers})
		else:
			statements.append({'entity': {'id': wikidata_url_to_wikidata_id(sub)}, 'predicate': {'id': wikidata_url_to_wikidata_id(pre)}, 'object': {'id': wikidata_url_to_wikidata_id(obj)}, 'qualifiers': []})
	# cache the data
	statements_dict[entity_id] = statements
	return statements

# check if the given wikidata object is an entity or a literal
def is_entity_or_literal(wd_object):
	if entity_pattern.match(wd_object.strip()):
		return True
	pattern = re.compile('^[A-Za-z0-9]*$')
	if len(wd_object) == 32 and pattern.match(wd_object.strip()):
		return False
	return True

# fetch all statements where the given qualifier statement occurs as subject
def get_all_statements_with_qualifier_as_subject(qualifier):
	statements = []
	triples, cardinality = document.search_triples(qualifier, "", "")
	for triple in triples:
		sub, pre, obj = triple
		# only consider triples with a wikidata-predicate
		if pre.startswith("http://www.wikidata.org/"):
			statements.append({'entity': sub, 'predicate': pre, 'object': obj})
	return statements

# fetch the statement where the given qualifier statement occurs as object
def get_statement_with_qualifier_as_object(qualifier):
	triples, cardinality = document.search_triples("", "", qualifier)
	for triple in triples:
		sub, pre, obj = triple
		# only consider triples with a wikidata-predicate
		if pre.startswith("http://www.wikidata.org/") and sub.startswith("http://www.wikidata.org/entity/Q"):
			return (sub, pre, obj)
	return False

# returns the frequency of the given predicate in wikidata
def predicate_frequency(predicate_id):
	if not(predicate_pattern.match(predicate_id.strip())):
		return 0
	if predicate_frequencies_dict.get(predicate_id) != None:
		return predicate_frequencies_dict[predicate_id]
	predicate = "http://www.wikidata.org/prop/direct/"+predicate_id
	triples, cardinality = document.search_triples("", predicate, "")
	predicate_frequencies_dict[predicate_id] = cardinality
	return cardinality

# returns the frequency of the given entity in wikidata
def entity_frequency(entity_id):
	if not(entity_pattern.match(entity_id.strip())):
		return 0
	if entity_frequencies_dict.get(entity_id) != None:
		return entity_frequencies_dict[entity_id]
	entity = "http://www.wikidata.org/entity/"+entity_id
	triples, cardinality = document.search_triples(entity, "", "")
	entity_frequencies_dict[entity_id] = cardinality
	return cardinality

# returns the english label that corresponds to the given wikidata_id
def wikidata_id_to_label(wikidata_id):
	if label_dict.get(wikidata_id) != None:
		return label_dict[wikidata_id]

	if not(entity_pattern.match(wikidata_id.strip())) and not(predicate_pattern.match(wikidata_id.strip())):
		return wikidata_id

	wikidata_url = "http://www.wikidata.org/entity/"+wikidata_id
	triples, cardinality = document.search_triples(wikidata_url, "http://schema.org/name", "")
	for triple in triples:
		obj = triple[2]
		if "@en" in obj:
			label = obj.split('"@en')[0].replace("\"", "")
			label_dict[wikidata_id] = label
			return label

# get top-k hits for the given name for wikidata search
def name_to_wikidata_ids(name, limit=3):
	name = name.split('(')[0]

	request_successfull = False
	while not request_successfull:
		try:
			entity_ids = requests.get('https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json&language=en&limit=' + str(limit) + '&search='+name).json()
			request_successfull = True
		except:
			time.sleep(5)
	results = entity_ids.get("search")
	if not results:
		return ""
	if not len(results):
		return ""
	res = []
	for result in results:
		res.append(result['id'])
	return res

#####################################################
###		Format processing
#####################################################

# return if the given string is a literal or a date
def is_literal_or_date (answer): 
	return not('www.wikidata.org' in answer)

# convert the given month to a number
def convert_month_to_number(month):
	return{
		"january" : "01",
		"february" : "02",
		"march" : "03",
		"april" : "04",
		"may" : "05",
		"june" : "06",
		"july" : "07",
		"august" : "08",
		"september" : "09", 
		"october" : "10",
		"november" : "11",
		"december" : "12"
	}[month.lower()]

# convert a date from the wikidata frontendstyle to timestamp style
def convert_date_to_timestamp (date):	
	sdate = date.split(" ")
	# add the leading zero
	if (len(sdate[0]) < 2):
		sdate[0] = "0" + sdate[0]
	return sdate[2] + '-' + convert_month_to_number(sdate[1]) + '-' + sdate[0] + 'T00:00:00Z'

# convert a year to timestamp style
def convert_year_to_timestamp(year):
	return year + '-01-01T00:00:00Z'

# get the wikidata id of a wikidata url
def wikidata_url_to_wikidata_id(url):
	if not url:
		return False
	if "XMLSchema#dateTime" in url or "XMLSchema#decimal" in url:
		date = url.split("\"", 2)[1]
		date = date.replace("+", "")
		return date
	if(is_literal_or_date(url)):
		if is_year(url):
			return convert_year_to_timestamp(url)
		if is_date(url):
			return convert_date_to_timestamp(url)
		else:
			url = url.replace("\"", "")
			return url
	else:
		url_array = url.split('/')
		# the wikidata id is always in the last component of the id
		return url_array[len(url_array)-1]

# parse the given answer string and return a list of wikidata_id's
def parse_answers(answers_string):
	answers = answers_string.split(';')
	return [wikidata_url_to_wikidata_id(answer) for answer in answers]

# return if the given string describes a year in the format YYYY
def is_year(year):
	pattern = re.compile('^[0-9][0-9][0-9][0-9]$')
	if not(pattern.match(year.strip())):
		return False
	else:
		return True

# return if the given string is a date
def is_date(date):
	pattern = re.compile('^[0-9]+ [A-z]+ [0-9][0-9][0-9][0-9]$')
	if not(pattern.match(date.strip())):
		return False
	else:
		return True

# return if the given string is a timestamp
def is_timestamp(timestamp):
	pattern = re.compile('^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T00:00:00Z')
	if not(pattern.match(timestamp.strip())):
		return False
	else:
		return True


