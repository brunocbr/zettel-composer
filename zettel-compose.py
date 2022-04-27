#!/usr/bin/env python
# -*- coding: utf-8 -*-

# zettel-compose.py
# 	by Bruno L. Conte <bruno@brunoc.com.br>, 2020-2022

import re
from glob import glob
from collections import OrderedDict
import os, time, sys, getopt
import hashlib

KEY_CITEKEY = 'citekey'
KEY_LOCATION = 'loc'

CF_PANDOC ='pandoc'

STR_UNINDEXED_HEADING = '# Unindexed'
STR_STREAMING_ID = "<!--\nzettel-compose.py\n-->\n"
STR_SIGN_INSERT = '▾ '	# = '▾ '
STR_SIGN_COMMENT = '▸ ' # =  '❧ '  = '▹ '
STR_HANDOUT_HEADING = '####'
SEPARATOR = [ '\n', '-----', '\n' ]

options = {
	'output': None,
	'no-commented-references': False,
	"no-paragraph-headings": False,
	"heading-identifier": "paragraph-",
	"watch": False,
	"sleep-time": 2,
	"output": None,
	"suppress-index": False,
	"only-link-from-index": False,
	"verbose": False,
	"stream-to-marked": False,
	'parallel-texts-processor': None,
	'parallel-texts-selection': 'lr',
	'no-separator': False,
	'handout-mode': False,
	'handout-with-sections': True,
	'link-all': False, # link normal wikilinks
	'custom-url': 'thearchive://match/',
	'section-symbol': '§',
	'insert-title': False,
	'insert-bib-ref': False
}

rx_dict = OrderedDict([
	('ignore', re.compile(r'^(△|○)')),
	('footnote', re.compile(r'\[\^(?P<fn_id>[a-zA-Z0-9_-]+)]')),
	('parallel_texts', re.compile(r' *>\s{0,1} *\[\[(?P<id_left>\d{3,})\]\] *:: *\[\[(?P<id_right>\d{3,})\]\]')), # > [[dddd]] :: [[dddd]]
	('pandoc_cite_noauthor', re.compile(r'-@ *\[\[(?P<id>\d{3,})\]\]')),# -@ [[dddd]]
	('pandoc_cite_inline', re.compile(r'@@ *\[\[(?P<id>\d{3,})\]\]')),	# @@ [[dddd]]
	('pandoc_cite', re.compile(r'@ *\[\[(?P<id>\d{3,})\]\]')),			#  @ [[dddd]]
	('no_ref', re.compile(r'- *\[\[(?P<id>\d{3,})\]\]')),		   		#  - [[dddd]]		do not add note
	('quote', re.compile(r' *>\s{0,1}\[\[(?P<id>\d{3,})\]\]')), 		#  > [[dddd]]		insert quote immediately
	('add_ref', re.compile(r'\+ *\[\[(?P<id>\d{3,})\]\]')), 			#  + [[dddd]]		insert note immediately
	('link', re.compile(r'§ *\[\[(?P<id>\d{3,})\]\]')),					#  § [[dddd]]		print reference to paragraph or text
	('cross_ref_alt', re.compile(r'\[\[(?P<id>\d{3,})\]\] *:')),   		#   [[dddd]] :		hidden cross reference
	('cross_ref', re.compile(r'\s*\[\[(?P<id>\d{3,})\]\]')),			#   [[dddd]]		hidden cross reference
	('yaml_end_div', re.compile(r'^\.\.\.$')),
	('yaml_div', re.compile(r'^\-\-\-$')),
	('md_heading', re.compile(r'^#{1,4}[\s\w]')),
	('title', re.compile(r'^title:\s*\'(?P<id>.*)\'\s*$'))
])

fields_dict = {
	"citekey": re.compile(r'^' + KEY_CITEKEY + r':[ \t]*(?P<id>[A-Za-z\d:]+)\s*$'),
	# "loc": re.compile(r'^' + KEY_LOCATION + r':[ \t]*(?P<id>[\d-]+)\s*$')
	"loc": re.compile(r'^' + KEY_LOCATION + r':[ \t]*(?P<id>[\S]+)\s*$')
}

def _initialize_stack():
	global z_count, z_stack, z_map, unindexed_links
	z_count = { "index": 0, "body": 0, "quote": 0, "sequential": 0, "citation": 0, "left_text": 0, "right_text": 0 }
	z_stack = []
	z_map = {} # maps zettel id's to paragraph or sequence
	unindexed_links = []

def _z_get_filepath(zettel_id):
	"""
	Get file path for a note
	"""
	global zettel_dir, index_filename

	try:
		if (zettel_id == "index"):
			fn = index_filename
		else:
			fn = glob(zettel_dir + "/" + zettel_id + "[ \.]*")[0]
		mtime = os.path.getmtime(fn)
	except:
		print("ERROR: file not found for zettel " + zettel_id)
		fn, mtime = None, None
	return fn, mtime

def _get_file_md5digest(pathname):
	md5_hash = hashlib.md5()

	with open(pathname, "rb") as a_file:
		content = a_file.read()
	
	md5_hash.update(content)
	digest = md5_hash.hexdigest()

	return digest

def _z_set_index(pathname):
	global z_map, z_stack
	mtime = os.path.getmtime(pathname)
	md5hash = _get_file_md5digest(pathname)
	z_map["index"] = { "type": "index", "ref": 0, "path": pathname, "mtime": mtime, "md5hash": md5hash }
	if len(z_stack) == 0:
		z_stack.append("index")

def _z_add_to_stack(zettel_id, z_type):
	"""
	Add a note to stack if not already in it
	"""
	global z_count
	global z_stack

	if not zettel_id in z_map:
		z_count[z_type] += 1
		path, mtime = _z_get_filepath(zettel_id)
		md5hash = _get_file_md5digest(path)
		z_map[zettel_id] = { "type": z_type, "ref": z_count[z_type], "path": path, "mtime": mtime, "md5hash": md5hash }
		if z_type in [ 'body', 'index', 'quote', 'citation', 'sequential', 'left_text', 'right_text' ]:
			z_stack.append(zettel_id)
	return z_map[zettel_id]

def _out_link(ref, id):
	"""
	Formatted output for link to a reference
	"""
	global options
	if options["no-paragraph-headings"]:
		return " {>> [[" + str(id) + "]] <<}"
	else:
		if options["heading-identifier"]:
			return " ([" + options['section-symbol'] + str(ref) + "](#" + options["heading-identifier"] + str(ref) + "))"
		else:
			return " (" + options['section-symbol'] + str(ref) + ")"

def _out_linked_zettel(id):
	return '[' + str(id) + '](' + options['custom-url'] + str(id) + ')'

def _out_quoteref(ref, id):
	"""
	Formatted output for text reference
	"""
	return "T" + str(ref)

def _out_paragraph_heading(ref, zettel_id):
	"""
	Formatted output for a paragraph heading
	"""
	global options
	if options["no-paragraph-headings"]:
		return  _out_commented_id(zettel_id)
	else:
		if options["heading-identifier"]:
			return "#### " + str(ref) + '. ' + _out_commented_id(zettel_id, pre=STR_SIGN_INSERT) + " {#" + options["heading-identifier"] + str(ref) + "}"
		else:
			return "#### " + str(ref) + '. '

def _out_commented_id(zettel_id, pre = "", post=""):
	"""
	Formatted output for [[id]]
	"""
	if options['no-commented-references']:
		return ''
	else:
		return ' {>> ' + pre + _out_linked_zettel(zettel_id) + post + ' <<}'

def _out_text_quote(ref, zettel_id):
	"""
	Formatted output for quote preamble
	"""
	return '> ' + _out_commented_id(zettel_id, pre=STR_SIGN_INSERT) + ' **T' + str(ref) + ':**  '

def _out_unindexed_notes():
	output = [ STR_UNINDEXED_HEADING, "", ""]
	for n in unindexed_links:
		base = os.path.basename(_z_get_filepath(n)[0])
		output.append(os.path.splitext(base)[0] + " " + _out_link(z_map[n]['ref'], n) + ".")
	return output

def _out_latex_parallel_texts(left_text, right_text):
	import subprocess

	CMD = [CF_PANDOC, '-f', 'markdown', '-t', 'latex']

	ps = subprocess.Popen(CMD,stdin=subprocess.PIPE,stdout=subprocess.PIPE,encoding="utf-8")
	left_text = (ps.communicate(input='\n'.join(left_text))[0]).splitlines()

	ps = subprocess.Popen(CMD,stdin=subprocess.PIPE,stdout=subprocess.PIPE,encoding="utf-8")
	right_text = (ps.communicate(input="\n".join(right_text))[0]).splitlines()

	output = ['\ParallelTexts{%'] + left_text + ['}{'] + right_text + ['}'] + ['']
	return output

def _out_parallel_texts(left, right):
	left_data = parse_zettel(z_map[left], left)
	right_data = parse_zettel(z_map[right], right)
	output = []
	if not options['handout-mode']: # qual será o padrão? esperar quotes nas fichas ou não?
		if ('l' in options['parallel-texts-selection']):
			output.append(_out_text_quote(z_map[left]["ref"], left))
			output = output + left_data
		else:
			output.append(_out_text_quote(z_map[right]["ref"], right))
		if ('r' in options['parallel-texts-selection']):
			output.append('> ')
			if ('l' in options['parallel-texts-selection']):
				output.append("> " + _out_commented_id(right, pre=STR_SIGN_INSERT) + '  ')
			output = output + right_data
	else:
		output.append(STR_HANDOUT_HEADING + ' ' + z_map[right]['title'])
		output.append('')
		if not options['parallel-texts-processor']:
			output = output + left_data + ['\n'] + right_data
		else:
			output = output + _out_latex_parallel_texts(left_data, right_data)

	return output

def _parse_line(line, thedict):
	for key, rx in thedict.items():
		match = rx.search(line)
		if match:
			return key, match, match.end()
	return None, None, None

def _remove_md_quotes(line):
	rx = re.compile(r'^\s*>\s*')
	match = rx.search(line)
	if match:
		line = rx.sub("", line)
	return line

def _md_quote(line):
	line = _remove_md_quotes(line)
	line = '> ' + line
	return line


def _pandoc_citetext(zettel_id):
	"""
	Get reference for pandoc-style citation
	"""
	global fields_dict
	citekey = None
	loc = None
	filepath, mtime = _z_get_filepath(zettel_id)

	with open(filepath, 'r') as file_obj:
		lines = file_obj.read().splitlines()

	for line in lines:
		key, match, end = _parse_line(line, fields_dict)
		if key == "citekey":
			citekey = match.group('id')
		if key == "loc":
			loc = match.group('id')

	citetext = None
	if (citekey and loc and loc != "0"):
		citetext = citekey + ", " + loc
	elif (citekey):
		citetext = citekey
	return citetext

def _pandoc_cite(zettel_id, parenthetical = True):
	citetext = _pandoc_citetext(zettel_id)
	if citetext and parenthetical:
		return "[@" + citetext + "]" + _out_commented_id(zettel_id, pre=STR_SIGN_COMMENT)
	elif citetext:
		return "@" + citetext + _out_commented_id(zettel_id, pre=STR_SIGN_COMMENT)

def _pandoc_cite_noauthor(zettel_id):
	citetext = _pandoc_citetext(zettel_id)
	if citetext:
		return "[-@" + citetext + "]" + _out_commented_id(zettel_id, pre=STR_SIGN_COMMENT)

def parse_zettel(z_item, zettel_id):
	global options, z_map, unindexed_links

	filepath = z_item["path"]

	yaml_divert = False
	got_content = False
	got_title = False
	insert_sequence = []

	data = [] # create an empty list to collect the data

	def parse_chunk(chunk):
		key, match, end = _parse_line(chunk, rx_dict)

		if (key is None):
			return chunk

		left_chunk = chunk[:end]

		if key == 'quote':
			link = match.group('id')
			insert_quotes.append(link)
			left_chunk = rx_dict["quote"].sub("", left_chunk)

		elif key == 'parallel_texts':
			left_link, right_link = match.group('id_left'), match.group('id_right')
			insert_parallel_texts.append((left_link, right_link))
			left_chunk = rx_dict['parallel_texts'].sub("", left_chunk)

		elif key == 'pandoc_cite':
			link = match.group('id')
			_z_add_to_stack(link, "citation")
			left_chunk = rx_dict["pandoc_cite"].sub(_pandoc_cite(link), left_chunk)

		elif key == 'pandoc_cite_inline':
			link = match.group('id')
			_z_add_to_stack(link, "citation")
			left_chunk = rx_dict["pandoc_cite_inline"].sub(_pandoc_cite(link, parenthetical = False), left_chunk)

		elif key == 'pandoc_cite_noauthor':
			link = match.group('id')
			_z_add_to_stack(link, "citation")			
			left_chunk = rx_dict["pandoc_cite_noauthor"].sub(_pandoc_cite_noauthor(link), left_chunk)

		elif key == 'add_ref':
			link = match.group('id')
			insert_sequence.append(link)
			left_chunk = rx_dict["add_ref"].sub("", left_chunk)

		elif (key == 'link') or (options['link-all'] and (key == 'cross_ref')):
			link = match.group('id')
			if (link in z_map) and (z_map[link]["type"] in ['quote', 'left_text', 'right_text']):
				left_chunk = rx_dict["link"].sub(_out_quoteref(z_map[link]["ref"], link), left_chunk) 
			elif (z_item["type"] not in [ "citation" ]) and ((z_item["type"] == "index") or (options["only-link-from-index"] is not True)):
				if (link not in z_map) and (z_item["type"] not in [ "index", "sequential" ]):
					unindexed_links.append(link)
				_z_add_to_stack(link, "body")
				left_chunk = rx_dict[key].sub(_out_link(z_map[link]["ref"], link), left_chunk)
			else:
				left_chunk = rx_dict[key].sub(_out_commented_id(link), left_chunk)

		elif key in [ 'cross_ref', 'cross_ref_alt' ]:
			link = match.group('id')
			left_chunk = rx_dict[key].sub(_out_commented_id(link, pre=STR_SIGN_COMMENT), left_chunk)

		elif key == 'no_ref':
			link = match.group('id')
			left_chunk = rx_dict["no_ref"].sub(_out_commented_id(link), left_chunk)

		elif key == 'footnote':
			fn_id = match.group('fn_id')
			left_chunk = rx_dict['footnote'].sub("[^fn-" + zettel_id + "-" + fn_id + "]", left_chunk)



		return left_chunk + parse_chunk(chunk[end:])

	with open(filepath, 'r') as file_object:
		lines = file_object.read().splitlines()

	zettel_title = 'Untitled'
	for line in lines:
		insert_quotes = []
		insert_parallel_texts = []
		insert_sequence = []
		# at each line check for a match with a regex
		key, match, end = _parse_line(line, rx_dict)

		if yaml_divert:
		   	yaml_divert = not key in ["yaml_div", "yaml_end_div"]
		   	if key == 'title':
		   		zettel_title = match.group('id')
		   		z_item['title'] = zettel_title
		   	continue

		if key == "yaml_div":
			yaml_divert = True
			continue

		if key == "ignore":
			continue

		# if the first content in a note is a heading, then insert
		# our paragraph heading after, not before it

		if (key == "md_heading") and not got_content:
			if (z_item["type"] != "quote" and ((not options['handout-mode']) or options['handout-with-sections'])): # headings in citation notes are ~~for handouts only~~ good for nothing
				data.append(line)
				data.append('')
				got_title = True
			got_content = False
			continue

		if (not line == '') and not got_content:
			if not got_title:
				if (not z_item["type"] != "quote"):  # insert note title as ATX heading unless it's a quote
					data.append("## " + zettel_title)
				got_title = True
			if (not options['handout-mode']):
				if (z_item["type"] == "body"):
					data.append(_out_paragraph_heading(z_item["ref"], zettel_id))
				elif (z_item["type"] == "quote"):
					data.append(_out_text_quote(z_item["ref"], zettel_id))
				elif (z_item["type"] in [ 'sequential' ]):
					data.append(_out_commented_id(zettel_id, pre=STR_SIGN_INSERT))
			elif (z_item['type'] in ['quote']): # headings in handout before content
					data.append(STR_HANDOUT_HEADING + ' ' + zettel_title)
					data.append(_out_commented_id(zettel_id, pre=STR_SIGN_INSERT))
			elif (z_item['type'] in ['left_text', 'right_text']) and not options['no-commented-references']:
					data.append(_out_commented_id(zettel_id, pre=STR_SIGN_INSERT))
			got_content = True

		if got_content:
			if options['handout-mode']:
				if key == 'md_heading' and options['handout-with-sections']:
					data.append(line)
					data.append('')
				else:
					line = parse_chunk(line)
					if z_item['type'] in ['left_text', 'right_text', 'quote']:
						line = _remove_md_quotes(line)
						data.append(line)
			else:
				line = parse_chunk(line)
				if (z_item['type'] in ['quote', 'left_text', 'right_text']): # enforce quotes when not printing handouts
					line = _md_quote(line)
				data.append(line)

		if insert_sequence is not []:
			for i in insert_sequence:
				_z_add_to_stack(i, "sequential")
				data = data + ['\n'] + parse_zettel(z_map[i], i)

		if insert_quotes is not []:
	   		for i in insert_quotes:
	   			_z_add_to_stack(i, "quote")					# add to stack...
	   			insert_data = parse_zettel(z_map[i], i)
	   			data = data + ['\n'] + insert_data 			# ...but insert immediately after line

		if insert_parallel_texts is not []:
	   		for l, r in insert_parallel_texts:
	   			_z_add_to_stack(l, 'left_text')
	   			_z_add_to_stack(r, 'right_text')
	   			insert_data = _out_parallel_texts(l, r)
	   			data = data + ['\n'] + insert_data

	if (z_item['type'] in ['right_text']) and not options['handout-mode']:
		while (data[-1] == '\n'):
			del data[-1]									# remove trailing lines
		data[-1] = data[-1] + ' (' + zettel_title + ')'		# add reference to last line in quote
	elif options['insert-bib-ref']:
		citetxt = _pandoc_citetext(zettel_id)
		if citetxt:
			data.append('')
			data.append("@" + citetxt)

	return data

def stream_to_marked(data):
	from AppKit import NSPasteboard
	
	if options["verbose"]:
		print("Streaming...")

	pb = NSPasteboard.pasteboardWithName_("mkStreamingPreview")
	pb.clearContents()
	pb.setString_forType_(data, 'public.utf8-plain-text')

def get_first_modified():
	global z_stack
	global z_map
	c = 0
	result = None
	while (not result and c < len(z_stack)):
		cur_path, cur_mtime = _z_get_filepath(z_stack[c])
		if cur_mtime != z_map[z_stack[c]]["mtime"]:
			md5hash = _get_file_md5digest(cur_path)
			if md5hash != z_map[z_stack[c]]["md5hash"]:
				result = c
		z_map[z_stack[c]]["path"], z_map[z_stack[c]]["mtime"] = cur_path, cur_mtime # update modified filenames and mtimes
		c += 1
	return result

def parse_index(pathname):
	global z_stack, z_map, options, unindexed_links

	c = 0
	parse_index.output = [ STR_STREAMING_ID ]
	parse_index.f_out = None

	def write_to_output(contents):
		if not options['no-separator']:
			contents = contents + SEPARATOR
		if parse_index.f_out:
			for l in contents:
				parse_index.f_out.write("%s\n" % l)	
		if options["stream-to-marked"]:
			parse_index.output = parse_index.output + contents

	_z_set_index(pathname)

	if options["output"] and (options["output"] != '-'):
		parse_index.f_out = open(options["output"], "w")
	elif not options["stream-to-marked"]:
		parse_index.f_out = sys.stdout

	while len(z_stack) > c:
		if options["verbose"]:
			print ("zettel id " + z_stack[c])
		if z_map[z_stack[c]]['type'] not in [ 'quote', 'citation', 'left_text', 'right_text' ]:
			d = parse_zettel(z_map[z_stack[c]], z_stack[c]) + ['']
			if not (options["suppress-index"] and z_map[z_stack[c]]["type"] == "index") and (z_map[z_stack[c]]["type"] not in [ "sequential" ]):
				write_to_output(d)
		c += 1

	if unindexed_links:
		d = _out_unindexed_notes()
		write_to_output(d)

	if parse_index.f_out and (parse_index.f_out is not sys.stdout):
		parse_index.f_out.close()

	if options["stream-to-marked"]:
		stream_to_marked("\n".join(parse_index.output))

def watch_folder():
	global z_stack, options

	while True:
		modified = get_first_modified()
		if modified is not None:
			if options["verbose"]:
				print("note " + str(modified) + " id " + z_stack[modified] + " was modified")
			time.sleep(1)
			_initialize_stack()
			parse_index(index_filename)
		time.sleep(options["sleep-time"])

useroptions, infile = getopt.getopt(sys.argv[1:], 'CO:MH:s:WnSIt:G:vh:PL', [ 'no-commented-references', 
	'no-paragraph-headings', 'heading-identifier=', 'watch', 'sleep-time=', 'output=', 'stream-to-marked', 
	'suppress-index', 'no-separator', 'link-all', 'custom-url=', 'section-symbol=', 'insert-title', 'insert-bib-ref'])


if infile == [ ]:
	raise ValueError("Argument is missing: you must provide a file name for the index note.")

_initialize_stack()

for opt, arg in useroptions:
	if opt in ('-O', '--output='):
		options["output"] = arg
	elif opt in ('-M', '--stream-to-marked'):
		options["stream-to-marked"] = True
	elif opt in ('-H', '--heading-identifier='):
		options["heading-identifier"] = arg
	elif opt in ('-W', '--watch'):
		options["watch"] = True
	elif opt in ('-s', '--sleep-time='):
		options["sleep-time"] = arg
	elif opt in ('-n', '--no-paragraph-headings'):
		options["no-paragraph-headings"] = True
	elif opt in ('--no-separator'):
		options["no-separator"] = True
	elif opt in ('-C', '--no-commented-references'):
		options['no-commented-references'] = True
	elif opt in ('-S', '--suppress-index'):
		options["suppress-index"] = True
	elif opt in ('-I'):
		options["only-link-from-index"] = True
	elif opt in ('-t'):
		z_count["quote"] = (int(arg) - 1)
	elif opt in ('-G'):
		if ('l' not in arg) and ('r' not in arg):
			raise ValueError("-G should take either 'l' or 'r' as argument")
		options['parallel-texts-selection'] = arg
	elif opt in ('-v'):
		options["verbose"] = True
	elif opt in ('-h'):
		options['handout-mode'] = True
		options['handout-with-sections'] = ('+' in arg)
	elif opt in ('-P'):
		options['parallel-texts-processor'] = True
		options['no-commented-references'] = True
	elif opt in ('-L', '--link-all'):
		options['link-all'] = True
	elif opt in ('--custom-url='):
		options['custom-url'] = arg
	elif opt in ('--section-symbol='):
		options['section-symbol'] = arg
	elif opt in ('--insert-title'):
		options['insert-title'] = True
	elif opt in ('--insert-bib-ref'):
		options['insert-bib-ref'] = True

index_filename = infile[0]
if options["verbose"]:
	print("Processing file " + infile[0])

zettel_dir = os.path.dirname(index_filename)

parse_index(index_filename)

if options["watch"]:
	if options["verbose"]:
		print("Will now watch for changes")
	watch_folder()
