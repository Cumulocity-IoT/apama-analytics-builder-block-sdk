# Update Cumulocity IoT input blocks to receive from assets

In version 10.18, support was added for receiving inputs from an asset (and not from its child devices). Existing Cumulocity IoT input blocks may need to be updated to enable receiving from assets.

Change the type of the parameter which holds the selected device identifier to `any`. For example, consider following block parameter `source` that holds the selected device, asset or group of devices.

```Java
event AlarmInput_$Parameters {
    /**
     * Input Source.
     *
     * Defines the source from which the alarm has been received.
     *
     * This can be a single device, an asset, an object that references or contains a group of devices, or all input sources.
     *
     * @$semanticType c8y_deviceOrGroupId
     */
    string deviceId;
    
    ...
}

event AlarmInput {
    
    ...

    action $validate() returns Promise {
        CumulocityInputParams params := CumulocityInputParams
                                        .create($parameters.deviceId, self, Alarm.getName())
                                        .withFields({"type":<any>$parameters.alarmType});
        return params.declare(inputHandlerCreated);
    }

    ...
}
```

Update the type of the parameter to be `any`. Remove any validation for the type of the parameter value as the validation of the parameter will be done by the `CumulocityInputParams` object. If the parameter is mandatory, then a check can be added to validate that the parameter is not empty.

```Java
event AlarmInput_$Parameters {
    /**
     * Input Source.
     *
     * Defines the source from which the alarm has been received.
     *
     * This can be a single device, an asset, an object that references or contains a group of devices, or all input sources.
     *
     * @$semanticType c8y_deviceOrGroupId
     */
    any deviceId;

    ...

    action $validate() {
        /** Check that deviceId parameter has non-empty values. */
        BlockBase.throwsOnEmpty(deviceId, "deviceId", self);
    }
}
event AlarmInput {
    
    ...

    action $validate() returns Promise {
        CumulocityInputParams params := CumulocityInputParams
                                        .create($parameters.deviceId, self, Alarm.getName())
                                        .withFields({"type":<any>$parameters.alarmType});
        return params.declare(inputHandlerCreated);
    }

    ...
}
```

[< Prev: Migrating input and output blocks to the version 2 API](150-MigrateInputOutputBlocks.md) | [Contents](000-contents.md) | [Next: Update Cumulocity IoT input blocks to receive from all input sources >](152-MigrateInputBlocksForAllInputs.md) 
