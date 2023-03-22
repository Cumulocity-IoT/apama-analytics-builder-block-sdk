#!/usr/bin/env python3

# $Copyright (c) 2019 Software AG, Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA, and/or its subsidiaries and/or its affiliates and/or their licensors.$
# Use, reproduction, transfer, publication or disclosure is prohibited except as specifically provided for in your License Agreement with Software AG
import os, buildExtension, zipfile

def add_arguments(parser):
    """ Add parser arguments. """
    #these are optional arguments, requires at least one of them to perform upload or delete
    parser.add_argument('--input', metavar='PATH', type=str, required=False,
                        help='path to a zip file to upload as an extension')
    parser.add_argument('--name', type=str, required=False, help='the extension name in the inventory')

    remote = parser.add_argument_group(
        'upload or delete (requires at least the following arguments: --cumulocity_url, --username, --password, (--input or --name))')
    remote.add_argument('--cumulocity_url', metavar='URL', help='the base Cumulocity URL')
    remote.add_argument('--username',
                        help='the Cumulocity tenant identifier and the username in the <tenantId>/<username> format')
    remote.add_argument('--password', help='the Cumulocity password')
    remote.add_argument('--delete', action='store_true', default=False, help='delete the extension from the inventory')
    remote.add_argument('--restart', action='store_true', default=False,
                        help='restart the apama-ctrl')
    remote.add_argument('--ignoreVersion', action='store_true', default=False, required=False,
                        help='ignore the analytics builder script version check')

def run(args):
    # Support remote operations and whether they are mandatory.
    remote = {'cumulocity_url': True, 'username': True, 'password': True, 'name': False, 'delete': False,
              'restart': False}

    # checks if all manadatory remote options are provided
    buildExtension.isAllRemoteOptions(args,remote)
    if args.input:
        if not os.path.exists(args.input):
            raise Exception(f'Provide a valid path to the .zip file.')
        if not os.path.basename(args.input).endswith('.zip'):
            raise Exception(f'Argument --input has to be in a .zip format.')
        zf = zipfile.ZipFile(os.path.abspath(args.input))
        for zinfo in zf.infolist():
            is_encrypted = zinfo.flag_bits & 0x1
            if is_encrypted:
                raise Exception(f'File <{zinfo.filename}> is encrypted. Please upload a password free file.')

        # using the basename of the zip file as the name, if name is not specified
        if not args.name:
            try:
                args.name = os.path.basename(args.input).split('.')[0]
            except Exception as ex:
                raise Exception(
                    f'Unable to map input basename to --name, if not specified.')

    else:
        # allowed restart with no other option 
        if (args.restart and args.name and not args.delete) or (not args.restart and not args.delete):
            raise Exception(f'Argument --input is required when not deleting an extension.')
        if args.delete and not args.name:
            raise Exception(f'Arguments --input or --name is needed to delete an extension.')
    return buildExtension.upload_or_delete_extension(args.input, args.cumulocity_url, args.username, args.password, args.name,
                                      args.delete, args.restart, args.ignoreVersion, printMsg=True)
