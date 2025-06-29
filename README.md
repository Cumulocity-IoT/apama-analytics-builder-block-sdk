# Apama Analytics Builder Block SDK

This is a Software Development Kit (SDK) for producing blocks for the Apama Analytics Builder.

## Disclaimer

These tools are provided as-is and without warranty or support. They do not constitute part of the product suite. Users are free to use, fork and modify them, subject to the license agreement. While we welcome contributions, we cannot guarantee to include every contribution in the main project.

## Licensing

Copyright 2019-present Cumulocity GmbH

This project is licensed under the Apache 2.0 license - see <https://www.apache.org/licenses/LICENSE-2.0>

This excludes the Analytics Framework 'CDP' file, which is provided in binary form only for the purpose of testing.

## Analytics Builder version

Use the 'main' branch for the current release or switch to the appropriate branch for Long-term support (LTS) / Maintenance releases.

## System requirements

This script requires an installation of Python 3.7+ and runs on either Windows or Linux. To build extensions or edit them using the [Apama extension for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=ApamaCommunity.apama-extensions), a `dev` installation of the latest Apama is required. You can download the package from [Apama Downloads](https://download.cumulocity.com/Apama). If you choose to install Apama, you can skip the manual installation of Python, as it is shipped with Apama.

Alternatively, the [apama-builder](https://gallery.ecr.aws/apama/apama-builder) Docker image from Amazon ECR Public Gallery can also be used for building and managing extensions.

Note that Analytics Builder requires your Cumulocity tenant to be subscribed to an 'apama-ctrl' microservice.  The 'apama-ctrl-starter' microservice offers only restricted functionality and does not support custom blocks.

## Documentation

The guide to writing blocks is available in the [doc directory](doc/000-contents.md) and there is [ApamaDoc reference](https://cumulocity-iot.github.io/apama-analytics-builder-block-sdk/doc/apamadoc/index.html) available.

## Getting started

From an Apama command prompt:

* Run sample tests (Unix):

```bash
export ANALYTICS_BUILDER_SDK=`pwd`
cd samples/tests
pysys run
```

* Package samples as an extension and upload:

```bash
analytics_builder build extension --input samples/blocks --cumulocity_url <URL> --username <tenantID>/<username> --password <password> --name sample-blocks --restart
```
> **Note:** After running the above command, the apama-ctrl microservice will be restarted.

## Change Log

See [Change Log](CHANGELOG.md) for changes.

## Migration of input and output blocks to the version 2 API

See [Migrating input and output blocks to the version 2 API](doc/150-MigrateInputOutputBlocks.md) for details on migrating custom input and output blocks to the version 2 API.
