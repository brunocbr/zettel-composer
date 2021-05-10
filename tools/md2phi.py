#!/usr/bin/env python
# -*- coding: utf-8 -*-

# md2phi.py
# 	by Bruno L. Conte <bruno@brunoc.com.br>, 2020

import re
from collections import OrderedDict
import os, sys

fields_dict = OrderedDict([
	('origin', re.compile(r'^origin:\s+(?P<value>.*)$')),
	('tags', re.compile(r'^tags:\s+(?P<value>.*)$')),
	('uplink', re.compile(r'^uplink:\s+(?P<value>\d{3,})$')),
	('blank_line', re.compile(r'^  $')) # two spaces in a line is a blank to be disconsidered
])

rx_dict = OrderedDict([
	('link', re.compile(r'\[(?P<anchor>.+)\]\(x-phi://(?P<link>\d{3,})\)')),
	('footnote', re.compile(r'\[\^(?P<fn_id>[a-zA-Z0-9_-]+)]')),
	('cross_ref', re.compile(r'\*\*(?P<id>\d{3,})\*\*')) 	# any three-or-more-digit bold text is a wikilink
])

title_rx = re.compile(r'(?P<id>\d{3,})\s+(\|\s+){0,1}(?P<title>.+)$')

phi_id = None
out_filename = None

def _parse_line(line, thedict):
	for key, rx in thedict.items():
		match = rx.search(line)
		if match:
			return key, match, match.end()
	return None, None, None

def parse_chunk(chunk):
	global phi_id, rx_dict
	key, match, end = _parse_line(chunk, rx_dict)

	if (key is None):
		return chunk

	left_chunk = chunk[:end]
	if key == 'cross_ref':
		ref_id = match.group('id')
		left_chunk = rx_dict['cross_ref'].sub("[[" + ref_id + "]]", left_chunk)
	if key == 'footnote':
		fn_id = match.group('fn_id')
		left_chunk = rx_dict['footnote'].sub("[^fn-" + phi_id + "-" + fn_id + "]", left_chunk)
	if (key == 'link'):
		value = match.group('anchor')
		link = match.group('link')
		left_chunk = rx_dict['link'].sub(value + " [[" + link + "]]", left_chunk)

	return left_chunk + parse_chunk(chunk[end:])

def getHeader(zettel_id, title, fields):
	header = [ "---", "title:\t'" + title + "'  ", "id:\t\tΦ" + zettel_id + "  "]
	for k in fields.keys():
			if k in ["origin", "tags"]:
				if (len(k) < 5):
					tabs = "\t\t"
				else:
					tabs ="\t"
				header = header + [ k + ":" + tabs + fields[k]]
	header = header + ["..."]

	if "uplink" in fields.keys():
		header = header + [ "", "△[[" + fields["uplink"] + "]]" ]

	return header


def readFile(filepath):
	global phi_id, out_filename

	with open(filepath, 'r') as file_object:
		lines = file_object.read().splitlines()

	fields = {}
	data = []
	
	match = title_rx.search(lines[0])
	if not match:
		raise Exception("Invalid file name for note detected in the first line")

	phi_id = match.group('id')
	title = match.group('title')
	out_filename = phi_id + " " + title + ".markdown"

	data.append("# " + title)

	for line in lines[1:]:
		key, match, end = _parse_line(line, fields_dict)
		if (key):
			if key != 'blank_line':
				value = match.group('value')
				fields[key] = value
			continue
		line = parse_chunk(line)
		data.append(line)

	h = getHeader(phi_id, title, fields)
	return h + [ '' ] + data

phi_dir = sys.argv[1]
infile = sys.argv[2]
d = readFile(infile)

with open(phi_dir + "/" + out_filename, "w") as f_out:
	for l in d:
		f_out.write("%s\n" % l)

