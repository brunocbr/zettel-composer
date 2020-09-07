#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from glob import glob
import os, time, sys


options = {
	"no-paragraph-headings": False,
	"heading-identifier": "paragraph-",
	"watch": True,
	"sleep-time": 2
}

rx_dict = {
#	'link': re.compile(r'[^△▽\+\-\%]\[\[(?P<id>\d{3,})\]\]'),
	'link': re.compile(r'\[\[(?P<id>\d{3,})\]\](^:|$)'),
	'no_ref': re.compile(r'\[\[(?P<id>\d{3,})\]\]:'),
#	'link_b': re.compile(r'^\[\[(?P<id>\d{3,})\]\]'),
	'footnote': re.compile(r' *\%\[\[(?P<id>\d{3,})\]\]'),
	'add_ref': re.compile(r'\+\[\[(?P<id>\d{3,})\]\]'),
	'yaml_end_div': re.compile(r'^\.\.\.$'),
	'yaml_div': re.compile(r'^\-\-\-$'),
	'md_heading': re.compile(r'^#{1,3}'),
	'ignore': re.compile(r'^(△|○)')
}


z_count = { "index": 0, "body": 0, "footnote": 0 }

z_stack = [ ]

z_map = {} # maps zettel id's to paragraph or footnote sequence


z_info = {} # contain path, status (se já foi processada)


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

def _z_set_index(pathname):
	global z_map, z_stack
	mtime = os.path.getmtime(pathname)
	z_map["index"] = { "type": "index", "ref": 0, "path": pathname, "mtime": mtime }
	if len(z_stack) == 0:
		z_stack.append("index")

def _z_add_to_stack(zettel_id, z_type):
	"""
	Add a note to stack if not already in it
	valid z_types are "body", "footnote"
	"""
	global z_count
	global z_stack

	if not zettel_id in z_map:
		z_count[z_type] += 1
		path, mtime = _z_get_filepath(zettel_id)
		z_map[zettel_id] = { "type": z_type, "ref": z_count[z_type], "path": path, "mtime": mtime }
		if z_type in [ "body", "index" ]:
			z_stack.append(zettel_id) 
	return z_map[zettel_id]

def _out_link(ref, id):
	"""
	Formatted output for link to a reference
	"""
	if options["no-paragraph-headings"]:
		return " {>> [[" + str(id) + "]] <<}"
	else:
		if options["heading-identifier"]:
			return " ([" + str(ref) + "](#" + options["heading-identifier"] + str(ref) + "))"
		else:
			return " (**" + str(ref) + "**)"


def _out_paragraph_heading(ref, zettel_id):
	"""
	Formatted output for a paragraph heading
	"""
	if options["no-paragraph-headings"]:
		return "{>> = " + str(zettel_id) + " = <<}"
	else:
		if options["heading-identifier"]:
			return "#### " + str(ref) + " {>> = " + str(zettel_id) + " <<}" + " {#" + options["heading-identifier"] + str(ref) + "}" 
		else:
			return "#### " + str(ref)

def _out_commented_id(zettel_id):
	"""
	Formatted output for -[[id]]
	"""
	return "{>> " + str(zettel_id) + " <<}"


def _parse_line(line):
	for key, rx in rx_dict.items():
		match = rx.search(line)
		if match:
			return key, match
	return None, None

def parse_zettel(z_item, zettel_id):
    """
    Parse text at given filepath

    Parameters
    ----------
    filepath : str
        Filepath for file_object to be parsed

    Returns
    -------
    data : pd.DataFrame
        Parsed data

    """
    filepath = z_item["path"]

    yaml_divert = False
    got_content = False

    data = [] # create an empty list to collect the data
    # open the file and read through it line by line
    with open(filepath, 'r') as file_object:
    	lines = file_object.read().splitlines()

    for line in lines:
		# at each line check for a match with a regex
        key, match = _parse_line(line)

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
        	data.append(line)
        	data.append('')
        	if (z_item["type"] == "body"):
	        	data.append(_out_paragraph_heading(z_item["ref"], zettel_id))
	        	data.append('')
        	got_content = True
        	continue

        if (not line == '') and not got_content:
        	if (z_item["type"] == "body"):
	        	data.append(_out_paragraph_heading(z_item["ref"], zettel_id))
	        	data.append('')
        	got_content = True

        if key == 'footnote':
            link = match.group('id')
            _z_add_to_stack(link, "footnote")


        # TODO: +[[id]] is actually intended to immediately include a file
        if key == 'add_ref':
            link = match.group('id')
            _z_add_to_stack(link, "body")


        if key == 'no_ref':
            link = match.group('id')
            line = rx_dict["no_ref"].sub(_out_commented_id(link), line)


        if key == 'link':
            link = match.group('id')
            _z_add_to_stack(link, "body")
            line = rx_dict["link"].sub(_out_link(z_map[link]["ref"] ,link), line)

       	if got_content:
	       	data.append(line)

    return data

def get_first_modified():
	global z_stack
	global z_map
	c = 0
	result = None
	while (not result and c < len(z_stack)):
		cur_path, cur_mtime = _z_get_filepath(z_stack[c])
		if cur_mtime != z_map[z_stack[c]]["mtime"]:
			result = c
		z_map[z_stack[c]]["path"], z_map[z_stack[c]]["mtime"] = cur_path, cur_mtime # update modified filenames and mtimes
		c += 1
	return result

def parse_index(pathname):
	global z_stack
	global z_map
	# _z_add_to_stack(zettel_id, "index")
	_z_set_index(pathname)
	c = 0
	with open("compose-output.md", "w") as f_out:
		while len(z_stack) > c:
			print ("zettel id " + z_stack[c])
			d = parse_zettel(z_map[z_stack[c]], z_stack[c]) + ['']
			for l in d:
				f_out.write("%s\n" % l)
			c += 1

def watch_folder():
	global z_stack, options

	while True:
		# cur_mtime = os.path.getmtime(zettel_dir)
		# if cur_mtime != last_mtime:

		modified = get_first_modified()
		if modified is not None:
			print "note " + str(modified) + " id " + z_stack[modified] + " was modified"
			parse_index(index_filename)
		time.sleep(options["sleep-time"])


index_filename = sys.argv[1]
zettel_dir = os.path.dirname(index_filename)

parse_index(index_filename)

if options["watch"]:
	print "Will now watch for changes"
	watch_folder()



