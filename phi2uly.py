#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# phi2uly.py
# 	by Bruno L. Conte <bruno@brunoc.com.br>, 2021

import re
from collections import OrderedDict
import os, sys, urllib.parse

fields_dict = OrderedDict([
	('tags', re.compile(r'^tags:\s+(?P<value>.*)\s*$')),
	('title', re.compile(r'^title:\s+\'+(?P<value>.*)\'\s*$')),
	('id', re.compile(r'^id:\s+Φ(?P<value>\d{3,})\s*$')),
	('phi_uplink', re.compile(r'^△\[\[(?P<value>\d{3,})\]\]')),
	('yaml_end_div', re.compile(r'^\.\.\.$')),
	('yaml_div', re.compile(r'^\-\-\-$')),
	('breadcrumb', re.compile(r'^○'))
])

rx_dict = OrderedDict([
	('phi_cross_ref', re.compile(r'\[\[(?P<id>\d{3,})\]\]')) 	# any three-or-more-digit bold text is a wikilink
])

def parse_line(line, thedict):
	for key, rx in thedict.items():
		match = rx.search(line)
		if match:
			return key, match, match.end()
	return None, None, None

def parse_chunk(chunk):
	global rx_dict
	key, match, end = parse_line(chunk, rx_dict)

	if (key is None):
		return chunk

	left_chunk = chunk[:end]
	if key == 'phi_cross_ref':
		ref_id = match.group('id')
		left_chunk = rx_dict['phi_cross_ref'].sub("**" + ref_id + "**", left_chunk)

	return left_chunk + parse_chunk(chunk[end:])

def getHeader(fields):
	try:
		tags = fields["tags"]
	except:
		tags = ""

	try:
		origin = fields["origin"]
	except:
		origin = ""

	try:
		uplink = fields["phi_uplink"]
	except:
		uplink = ""


	header = [ "origin: " + origin, "tags: " + tags,  "uplink: " + uplink ]
	return header

def readFile(filepath):
	with open(filepath, 'r') as file_object:
		lines = file_object.read().splitlines()

	fields = {}
	data = []
	
	for line in lines:
		key, match, end = parse_line(line, fields_dict)
		if (key):
			if key not in ['yaml_end_div', 'yaml_div', 'breadcrumb']:
				value = match.group('value')
				fields[key] = value
			continue
		line = parse_chunk(line)
		data.append(line)

	return data, fields


infile = sys.argv[1]
d, f = readFile(infile)
h = getHeader(f)
titleline = [f["id"] + " " + f["title"], ""]
out = "\n".join(titleline + d + [""] + h)

os.system("open ulysses://x-callback-url/new-sheet?text=" + urllib.parse.quote(out))