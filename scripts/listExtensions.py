#!/usr/bin/env python3

# Copyright (c) 2021-present Cumulocity GmbH, Duesseldorf, Germany and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except as specifically provided for in your License Agreement with Cumulocity GmbH
import os, urllib, buildExtension

def add_arguments(parser):
    """ Add parser arguments. """
    #these are the arguments that requires to list extensions
    remote = parser.add_argument_group(
        'list extensions requires the following arguments: --cumulocity_url, --username, --password, or their corresponding environment variables')
    remote.add_argument('--cumulocity_url', metavar='URL', help='the base Cumulocity URL (can also be set via CUMULOCITY_SERVER_URL environment variable)')
    remote.add_argument('--username',
                        help='the Cumulocity tenant identifier and the username in the <tenantId>/<username> format (can also be set via CUMULOCITY_USERNAME environment variable)')
    remote.add_argument('--password', help='the Cumulocity password (can also be set via CUMULOCITY_PASSWORD environment variable)')

def run(args):
    # Support remote operations and whether they are mandatory.
    remote = {'cumulocity_url': True, 'username': True, 'password': True}

    # checks if all manadatory remote options are provided
    buildExtension.prepareRemoteOptions(args,remote)
    connection = buildExtension.C8yConnection( args.cumulocity_url, args.username,args.password)
    try:
        extension_mos = connection.do_get('/inventory/managedObjects', {'fragmentType': "pas_extension", "pageSize": 2000})
        for mo in extension_mos['managedObjects']: 
            print(mo['pas_extension'])
    except urllib.error.HTTPError as err:
        if err.code == 404:
	        raise Exception(
		        f'Failed to perform REST request for resource /inventory/managedObjects on url {connection.base_url}. Verify that the base Cumulocity URL is correct.')
        raise err
