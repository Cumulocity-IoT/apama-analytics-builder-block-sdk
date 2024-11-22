#!/usr/bin/env python3

# $Copyright (c) 2019-2022 Software AG, Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA, and/or its subsidiaries and/or its affiliates and/or their licensors.$
# Use, reproduction, transfer, publication or disclosure is prohibited except as specifically provided for in your License Agreement with Software AG
import shutil, json, os, subprocess, urllib
import blockMetadataGenerator, buildVersions
from pathlib import Path
import ssl, urllib.parse, urllib.request, base64, sys

ENCODING = 'UTF8'
BLOCK_METADATA_EVENT = 'apama.analyticsbuilder.BlockMetadata'
BLOCK_MESSAGES_EVENT = 'apama.analyticsbuilder.BlockMessages'
PAS_EXT_TYPE = 'pas_extension'	# Type of the ManagedObject containing information about extension zip.
PAS_EXT_ID_FIELD = 'pas_extension_binary_id' # The field of the ManagedObject with id of the extension zip binary object.
BLOCK_REGISTRY_CHANNEL = 'analyticsbuilder.metadata.requests'
UNSUPPORTED_FILE_TYPES = ('.log','.classpath','.dependencies','.project','.deploy','.launch','.out','.o') # Files to exclude

def add_arguments(parser):
	""" Add parser arguments. """
	parser.add_argument('--input', metavar='DIR', type=str, required=False, help='the input directory containing extension files - required when not deleting an extension')
	parser.add_argument('--cdp', action='store_true', default=False, required=False, help='package all EPL files into a single CDP file')
	parser.add_argument('--priority', metavar='N', type=int, required=False, help='the priority of the extension')
	parser.add_argument('--folderToSkip', action='append', required=False, help='the list of folders to skip from building extension.')

	local = parser.add_argument_group('local save (requires at least the following arguments: --input, and --output)')
	local.add_argument('--output', metavar='ZIP_FILE', type=str, required=False, help='the output zip file (requires the --input argument)')

	remote = parser.add_argument_group('remote upload or delete (requires at least the following arguments: --cumulocity_url, --username, --password, and --name)')
	remote.add_argument('--cumulocity_url', metavar='URL', help='the base Cumulocity URL')
	remote.add_argument('--username', help='the Cumulocity tenant identifier and the username in the <tenantId>/<username> format')
	remote.add_argument('--password', help='the Cumulocity password')
	remote.add_argument('--name', help='the extension name in the inventory')
	remote.add_argument('--delete', action='store_true', default=False, help='delete the extension from the inventory')
	remote.add_argument('--restart', action='store_true', default=False, help='restart the apama-ctrl after upload or delete operation')
	remote.add_argument('--ignoreVersion', action='store_true', default=False, required=False,
						help='ignore the analytics builder script version check')

def write_evt_file(ext_files_dir, name, event):
	"""
	Append event into the evt file of the extension.
	:param ext_files_dir: The 'files' directory of the extension.
	:param name: Name of the evt file
	:param event: The event to append.
	:return:
	"""
	events_dir = ext_files_dir / 'events'
	events_dir.mkdir(parents=True, exist_ok=True)
	with open(events_dir / name, mode='w+', encoding='UTF8') as f:
		return f.writelines([event])

def embeddable_json_str(json_str):
	"""Return JSON string which could be included in a string literal of an event string."""
	s = json.dumps(json.loads(json_str), separators=(',', ':'))
	return json.dumps(s)

def gen_messages_evt_file(name, input, ext_files_dir, messages_from_metadata):
	"""
	Generate evt file containing event string for sending message JSON.
	:param name: Extension name.
	:param input: The input directory containing messages JSON files.
	:param ext_files_dir: The 'files' directory of the extension.
	:param messages_from_metadata: Extra messages to include extracted from blocks' metadata.
	:return: None
	"""
	all_msgs = messages_from_metadata.copy()
	msg_to_files = {}
	msg_files = list(input.rglob('messages.json')) + list(input.rglob('*-messages.json'))
	for f in msg_files:
		try:
			data = json.loads(f.read_text(encoding=ENCODING))
			if not isinstance(data, dict):
				print(f'Skipping JSON file with invalid messages format: {str(f)}')
				continue
			for (k, v) in data.items():
				if k in all_msgs:
					print(f'Message {k} defined multiple times in "{msg_to_files[k]}" and "{f}".')
				else:
					all_msgs[k] = v
					msg_to_files[k] = f
		except:
			print(f'Skipping invalid JSON file: {str(f)}')

	write_evt_file(ext_files_dir, f'{name}_messages.evt',
				   f'"{BLOCK_REGISTRY_CHANNEL}",{BLOCK_MESSAGES_EVENT}("{name}", "EN", {embeddable_json_str(json.dumps(all_msgs))})')


def createCDP(name, mons, ext_files_dir):
	"""
	Package mon files into a CDP file.
	:param name: The name of the CDP file.
	:param mons: The mon files to include in the CDP file.
	:param ext_files_dir: Output directory for the CDP file.
	:return: None
	"""
	cmd = [
		os.path.join(os.getenv('APAMA_HOME'), 'bin', 'engine_package'),
		'-u',
		'-o', os.path.join(ext_files_dir, name+'.cdp'),
	] + [str(f) for f in mons]

	subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE).check_returncode()

   

def build_extension(input, output, tmpDir, cdp=False, priority=None, printMsg=False,folderToSkip=None):
	"""
	Build an extension from specified input directory.
	:param input: The input directory containing artifacts for the extension.
	:param output: The output zip file for the extension.
	:param tmpDir: The temporary directory.
	:param cdp: Package all monitors into a CDP file.
	:param priority: The priority of the package.
	:param printMsg: Print success message with location of the extension zip.
	:param folderToSkip: The list of directories to skip from build.
	:return:
	"""
	input = Path(input).resolve()
	output = Path(output).resolve()
	tmpDir = Path(tmpDir).resolve()
	if folderToSkip is None: folderToSkip = list()

	if not input.exists():
		raise Exception(f'Input directory does not exist: {input.absolute()}')

	name = output.name	# catalog name
	if name.endswith('.zip'):
		name = name[:-4]
		output = output.with_name(name)

	ext_dir = tmpDir / name				# '/' operator on Path object joins them
	ext_files_dir = ext_dir / 'files'
	ext_files_dir.mkdir(parents=True, exist_ok=True)

	# Define priority of the extension if specified
	if priority is not None:
		ext_dir.joinpath('priority.txt').write_text(str(priority), encoding=ENCODING)
	
	files_to_copy = []

	# Create CPD or copy mon files to extension directory while maintaining structure
	mons = list(input.rglob('*.mon'))
	if cdp:
		createCDP(name, mons, ext_files_dir)
	else:
		files_to_copy.extend(mons)
	
	# Adding all the files
	all_files = list(input.rglob('*.*'))

	# Excluding UNSUPPORTED_FILE_TYPES from all_files
	for file in all_files:
		if not str(file).endswith(UNSUPPORTED_FILE_TYPES + ('.mon',)):# mon files are already included in files_to_copy
			files_to_copy.append(file)

	filtered_files = list() if len(folderToSkip) > 0 else files_to_copy
	
	if len(folderToSkip) > 0:
		for f in files_to_copy:
			if not any(folder in str(f.relative_to(input).parent) for folder in folderToSkip):
				filtered_files.append(f)
		
			
	for p in filtered_files:
		target_file = ext_files_dir / p.relative_to(input)
		target_file.parent.mkdir(parents=True, exist_ok=True)
		shutil.copy2(p, target_file)

	# Generate block metadata
	metadata_tmp_dir = tmpDir / 'metadata'
	(metadata_json_file, messages) = blockMetadataGenerator.run_metadata_generator(input, str(metadata_tmp_dir / name), str(metadata_tmp_dir))

	if metadata_json_file:
		# Write evt file for metadata events
		metadata = Path(metadata_json_file).read_text(encoding=ENCODING)
		write_evt_file(ext_files_dir, f'{name}_metadata.evt', f'"{BLOCK_REGISTRY_CHANNEL}",{BLOCK_METADATA_EVENT}("{name}", "EN", {embeddable_json_str(metadata)})')

	# Collate all the messages from the messages.json and *-messages.json
	gen_messages_evt_file(name, input, ext_files_dir, messages)

	# Create zip of extension
	shutil.make_archive(output, format='zip', root_dir=ext_dir)
	if printMsg:
		print(f'Created {output}.zip')
	return output.absolute().with_suffix('.zip')

class C8yConnection(object):
	"""
	Simple object to create connection to Cumulocity and perform REST requests.
	"""
	def __init__(self, url, username, password):
		if not (url.startswith('http://') or url.startswith('https://')):
			url = 'https://' + url
		auth_handler = urllib.request.HTTPBasicAuthHandler()
		auth_handler.add_password(realm='Name of Your Realm',
								  uri=url,
								  user=username,
								  passwd=password)
		auth_handler.add_password(realm='Cumulocity',
								  uri=url,
								  user=username,
								  passwd=password)
		ctx = ssl.create_default_context()
		ctx.check_hostname = False
		ctx.verify_mode = ssl.CERT_NONE
		self.urlopener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx, check_hostname=False), auth_handler)
		self.base_url = url
		self.auth_header = "Basic " + base64.b64encode(bytes("%s:%s" % (username, password), "utf8")).decode()

	def request(self, method, path, body=None, headers=None):
		"""
		Perform an HTTP request. In case of POST request, return the id of the created resource.
		:param method: The method.
		:param path: The path of the resource.
		:param body: The body for the request.
		:param headers: The headers for the request.
		:return: Body of the response. In case of POST request, id of the resource specified by the Location header.
		"""
		headers = headers or {}
		headers['Authorization'] = self.auth_header
		if isinstance(body, str):
			body = bytes(body, encoding=ENCODING)
		url = self.base_url[:-1] if self.base_url.endswith('/') else self.base_url
		req = urllib.request.Request(url + path, data=body, headers=headers, method=method)
		resp = self.urlopener.open(req)
		if resp.getheader('Content-Type', '') == 'text/html': # we never ask for HTML, if we got it, this is probably the wrong URL (or we're very confused)
			raise urllib.error.HTTPError(url, 404, resp.getheaders(), f'Failed to perform REST request for resource {path} on url {self.base_url}. Verify that the base Cumulocity URL is correct.', None)


		# return the object id if POST
		if method == 'POST':
			loc = resp.getheader('Location', None)
			if loc.endswith('/'): loc = loc[:-1]
			return loc.split('/')[-1]
		return resp.read()

	def do_get(self, path, params=None, headers=None, jsonResp=True):
		"""
		Perform GET request.
		:param path: The path to the resource.
		:param params: The query params.
		:param headers: The headers.
		:param jsonResp: Response is JSON.
		:return: The body of the response. If JSON output is expected then parse the JSON string to python object.
		"""
		if params:
			path = f'{path}?{urllib.parse.urlencode(params)}'
		body = self.request('GET', path, None, headers)
		if body and jsonResp:
			body = json.loads(body)
		return body

	def do_request_json(self, method, path, body, headers=None):
		"""
		Perform REST request (POST/GET mainly) with JSON body.
		:param method: The REST method.
		:param path: The path to resource.
		:param body: The JSON body.
		:param headers: The headers.
		:return: Response body string.
		"""
		headers = headers or {}
		headers['Content-Type'] = 'application/json'
		body = json.dumps(body)
		return self.request(method, path, body, headers)

def upload_new_extension(connection, f, extension_name):
	"""
	Create multi-form payload and header for REST request to upload the specified file.
	:param connection: Object to perform REST requests.
	:param f: The file to upload.
	:param extension_name: Name of the extension to create.
	:return: None
	"""
	formBoundary = '----PASExtension3XtDFfhJ8XLIrkPw'
	headers = {
		'Accept': '*/*',
		'Content-Type': f'multipart/form-data; boundary={formBoundary}',
		'Content': 'multipart/form-data'
	}
	file_content = Path(f).read_bytes()
	formBoundary = '--' + formBoundary
	filename = extension_name + '.zip'
	body = bytearray('%s\r\nContent-Disposition: form-data; name="object"\r\n\r\n{"name":"%s","type":"application/zip","pas_extension":"%s"}\r\n' % (formBoundary, filename, extension_name), encoding=ENCODING)
	body += bytearray('%s\r\nContent-Disposition: form-data; name="filesize"\r\n\r\n%s\r\n' % (formBoundary, len(file_content)), encoding=ENCODING)
	body += bytearray('%s\r\nContent-Disposition: form-data; name="file"; filename="%s"\r\nContent-Type: application/zip\r\n\r\n' % (formBoundary, filename), encoding=ENCODING)
	body += file_content
	body += bytearray(f'\r\n{formBoundary}--', encoding=ENCODING)
	try:
		connection.request('POST', '/inventory/binaries', body, headers)
	except Exception as ex:
		raise Exception(f'Unable to upload extension using POST on /inventory/binaries: {ex}')

def replace_extension_content(connection, f, moId):
	"""
	Replace content of existing extension.
	:param connection: Object to perform REST requests.
	:param f: The zip file.
	:param moId: The id of the extension object.
	:return: None
	"""
	file_content = Path(f).read_bytes()
	headers = {
		'Accept': '*/*',
		'Content-Type': f'application/zip',
	}
	try:
		connection.request('PUT', f'/inventory/binaries/{moId}', file_content, headers)
	except Exception as ex:
		raise Exception(f'Unable to replace extension content using PUT on /inventory/binaries/{moId}: {ex}')

def upload_or_delete_extension(extension_zip, url, username, password, name, delete=False, restart=False, ignoreVersion=False, printMsg=False):
	"""
	Upload the extension to the Cumulocity inventory or delete the extension from the inventory.
	:param extension_zip: The extension zip to upload.
	:param url: The Cumulocity URL.
	:param username: The username.
	:param password: The password.
	:param name: The name of the extension.
	:param delete: Delete the extension instead of uploading it.
	:param restart: Restart the apama-ctrl after uploading the extension.
	:param ignoreVersion: Ignores block sdk version.
	:param printMsg: Print the success message.
	:return:
	"""
	connection = C8yConnection(url, username, password)
	
	# checks Analytics builder version with Apama-ctrl version
	checkVersions(connection, ignoreVersion)
	checkIfStarter(connection, ignoreVersion)
	
	# Get existing ManagedObject for PAS extension.
	try:
		extension_mos = connection.do_get('/inventory/managedObjects', {'query': f"pas_extension eq '{name}'"})
	except urllib.error.HTTPError as err:
		if err.code == 404:
			raise Exception(
				f'Failed to perform REST request for resource /inventory/managedObjects on url {connection.base_url}. Verify that the base Cumulocity URL is correct.')
		raise err
	
	extension_mo = None
	if extension_mos:
		extension_mos = extension_mos.get('managedObjects', [])
		extension_mo = extension_mos[0] if len(extension_mos) == 1 else None
		if len(extension_mos) > 1:
			raise Exception(f'Multiple Managed Objects found with pas_extension={name}. Delete them to upload a new extension with the same name.')

	if extension_mo:
		moId = extension_mo["id"]
		if delete:
			try:
				connection.request('DELETE', f'/inventory/binaries/{moId}')
			except Exception as ex:
				raise Exception(f'Unable to delete extension using DELETE on /inventory/binaries/{moId}: {ex}')
			if printMsg: print(f'Deleted extension {name}')
		else:
			replace_extension_content(connection, extension_zip, moId)
			if printMsg: print(f'Uploaded extension {name}')
	else:
		if delete:
			print('Extension already deleted')
		elif name:
			upload_new_extension(connection, extension_zip, name)
			if printMsg: print(f'Uploaded extension {name}')

	if restart:
		try:
			connection.request('PUT', f'/service/cep/restart')
			if printMsg: print('Restart requested')
		except (urllib.error.HTTPError, urllib.error.URLError) as ex:
			statuscode = int(ex.code)
			if statuscode // 10 == 50:
				if printMsg: print('Restart requested')
			else:
				raise Exception(f'Failed to restart Apama-ctrl: {ex}')
		except Exception as ex:
			raise Exception(f'Failed to restart Apama-ctrl: {ex}')

def isAllRemoteOptions(args, remote):
		for k, v in remote.items():
			if v and getattr(args, k, None) is None:
				raise Exception(f'Argument --{k} is required for the remote operation.')

def checkIfStarter(connection,ignoreVersion):
	is_starter = None
	try:
		resp = connection.request('GET',f'/service/cep/diagnostics/apamaCtrlStatus')
		is_starter = (json.loads(resp).get('is_starter_mode'))		
	except urllib.error.HTTPError as err:
		print(f'Could not identify Apama-ctrl : {err}')	
	if is_starter == True:
		if ignoreVersion:
			print(f'WARNING: Uploaded extensions are not supported in Apama Starter so they will not be available in the model editor.')
		else:
			print(f'FAILED: Extensions are not supported in Apama Starter. Ignore the check using --ignoreVersion')
			exit()

def checkVersions(connection, ignoreVersion):
	
	apamactrl_version = None
	git_url = 'https://github.com/Cumulocity-IoT/apama-analytics-builder-block-sdk/releases'

	try:
		resp = connection.request('GET', f'/service/cep/diagnostics/componentVersion')
		apamactrl_version = json.loads(resp).get('releaseTrainVersion')
		
	except urllib.error.HTTPError as err:
		microserviceNotSubscribed=False
		if err.code == 404:
			if 'Content-Type' in err.headers and 'application/json' in err.headers['Content-Type']:
				try:
					errMsg = json.load(err)
					if 'error' in errMsg and 'microservice/' in errMsg['error']:
						microserviceNotSubscribed=True
				except:
					pass # mal-formed error response, suggests it's something else.
		if err.code == 404 and not microserviceNotSubscribed:
			# if it's a 404 and not a microservice not subscribed error, this is a 404 from the microservice itself.
			if ignoreVersion:
				print(f'WARNING: It is recommended to use the Analytics Builder script only against Apama-ctrl with the same version.', file=sys.stderr)
			else:
				raise Exception(f'Failed to perform REST request for resource /diagnostics/componentVersion on url {connection.base_url} (HTTP status {err.code}). A user using a Cumulocity tenant version ({apamactrl_version}) has to checkout the latest and compatible version of the branch, for example if using the cloned github repository, switch to the 10.5.0.x branch using git checkout rel/10.5.0.x. Else download the latest release of 10.5.0.x from {git_url}.')


		else:
			if err.code >= 400:
				if not ignoreVersion:
					ignoreVersion= True
					print(f'WARNING: apama-ctrl may not be running, skipping version check.', file=sys.stderr)
					apamactrl_version = 'Unknown'
			else:
				raise err
	
	sdk_version = buildVersions.RELEASE_TRAIN_VERSION
	
	if apamactrl_version is not None and apamactrl_version != sdk_version:
		
		if ignoreVersion:
			print(f'WARNING: It is recommended to use the Analytics Builder script only against Apama-ctrl with the same version. The version of the Analytics Builder script is {sdk_version} but the version of Apama-ctrl is {apamactrl_version}.')
		else:
			raise Exception(f'The apama analytics builder block sdk version has to be compatible with the apama-ctrl microservice version. Please download the latest block sdk release for v{apamactrl_version} from https://github.com/Cumulocity-IoT/apama-analytics-builder-block-sdk/releases. If you have cloned the git repository then checkout/switch to the branch that\'s compatible with the version of the apama-ctrl microservice. For example, if the apama-ctrl microservice release train version is {apamactrl_version} switch to {apamactrl_version}.x branch using \'git checkout rel/{apamactrl_version}.x\'. You can also provide the --ignoreVersion command line option if you want to ignore the version compatibility check.')

def run(args):
	# Support remote operations and whether they are mandatory.
	remote = {'cumulocity_url':True, 'username':True, 'password':True, 'name':True, 'delete':False, 'restart':False}

	# Check if any remote option is provided
	is_remote = False
	for k in remote.keys():
		if getattr(args, k, None):
			is_remote = True
			break

	# check all mandatory remote options are provided
	if is_remote:
		isAllRemoteOptions(args, remote)

	# check either output or mandatory remote options are provided.
	if not (is_remote or args.output):
		raise Exception(f'Provide arguments to save the extension locally, perform remote operations or both.')

	if not args.input and not args.delete:
		raise Exception(f'Argument --input is required when not deleting an extension')


	zip_path = Path(args.tmpDir, args.name).with_suffix('.zip') if is_remote else args.output # Use the <name>.zip for the zip name which gets uploaded.
	if not args.delete:
		zip_path = build_extension(args.input, zip_path, args.tmpDir, args.cdp, args.priority, printMsg=bool(args.output),folderToSkip=args.folderToSkip)
	if is_remote:
		if args.output and not args.delete:
			output = args.output + ('' if args.output.endswith('.zip') else '.zip')
			shutil.copy2(zip_path, output)
		return upload_or_delete_extension(zip_path, args.cumulocity_url, args.username,
										  args.password, args.name, args.delete, args.restart, args.ignoreVersion, printMsg=True)
