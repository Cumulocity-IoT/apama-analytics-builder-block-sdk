# Monitoring Device Hierarchy with `CumulocityInputHandler`

The `createListeners` API now supports dynamic detection of changes to the group hierarchy (devices, assets, and groups) post-deployment.

You should no longer manually implement per-device listeners for inputs. Using `createListeners` ensures that hierarchy updates are handled automatically, preventing listener leaks and simplifying maintenance.

```Java
/**
* Create listeners to listen for new alarms of a specific type.
*/
action $init() {
	// provide all the necessary info required to set up the listeners
	inputHandler.createListeners(Alarm.getName(), {"type" : <any>$parameters.alarmType}, handleAlarm);
}
```

[< Prev: Update Cumulocity input blocks to receive from all input sources](152-MigrateInputBlocksForAllInputs.md) | [Contents](000-contents.md) | [Next: Sharing data across partitions and workers >](160-SharingDataAcrossPartition.md) 
