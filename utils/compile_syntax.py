#  sfzen/utils/compile_syntax.py
#
#  Copyright 2024 liyang <liyang@veronica>
#
import os, logging, yaml, importlib
from numbers import Real
from pretty_repr import Repr

def inspect(obj):
	print(type(obj).__name__)
	for k in dir(obj):
		if k[0] != '_':
			print(k, ':', type(getattr(obj, k)).__name__)
	print()

def compile_syntax(yaml_file, target_file):
	with open(yaml_file) as ymlfile:
		syntax = yaml.load(ymlfile, Loader=yaml.SafeLoader)
	with open(target_file, 'w') as pyfile:
		pyfile.write('SYNTAX = ')
		Repr(syntax).write(pyfile)
	print(f'Wrote "{target_file}"')

def compile_opcodes(syntax_file, target_file):
	module = importlib.import_module('sfzen.syntax')
	opcodes = { opcode['name']: opcode for opcode in _extract_opcodes(module.SYNTAX['categories']) }
	with open(target_file, 'w') as pyfile:
		pyfile.write('OPCODES = ')
		Repr(opcodes).write(pyfile)
	print(f'Wrote "{target_file}"')
	module = importlib.import_module('sfzen.opcodes')
	print(f'Successfully imported sfzen.opcodes')

def _extract_opcodes(categories):
	for category in categories:
		opcodes = category.get('opcodes')
		if opcodes:
			yield from _iter_opcodes(opcodes, category['name'])
		types = category.get('types')
		if types:
			yield from _extract_opcodes(types)

def _iter_opcodes(opcodes, category):
	for opcode in opcodes:
		yield from _opcode_validator(opcode, category, None, None)

def _opcode_validator(opcode, category, op_name, mod_type):
	opcode_meta = {
		'name'		: opcode['name'],
		'ver'		: _ver_code(opcode.get('version', 'unknown')),
		'category'	: category,
		'modulates'	: op_name,
		'mod_type'	: mod_type
	}
	_extract_vdr_meta(opcode, opcode_meta)
	yield opcode_meta
	for alias in opcode.get('alias', []):
		alias_meta = {
			'name': alias['name'],
			'value': {'valid': "Alias(" + repr(opcode['name']) + ")"},
		}
		if 'version' in alias:
			alias_meta['ver'] = _ver_mapping[alias['version']]
		else:
			alias_meta['ver'] = opcode_meta['ver']
		yield alias_meta
		if 'modulation' in alias:
			yield from extract_modulation(
				category,
				alias['modulation'].items(),
				alias['name'])
	if 'modulation' in opcode:
		yield from extract_modulation(
			category,
			opcode['modulation'].items(),
			opcode['name'])


def extract_modulation(category, items, op_name):
	for mod_type, modulations in items:
		if isinstance(modulations, list):  # some are just checkmarks
			for mod in modulations:
				yield from _opcode_validator(mod, category, op_name, mod_type)


def _extract_vdr_meta(opcode, opcode_meta):
	for key in ('value', 'index'):
		if key in opcode:
			if key not in opcode_meta:
				opcode_meta[key] = {}
			opcode_meta[key]['valid'] = _validator(opcode[key])
			type_name = opcode[key].get('type_name')
			if type_name:
				opcode_meta[key]['type'] = type_name
			unit = opcode[key].get('unit')
			if unit:
				opcode_meta[key]['unit'] = unit

def _validator(data_value):
	if 'min' in data_value:
		if 'max' in data_value:
			if not isinstance(data_value['max'], Real):
				# string value, eg "SampleRate / 2"
				return "Min(" + repr(data_value['min']) + ")"
			return "Range(" + repr(data_value['min']) + ", " + repr(data_value['max']) + ")"
		return "Min(" + repr(data_value['min']) + ")"
	if 'options' in data_value:
		return "Choice(" + repr([o['name'] for o in data_value['options']]) + ")"
	return "Any()"


_ver_mapping = {
	None				: 'unknown',
	'SFZ v1'			: 'v1',
	'SFZ v2'			: 'v2',
	'ARIA'				: 'aria',
	'LinuxSampler'		: 'linuxsampler',
	'Cakewalk'			: 'cakewalk',
	'Cakewalk SFZ v2'	: 'cakewalk_v2',  # unimplementd by any player
}

def _ver_code(version):
	return _ver_mapping.get(version, version.lower())

if __name__ == "__main__":
	app_dir = os.path.dirname(os.path.dirname(__file__))
	yaml_file = os.path.join(app_dir, 'res', 'syntax.yml')
	syntax_file = os.path.join(app_dir, 'syntax.py')
	opcodes_file = os.path.join(app_dir, 'opcodes.py')
	if not os.path.exists(syntax_file):
		compile_syntax(yaml_file, syntax_file)
	if not os.path.exists(opcodes_file):
		compile_opcodes(syntax_file, opcodes_file)

#  end sfzen/utils/compile_syntax.py
