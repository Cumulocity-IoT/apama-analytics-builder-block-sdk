# Building a block into an extension

Once a block is written in EPL, it can be packaged into an "extension". Extensions are **.zip** files that can be used to add blocks to the Analytics Builder runtime. Analytics Builder is deployed within Cumulocity IoT, and extensions are stored in the inventory. The extensions are only read when the apama-ctrl microservice inside Cumulocity is started, so the service must be restarted to make use of a new block. Restarting the microservice will lose state in any running models or custom EPL applications running in that tenant. This SDK provides a command line utility called `analytics_builder` which is available in the root directory of the SDK. This can be used to build an extension or manage an extension in a Cumulocity IoT installation. You must navigate out of the model editor to the model manager and back to the editor to expose the new blocks after uploading an extension.

Most of the `analytics_builder` commands use a `--input` argument which specifies the path to a directory. All **.mon** files found under that directory will be included, and message files matching **\*-messages.json** or named **messages.json** will be used for the runtime messages. 

The `analytics_builder` script is run from an Apama command prompt (on Windows, run **Apama Command Prompt** from the Start Menu group of your Apama installation; on Linux, source the `apama_env` script). **Note:** You must place the script in a directory that does not have any spaces in its full path. 

The `analytics_builder` script takes a two-word command, followed by any arguments required by the command. Available commands are:

* `build extension --output <path to zip file>`

  Build an extension, generating a local **.zip** file. For example:

  ```bash
  analytics_builder build extension --input samples/blocks --output sample-blocks.zip
  ```

* `build extension --cumulocity_url <url> --username <user> --password <password> --name sample-blocks`

  Build and upload an extension to a Cumulocity IoT instance. For example:

  ```bash
  analytics_builder build extension --input samples/blocks --cumulocity_url https://demo.cumulocity.com/ --username tenantID/user --password pass
  ```

* `upload extension --cumulocity_url <url> --username <user> --password <password> --input <path to zip file>`

  Upload an extension to a Cumulocity IoT instance.  Note that the 'apama-ctrl-starter' version of Apama in Cumulocity IoT does not support extensions and thus you cannot use it for custom blocks.
  Ask your support contact to upgrade to a fully-featured version of apama-ctrl.


* `build metadata --output <json file>`

  Build JSON metadata only. This can be useful for reviewing what is extracted from the block and visible in the model editor. For example:

  ```bash
  analytics_builder build metadata --input samples/blocks  --output samples.json
  ```

* `configure designer`

  Configure Software AG Designer with the location of the block SDK.  See [Using Software AG Designer](007-UsingDesigner.md).

* `json extract --output <path to directory>` or `json pack --output <path to directory>`

  Extract or pack message or metadata JSON files from/to event files. This allows the metadata or the messages to be edited as JSON.

See the `analytics_builder --help` output for full details of the options.

## Common options

For `build extension` and `upload extension`:

* The `--username` argument can also take the tenant identifier along with user name in the format `tenantID/username`.  The user must have the 'Inventory - CREATE' permission to upload an extension.
* Specify `--restart` to request a restart of the apama-ctrl service.  The user must have the 'CEP management - ADMIN' permission to request a restart.
* Specify `--delete` and `--name <base name of extension>` to delete a previously uploaded extension.
* Specify `--ignoreVersion` to not check whether the script and apama-ctrl service are of the same version.


**Note:** If you wish to use the samples provided in the **samples** directory as the starting point for your own blocks, it is strongly recommended that you:

* Make a copy of the contents of the **samples** directory.
* Change the package name (and if appropriate, the block names) of the blocks.

This avoids any confusion as to the functionality and ownership of the blocks. The samples are not productized blocks, and are subject to removal or changes in future releases without notice.

[< Prev: Naming and documenting blocks](020-NamingAndDoc.md) | [Contents](000-contents.md) | [Next: Testing blocks >](035-Testing.md) 
