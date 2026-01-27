# Change Log

## 27.23.0
* Add @$isPreviewBlock annotation, which will suppress visibility of a block unless preview blocks are enabled by the user.

## 26.260.0
* `CumulocityInputHandler.createListeners` has been enhanced to dynamically detect changes in the group hierarchy. This includes detecting the addition, deletion, or update of devices and assets, as well as structural changes within groups. This enhancement ensures consistent behavior, simplifies maintenance, prevents listener leaks, and aligns with updated best practices. See [Monitoring Device Hierarchy with CumulocityInputHandler](doc/153-MigrateInputBlocksToMonitorDeviceHierarchy.md) for more details.

## 26.95.0
* The Analytics Builder Block SDK is no longer supported natively on Windows environments. For Windows users, we recommend switching to a WSL-based (Windows Subsystem for Linux) environment using Debian. You may wish to use the [Apama Extension for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=ApamaCommunity.apama-extensions) for block development. 

## 25.298.0
* HTTPOutput Sample block works correctly in partitioned model.

## 25.90.0
* The Analytics Builder Block SDK is now processing the input events with timestamp 0.0.

## 24.0.0
* The Analytics Builder Block SDK is now moving to a continuous delivery (CD) model.

## 10.18.1.0
* .git and .github subdirectories are now skipped when building extensions. See [Building a block into an extension](doc/030-BuildingExtensions.md) for more details.

## 10.18.0.0
* Cumulocity input blocks can now receive from assets (and from their child devices). Existing input blocks may need to be updated to enable receiving from assets. See [Update Cumulocity input blocks to receive from assets](doc/151-MigrateInputBlocksForAssetInput.md) for more details.

## 10.17.0.0
* The version 1 API for writing input and output blocks has been removed. Existing blocks that use the version 1 API must be migrated to use the version 2 API. See [Migrating input and output blocks to the version 2 API](doc/150-MigrateInputOutputBlocks.md) for more details.

## 10.14.0.3
* The SDK documentation now lists the categories that you can use when writing your own blocks. See [Allowed categories](doc/020-NamingAndDoc.md#allowed-categories) for more details.

## 10.11.0.0
* You can now build an extension by skipping uninteresting folders from the build. See [Building a block into an extension](doc/030-BuildingExtensions.md) for more details.
* It is now possible to list the extensions that are uploaded to a Cumulocity instance. See [Building a block into an extension](doc/030-BuildingExtensions.md) for more details.

## 10.7.0.0
* The version 2 API for writing input and output blocks is available.
* The version 1 API for writing input and output blocks is deprecated. Existing blocks will need to be migrated. See [Migrating input and output blocks to the version 2 API](doc/150-MigrateInputOutputBlocks.md) for more details.




