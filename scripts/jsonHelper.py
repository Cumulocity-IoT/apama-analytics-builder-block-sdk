#!/usr/bin/env python3

# Copyright (c) 2019-present Cumulocity GmbH, Duesseldorf, Germany and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except as specifically provided for in your License Agreement with Cumulocity GmbH
import json, os, sys, re
from pathlib import Path

import buildExtension

ENCODING = 'UTF8'
BLOCK_METADATA_EVENT = buildExtension.BLOCK_METADATA_EVENT
BLOCK_MESSAGES_EVENT = buildExtension.BLOCK_MESSAGES_EVENT
BLOCK_REGISTRY_CHANNEL = buildExtension.BLOCK_REGISTRY_CHANNEL
LOCALES = 'EN,DE,PL,PT_BR,ZH_CN,ZH_TW,NL,FR,JA_JP,KO,RU,ES'

def add_arguments_extract(parser):
	parser.add_argument('--input', metavar='INPUT', type=str, required=True, help='the input directory (should contain <name>_messages.evt and <name>_metadata.evt)')
	parser.add_argument('--output', metavar='OUTPUT', type=str, required=True, help='the output directory')

def add_arguments_pack(parser):
	parser.add_argument('--input', metavar='INPUT', type=str, required=True, help='the input directory (should contain <name>-messages.json and <name>.json)')
	parser.add_argument('--output', metavar='OUTPUT', type=str, required=True, help='the output directory')
	parser.add_argument('--name', metavar='NAME', type=str, required=True, help='the name of the block catalog')

def run_json_extract(args):
	input = Path(args.input).resolve()
	output = Path(args.output).resolve()
	for filename in list(input.rglob('*_messages.evt')) + list(input.rglob('*_metadata.evt')):
		with open(filename, encoding=ENCODING) as f:
			for line in f:
				suffix=None
				if line.find(BLOCK_METADATA_EVENT) != -1: suffix=''
				if line.find(BLOCK_MESSAGES_EVENT) != -1: suffix='-messages'
				if suffix != None:
					#Get all characters between first and last parenthesis
					pattern = r'\((.*)\)'
					jsonversion = '['+ re.search(pattern,line).group(1) + ']'
					(name, lang, jsonstr) = json.loads(jsonversion)
					(output / Path(lang)).mkdir(parents=True, exist_ok=True)
					with open(output / Path(lang) / Path(name+suffix+'.json'), 'w', encoding=ENCODING) as w:
						json.dump(json.loads(jsonstr), w, indent='\t')

def run_json_pack(args):
	input = Path(args.input).resolve()
	output = Path(args.output).resolve()
	name = args.name
	buildExtension.gen_messages_evt_file(name, input, output, {})
	packed = False
	for locale in LOCALES.split(','):
		if os.path.exists(Path(input / (f'{locale}/'))):
			if not packed:
				# First time writing to evt file, clear existing contents, so that each locale can be appended.
				packed = True
				outFile = Path(output / 'events' / f'{name}_metadata.evt')
				if os.path.exists(outFile):
					os.remove(outFile)
			metadata = Path(input / (f'{locale}/' + name + '.json')).read_text(encoding=ENCODING)
			buildExtension.write_evt_file(output, f'{name}_metadata.evt', f'"{BLOCK_REGISTRY_CHANNEL}",{BLOCK_METADATA_EVENT}("{name}", "{locale}", {buildExtension.embeddable_json_str(metadata)})')

	if not packed:
		print(f"Error during pack: Failed to find a directory with supported locales at '{input}/'. Supported locales: {LOCALES}", file=sys.stderr)

