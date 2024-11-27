# Building a block into an extension

Once a block is written in EPL, it can be packaged into an "extension". Extensions are **.zip** files that can be used to add blocks to the Analytics Builder runtime. Analytics Builder is deployed within Cumulocity IoT, and extensions are stored in the inventory. The extensions are only read when the Apama-ctrl microservice inside Cumulocity IoT is started, so the service must be restarted to make use of a new block. Restarting the microservice will lose state in any running models or custom EPL applications running in that tenant. This SDK provides a command line utility called `analytics_builder` which is available in the root directory of the SDK. This can be used to build an extension or list an extension or manage an extension in a Cumulocity IoT installation. You must navigate out of the model editor to the model manager and back to the editor to expose the new blocks after uploading an extension.

Most of the `analytics_builder` commands use an `--input` argument that specifies the path to a directory. All files in that directory are included in the **.zip** file, except for the files with the following extensions: **.log**, **.classpath**, **.dependencies**, **.project**, **.deploy**, **.launch**, **.out**, and **.o**. Files in the **.git** and **.github** subdirectories are also not included. The message files named **messages.json** or matching **\*-messages.json** are used for the runtime messages.

The `analytics_builder` script is run from an Apama command prompt (on Windows, run **Apama Command Prompt** from the Start Menu group of your Apama installation; on Linux, source the `apama_env` script). **Note:** You must place the script in a directory that does not have any spaces in its full path. 

The `analytics_builder` script takes a two-word command, followed by any arguments required by the command. Available commands are:

* `build extension --output <path to zip file>`

  Build an extension, generating a local **.zip** file. For example:

  ```bash
  analytics_builder build extension --input samples/blocks --output sample-blocks.zip
  ```

* `build extension --cumulocity_url <url> --username <user> --password <password> --name sample-blocks`

*  A full version of Apama is required for building an extension.

  Build and upload an extension to a Cumulocity IoT instance. For example:

  ```bash
  analytics_builder build extension --input samples/blocks --cumulocity_url https://demo.cumulocity.com/ --username tenantID/user --password pass
  ```

* `build extension --cumulocity_url <url> --username <user> --password <password> --folderToSkip <folder_name>`

  Build and upload an extension to a Cumulocity IoT instance by skipping uninteresting folders from the build. For example:

  ```bash
  analytics_builder build extension --input samples/blocks --cumulocity_url https://demo.cumulocity.com/ --username tenantID/user --password pass --folderToSkip temp --folderToSkip temp1
  ```

* `upload extension --cumulocity_url <url> --username <user> --password <password> --input <path to zip file>`

  Upload an extension to a Cumulocity IoT instance.  Note that the 'apama-ctrl-starter' version of Apama in Cumulocity IoT does not support extensions and thus you cannot use it for custom blocks.
  Ask your support contact to upgrade to a fully-featured version of the Apama-ctrl microservice.

* `list extensions --cumulocity_url <url> --username <user> --password <password> `

  List extensions that are uploaded to a Cumulocity IoT instance. For example:

  ```bash
  analytics_builder list extensions --cumulocity_url https://demo.cumulocity.com/ --username tenantID/user --password pass
  ```
  
* `build metadata --output <json file>`

  Build JSON metadata only. This can be useful for reviewing what is extracted from the block and visible in the model editor. For example:

  ```bash
  analytics_builder build metadata --input samples/blocks  --output samples.json
  ```

* `configure designer`

  Configure Apama Plugin for Eclipse with the location of the block SDK.  See [Using Apama Plugin for Eclipse](007-UsingDesigner.md).

* `json extract --output <path to directory>` or `json pack --output <path to directory>`

  Extract or pack message or metadata JSON files from/to event files. This allows the metadata or the messages to be edited as JSON.

See the `analytics_builder --help` output for full details of the options.

## Common options

For `build extension` and `upload extension`:

* The `--username` argument can also take the tenant identifier along with user name in the format `tenantID/username`.  The user must have the 'Inventory - CREATE' permission to upload an extension.
* Specify `--restart` to request a restart of the Apama-ctrl microservice.  The user must have the 'CEP management - ADMIN' permission to request a restart.
* Specify `--delete` and `--name <base name of extension>` to delete a previously uploaded extension.
* Specify `--ignoreVersion` to not check whether the script and Apama-ctrl microservice are of the same version.


**Note:** If you wish to use the samples provided in the **samples** directory as the starting point for your own blocks, it is strongly recommended that you:

* Make a copy of the contents of the **samples** directory.
* Change the package name (and if appropriate, the block names) of the blocks.

This avoids any confusion as to the functionality and ownership of the blocks. The samples are not productized blocks, and are subject to removal or changes in future releases without notice.

## Invalid or corrupt extensions

If the uploaded extension is invalid, corrupt, or duplicate, it is not injected into the correlator and warning or error messages are logged in the microservice logs. Here is a list of the warning or error messages that are generated and how to resolve the problem:

* `Refusing to overwrite "<path>" as it is a core component`

  If the extension tries to overwrite a file that belongs to the core component, a warning message is generated and the file is ignored. You should either delete or rename the file.

* `Not copying extensions in safe mode. Extensions present but not loaded: <list of extensions>`

  If there is an error while applying extensions, the Apama-ctrl microservice restarts in safe mode and extensions are not loaded. In such a scenario either the invalid or corrupt extension should be replaced or deleted and then the microservice should be restarted.

* `Only files with extension .txt are supported for arguments, skipping: <path>`

  Arguments should be provided in a file with a `.txt` extension. Otherwise, the file is ignored.

* `Cannot handle file of unknown type: <file name>`

  If the extension file is not a zip file, is corrupted, or the path to the extension directory is not valid, the above error is logged. You should either replace or delete the file.

* `Duplicate extensions identified, starting the microservice without all extensions: <list of extensions>. Multiple extensions with the same name have been found: <list of duplicate extensions>`

  If multiple extensions with the same name are specified, an alarm is raised, an error is logged, and none of the extensions are loaded. Delete or rename the listed duplicate extensions.

* `Caught exception while creating extensions directory <extension dir> and reverted back to using the default '/config/extensions' folder`

  If an error occurs while creating the specified extension directory, the default location is used. Specify a valid path or investigate why the folder could not be created. 

* `Multiple managed objects found with pas_extension=<extension name>. Delete them and upload a new extension with the same name.`

  When uploading an extension to the Cumulocity IoT inventory, if an extension with the same name already exists, its contents are replaced. If more than one extension with the same name is found in the inventory, the above error is raised. Delete the extensions and then upload a new extension with the same name.

[< Prev: Naming and documenting blocks](020-NamingAndDoc.md) | [Contents](000-contents.md) | [Next: Testing blocks >](035-Testing.md) 
