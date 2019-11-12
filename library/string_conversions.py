# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re

# open the stopwords
with open( "data/stopwords.txt", "r") as data:
	stopwords = data.read().split('\n')
	
# get the wikidata id of a wikidata url
def wikidata_url_to_wikidata_id(url):
	if not url:
		return False
	if(is_literal_or_date(url)):
		if is_year(url):
			return convert_year_to_timestamp(url)
		if is_date(url):
			return convert_date_to_timestamp(url)
		else:
			return url
	else:
		url_array = url.split('/')
		# the wikidata id is always in the last component of the id
		return url_array[len(url_array)-1]

# parse the given answer string and return all answers in a list
def parse_answers(answers_string):
	answers = answers_string.split(';')
	return [wikidata_url_to_wikidata_id(answer) for answer in answers]

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