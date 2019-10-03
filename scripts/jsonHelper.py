#!/usr/bin/env python3

# $Copyright (c) 2019 Software AG, Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA, and/or its subsidiaries and/or its affiliates and/or their licensors.$
# Use, reproduction, transfer, publication or disclosure is prohibited except as specifically provided for in your License Agreement with Software AG
import json, os
from pathlib import Path

import buildExtension

ENCODING = 'UTF8'
BLOCK_METADATA_EVENT = buildExtension.BLOCK_METADATA_EVENT
BLOCK_MESSAGES_EVENT = buildExtension.BLOCK_MESSAGES_EVENT

def add_arguments_extract(parser):
	parser.add_argument('--input', metavar='INPUT', type=str, required=True, help='the input directory (should contain <name>-messages.json and <name>.json)')
	parser.add_argument('--output', metavar='OUTPUT', type=str, required=True, help='the output directory')

def add_arguments_pack(parser):
	parser.add_argument('--input', metavar='INPUT', type=str, required=True, help='the input directory (should contain <name>_messages.evt and <name>_metadata.evt)')
	parser.add_argument('--output', metavar='OUTPUT', type=str, required=True, help='the output directory')
	parser.add_argument('--name', metavar='NAME', type=str, required=True, help='the name of the block catalog')

def run_json_extract(args):
	input = Path(args.input).resolve()
	output = Path(args.output).resolve()
	for filename in list(input.rglob('*_messages.evt')) + list(input.rglob('*_metadata.evt')):
		with open(filename, encoding=ENCODING) as f:
			for line in f:
				suffix=None
				if line.startswith(BLOCK_METADATA_EVENT): suffix=''
				if line.startswith(BLOCK_MESSAGES_EVENT): suffix='-messages'
				if suffix != None:
					jsonversion = '['+line.split('(', 1)[1][0:-1]+']'
					(name, lang, jsonstr) = json.loads(jsonversion)
					(output / Path(lang)).mkdir(parents=True, exist_ok=True)
					with open(output / Path(lang) / Path(name+suffix+'.json'), 'w', encoding=ENCODING) as w:
						json.dump(json.loads(jsonstr), w, indent='\t')

def run_json_pack(args):
	input = Path(args.input).resolve()
	output = Path(args.output).resolve()
	name = args.name
	buildExtension.gen_messages_evt_file(name, input, output, {})
	metadata = Path(input / ('EN/' + name + '.json')).read_text(encoding=ENCODING)
	buildExtension.write_evt_file(output, f'{name}_metadata.evt', f'{BLOCK_METADATA_EVENT}("{name}", "EN", {buildExtension.embeddable_json_str(metadata)})')


