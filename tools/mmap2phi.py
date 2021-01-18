#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os, sys
from urllib.parse import quote
from collections import OrderedDict

MINDNODE_URI='mindnode:/'
MINDNODE_PHI_PATH = 'phi'


rx_dict = OrderedDict([
#	('task', re.compile(r'\[(?P<status>.)\]\s+(?P<task>.*)')),
	('link', re.compile(r'\[(?P<anchor>.+)\]\(x-phi://(?P<link>\d{3,})\)')),
	('list_entry', re.compile(r'^\s*- (?P<entry>.*)$')),
	('atx_header', re.compile(r'^#+'))
])

title_rx = re.compile(r'(?P<id>\d{3,})\s+(?P<title>.+)$')

def parse_chunk(chunk):
	global rx_dict

	for key, rx in rx_dict.items():
		match = rx.search(chunk)
		if match:
			left_chunk = chunk[:match.end()]

			if (key == 'link'):
				value = match.group('anchor')
				link = match.group('link')
				left_chunk = rx_dict['link'].sub(value + " [[" + link + "]]", left_chunk)

#			if (key == 'list_entry'):
#				value = match.group('entry')
#				left_chunk = rx_dict['list_entry'].sub(value + ".", left_chunk)

			if (key == 'task'):
				value = match.group('status')
				task = match.group('task')
				left_chunk = rx_dict['task'].sub('- [' + value + '] ' + task, left_chunk)

			chunk = left_chunk + parse_chunk(chunk[match.end():])

	return chunk

def getHeader(zettel_id, title):
	header = [ "---", "title:\t'" + title + "'  ", "id:\t\tΦ" + zettel_id + "  ",
		'origin:\t' + MINDNODE_URI + '/open?name=' + quote(zettel_id + ' ' + title) + '.mindnode&path=' + MINDNODE_PHI_PATH ]

	header.append("...")
	header.append("")

	return header

def readFile(infile):
	global rx_dict

	data = []
	got_list_item = False
	atx_header = False
	got_blank = False

	with open(infile, 'r') as file_obj:
		lines = file_obj.read().splitlines()

	for line in lines:
		line = parse_chunk(line)
		atx_header = rx_dict['atx_header'].search(line)

		if atx_header and got_blank:
			data.append('')
		if (line != '') or not got_list_item:
			data.append(line)
		if (line != ''):
			got_list_item = rx_dict['list_entry'].search(line)
			got_blank = False
		else:
			got_blank = True

	h = getHeader(phi_id, title)
	return h + data

phi_dir = sys.argv[1]
infile = sys.argv[2]
title_basename = os.path.splitext(os.path.basename(infile))[0]

match = title_rx.search(title_basename)
if not match:
	raise Exception("Invalid file name for note detected in the first line")

phi_id = match.group('id')
title = match.group('title')
out_filename = phi_dir + '/' + phi_id + ' ' + title + '.markdown'

d = readFile(infile)

with open(out_filename, 'w') as f_out:
	for l in d:
		f_out.write("%s\n" % l)




