#!/usr/bin/env python
# -*- coding: utf-8 -*-

# zettel-compose.py
# 	by Bruno L. Conte <bruno@brunoc.com.br>, 2020

import re
from glob import glob
from collections import OrderedDict
import os, time, sys, getopt
import hashlib

KEY_CITEKEY = 'citekey'
KEY_LOCATION = 'loc'

STR_UNINDEXED_HEADING = '# Unindexed'
STR_STREAMING_ID = "<!--\nzettel-compose.py\n-->\n"

options = {
	"no-paragraph-headings": False,
	"heading-identifier": "paragraph-",
	"watch": False,
	"sleep-time": 2,
	"output": None,
	"suppress-index": False,
    "only-link-from-index": False,
    "numbered-quotes": False,
    "verbose": False,
    "stream-to-marked": False
}

rx_dict = OrderedDict([
	('ignore', re.compile(r'^(△|○)')),
	('cross_ref_alt', re.compile(r'\[\[(?P<id>\d{3,})\]\]:')),			#   [[dddd]]:		anywhere in the text, hidden hidden cross reference
	('cross_ref', re.compile(r'^\[\[(?P<id>\d{3,})\]\]')),				#   [[dddd]]		at the beginning of a line, hidden cross reference
	('pandoc_cite_noauthor', re.compile(r'-@\[\[(?P<id>\d{3,})\]\]')),	# -@[[dddd]]
	('pandoc_cite_inline', re.compile(r'@@\[\[(?P<id>\d{3,})\]\]')),	# @@[[dddd]]
	('pandoc_cite', re.compile(r'@\[\[(?P<id>\d{3,})\]\]')),			#  @[[dddd]]
	('no_ref', re.compile(r'-\[\[(?P<id>\d{3,})\]\]')),					#  -[[dddd]]		do not add note
	('quote', re.compile(r' *>\[\[(?P<id>\d{3,})\]\]')), 				#  >[[dddd]]		insert quote immediately
	('add_ref', re.compile(r'\+\[\[(?P<id>\d{3,})\]\]')), 				#  +[[dddd]]		insert note immediately
	('link', re.compile(r'\[\[(?P<id>\d{3,})\]\]')),					#   [[dddd]]
	('yaml_end_div', re.compile(r'^\.\.\.$')),
	('yaml_div', re.compile(r'^\-\-\-$')),
	('md_heading', re.compile(r'^#{1,4}[\s\w]'))
])

fields_dict = {
	"citekey": re.compile(r'^' + KEY_CITEKEY + r':[ \t]*(?P<id>[A-Za-z\d:]+) *$'),
	"loc": re.compile(r'^' + KEY_LOCATION + r':[ \t]*(?P<id>[\d-]+) *$')
}

def _initialize_stack():
	global z_count, z_stack, z_map, unindexed_links
	z_count = { "index": 0, "body": 0, "quote": 0, "sequential": 0, "citation": 0 }
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
		print "ERROR: file not found for zettel " + zettel_id
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
		if z_type in [ "body", "index", "quote", "citation", "sequential" ]:
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
			return " ([§" + str(ref) + "](#" + options["heading-identifier"] + str(ref) + "))"
		else:
			return " (§" + str(ref) + ")"

def _out_quoteref(ref, id):
    """
    Formatted output for text reference
	"""
    global options
    return "T" + str(ref)

def _out_paragraph_heading(ref, zettel_id):
	"""
	Formatted output for a paragraph heading
	"""
	global options
	if options["no-paragraph-headings"]:
		return "{>> = " + str(zettel_id) + " = <<}"
	else:
		if options["heading-identifier"]:
			return "#### " + str(ref) + " {>> = " + str(zettel_id) + " <<}" + " {#" + options["heading-identifier"] + str(ref) + "}"
		else:
			return "#### " + str(ref)

def _out_commented_id(zettel_id, pre = ""):
	"""
	Formatted output for -[[id]]
	"""
	return "{>> " + pre + str(zettel_id) + " <<}"

def _out_text_quote(ref, zettel_id):
    """
    Formatted output for quote preamble
    """
    global options
    if options["numbered-quotes"]:
        return "> **T" + str(ref) + "**{>> = " + str(zettel_id) + " <<}:  "
    else:
        return "{>> " + str(zettel_id) + " <<}"

def _out_unindexed_notes():
	output = [ STR_UNINDEXED_HEADING, "", ""]
	for n in unindexed_links:
		base = os.path.basename(_z_get_filepath(n)[0])
		output.append(os.path.splitext(base)[0] + " " + _out_link(z_map[n]['ref'], n) + ".")
	return output

def _parse_line(line, thedict):
	for key, rx in thedict.items():
		match = rx.search(line)
		if match:
			return key, match, match.end()
	return None, None, None


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
		return "[@" + citetext + "]"
	elif citetext:
		return "@" + citetext

def _pandoc_cite_noauthor(zettel_id):
	citetext = _pandoc_citetext(zettel_id)
	if citetext:
		return "[-@" + citetext + "]"

def parse_zettel(z_item, zettel_id):
    global options, z_map, unindexed_links

    filepath = z_item["path"]

    yaml_divert = False
    got_content = False
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

        if key == 'pandoc_cite':
            link = match.group('id')
            _z_add_to_stack(link, "citation")
            left_chunk = rx_dict["pandoc_cite"].sub(_pandoc_cite(link), left_chunk)

        if key == 'pandoc_cite_inline':
            link = match.group('id')
            _z_add_to_stack(link, "citation")
            left_chunk = rx_dict["pandoc_cite_inline"].sub(_pandoc_cite(link, parenthetical = False), left_chunk)

        if key == 'pandoc_cite_noauthor':
            link = match.group('id')
            _z_add_to_stack(link, "citation")            
            left_chunk = rx_dict["pandoc_cite_noauthor"].sub(_pandoc_cite_noauthor(link), left_chunk)

        if key == 'add_ref':
            link = match.group('id')
            insert_sequence.append(link)
            left_chunk = rx_dict["add_ref"].sub("", left_chunk)


        if key in [ 'cross_ref', 'cross_ref_alt' ]:
            link = match.group('id')
            left_chunk = rx_dict[key].sub(_out_commented_id(link), left_chunk)

        if key == 'no_ref':
            link = match.group('id')
            left_chunk = rx_dict["no_ref"].sub(_out_commented_id(link), left_chunk)

        if key == 'link':
            link = match.group('id')
            if (link in z_map) and (z_map[link]["type"] == "quote"):
                left_chunk = rx_dict["link"].sub(_out_quoteref(z_map[link]["ref"], link), left_chunk) 
       	    elif (z_item["type"] == "index") or (options["only-link-from-index"] is not True):
	            if (link not in z_map) and (z_item["type"] not in [ "index", "sequential" ]):
	            	unindexed_links.append(link)
	            _z_add_to_stack(link, "body")
	            left_chunk = rx_dict["link"].sub(_out_link(z_map[link]["ref"], link), left_chunk)
    	    else:
    	    	left_chunk = rx_dict["link"].sub(_out_commented_id(link), left_chunk)

       	return left_chunk + parse_chunk(chunk[end:])

    with open(filepath, 'r') as file_object:
    	lines = file_object.read().splitlines()

    for line in lines:
    	insert_quotes = []
    	insert_sequence = []
		# at each line check for a match with a regex
        key, match, end = _parse_line(line, rx_dict)

        if yaml_divert:
	       	yaml_divert = not key in ["yaml_div", "yaml_end_div"]
	       	continue

        if key == "yaml_div":
        	yaml_divert = True
        	continue

        if key == "ignore":
        	continue

        # if the first content in a note is a heading, then insert
        # our paragraph heading after, not before it

        if (key == "md_heading") and not got_content:
        	if (z_item["type"] != "quote"): # headings in citation notes are for handouts only
	        	data.append(line)
	        	data.append('')
	        got_content = True
        	if (z_item["type"] == "body"):
        		data.append(_out_paragraph_heading(z_item["ref"], zettel_id))
        	elif (z_item["type"] == "quote"):
        		got_content = False
        	elif (z_item["type"] == "sequential"):
        		data.append(_out_commented_id(zettel_id))
        	continue

        if (not line == '') and not got_content:
        	if (z_item["type"] == "body"):
        		data.append(_out_paragraph_heading(z_item["ref"], zettel_id))
        	elif (z_item["type"] == "quote"):
        		data.append(_out_text_quote(z_item["ref"], zettel_id))
        	elif (z_item["type"] == "sequential"):
        		data.append(_out_commented_id(zettel_id))	        	
        	got_content = True

       	if got_content:
       		line = parse_chunk(line)
	       	data.append(line)

		if insert_sequence is not []:
			for i in insert_sequence:
				_z_add_to_stack(i, "sequential")
				data = data + ['\n'] + parse_zettel(z_map[i], i)

       	if insert_quotes is not []:
       		for i in insert_quotes:
       			_z_add_to_stack(i, "quote")					# add to stack...
       			insert_data = parse_zettel(z_map[i], i)
       			data = data + ['\n'] + insert_data 						# ...but insert immediately after line

    return data

def stream_to_marked(data):
	from AppKit import NSPasteboard
	
	if options["verbose"]:
		print("Streaming...")

	pb = NSPasteboard.pasteboardWithName_("mkStreamingPreview")
	pb.clearContents()
	pb.setString_forType_(data.decode('utf-8'), 'public.utf8-plain-text')


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
		d = parse_zettel(z_map[z_stack[c]], z_stack[c]) + ['']
		if not (options["suppress-index"] and z_map[z_stack[c]]["type"] == "index") and (z_map[z_stack[c]]["type"] not in [ "quote", "citation", "sequential" ]):
			write_to_output(d)
		c += 1

	if unindexed_links and options["stream-to-marked"]:
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

useroptions, infile = getopt.getopt(sys.argv[1:], 'O:MH:s:WnSITt:v', [ 'no-paragraph-headings', 'heading-identifier=', 'watch', 'sleep-time=', 'output=', 'stream-to-marked', 'suppress-index'])

_initialize_stack()

for opt, arg in useroptions:
	if opt in ('-O', '--output='):
		options["output"] = arg
	elif opt in ('-M', '--stream-to-marked'):
		options["stream-to-marked"] = True
	elif opt in ('-H', 'heading-identifier='):
		options["heading-identifier"] = arg
	elif opt in ('-W', '--watch'):
		options["watch"] = True
	elif opt in ('-s', '--sleep-time='):
		options["sleep-time"] = arg
	elif opt in ('-n', '--no-paragraph-headings'):
		options["no-paragraph-headings"] = True
	elif opt in ('-S', '--suppress-index'):
		options["suppress-index"] = True
	elif opt in ('-I'):
		options["only-link-from-index"] = True
	elif opt in ('-T'):
		options["numbered-quotes"] = True
	elif opt in ('-t'):
		z_count["quote"] = (int(arg) - 1)
	elif opt in ('-v'):
		options["verbose"] = True

index_filename = infile[0]
if options["verbose"]:
	print "Processing file " + infile[0]

zettel_dir = os.path.dirname(index_filename)

parse_index(index_filename)

if options["watch"]:
	if options["verbose"]:
		print "Will now watch for changes"
	watch_folder()
