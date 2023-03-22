#  Sharing data across partitions and workers

## Worker state

Analytics Builder models use either a group of devices, or one or more specific devices. When a model uses one or more specific devices, the model is evaluated in the context of a single shared partition. A block consuming values from multiple such devices will have a single shared state. When a model uses a group of devices, the model is evaluated in the context of partitions corresponding to each device within the group. A block consuming values for such devices will have a separate block state per device, for example, the Average (Mean) block generates means independently for each device within the group. See [Partition values](070-Partitions.md) for more details.

There can be use cases where we may want to share state among all devices within a group, for example, to generate the mean of all devices rather than calculate the mean of each device. In such scenarios, a special type of state object, `WorkerState` should be used to share state between devices in a group. 

If the Analytics Builder runtime is configured to use more than one worker thread, then blocks will have one `WorkerState` object per worker thread and blocks will have to combine them to compute the value across all devices within the group.

Note: It is assumed that the computed value does not have to be time-synchronous with respect to the input, and that the computed value uses the input value from all devices up to the approximate time T, not the exact time T.

To share the state of the block across partitions in a worker, use a separate event type, named `<block>_$WorkerState`. This can be supplied as a `$workerState` parameter to the framework methods of the block. It can contain whatever values the block requires to execute.

The fields of the `WorkerState` object have the same restrictions as those of the normal state object; refer to [050-State.md](050-State.md) for more details.

If the Analytics Builder runtime is configured to use only one worker thread, then the `WorkerState` object can hold state from all devices within the group and can compute values accordingly.

Note: A block should use the `$WorkerState` parameter only in a model which is processing events from multiple devices in a group.

## Sharing data across workers 

When the Analytics Builder runtime is configured to use multiple workers threads then devices will be distributed across workers and one `WorkerState` object will have data on a subset of devices. 

So we need to share data across workers. Sharing data between workers is an expensive operation and it is very difficult to have time synchronous outputs combined from each device so it should only be done periodically.
 
To send data from one worker to others periodically, use an un-partitioned (without any partition value) [recurring timer](060-Timers.md). When this timer is triggered, send the data computed on the current worker to all other workers. Instances of the block on other workers save this latest data so that they can generate output later.

Note: No extra steps are needed if the Analytics Builder runtime is configured with one worker.

## Generating periodic output to all partitions

To combine data from all workers and to generate outputs for each partition, create a [recurring timer](060-Timers.md) with `Partition_Broadcast` as the [partition](070-Partitions.md) type, so that it is triggered for all partitions (all devices in a group). When this timer is triggered, combine the data received from all the workers to generate the final value.


The following code snippet shows how to use `$WorkerState` to share `Data` across partitions on multiple workers:
```java
/**Actual data values. */
event Data {
}

/** Sharing data of a worker to other workers. */
event WorkerData {
	/** The worker ID. */
	integer workerId;
	/** The block ID. */
	string blockId;
	/** The model ID. */
	string modelId;
	/** Combined data for all devices on the worker specified by the worker ID. */
	Data data;	
}

/** Shared state of the block in a worker. The block instance running on other workers will have a different shared state. */
event Block_$WorkerState {
	/** Latest snapshot of data received from all workers.*/ 
	dictionary<integer, Data> workerSnapshot;
}
event Block {
    BlockBase $base;
    /** Constant to identify a recurring timer for calculating aggregate values for the current worker and sending them to other workers for generating final aggregate values. */
    constant integer TIMERTYPE_SHAREDATA_RECUR := 1;
    
    /** Constant to identify a recurring timer for generating final aggregate values by combining values from all workers. */
    constant integer TIMERTYPE_GENOUTPUT := 2;
    
    
    action $init(Block_$WorkerState $workerState) {
         
        // The amount of time (in seconds) between each output. This value can be taken from one of the block parameters.
        float period := 5.0; 
        // Combine values from all the partitions on the worker and send the values to all workers.
        TimerHandle shareDataHandle := $base.createTimerWith(TimerParams.recurring(period).withPayload(TIMERTYPE_SHAREDATA_RECUR));
    
        // Listen for data from all workers but only for the correct block in the correct model by filtering on the blockId and modelId.
        on all WorkerData(blockId=$base.getBlockId(), modelId=$base.getModelId()) as workerData {
            $workerState.workerSnapshot[workerData.workerId] := workerData.data;
        }
    
        // Create a timer for combining data from all workers to generate final values. Pass the TIMERTYPE_GENOUTPUT as the payload so that we 
        // can identify the type of the triggered timer. Use Partition_Broadcast as the partition so that the timer is triggered for each device and output generated.
        TimerHandle genOutputHandle := $base.createTimerWith(TimerParams.recurring(period).withPayload(TIMERTYPE_GENOUTPUT).withPartition(new Partition_Broadcast));
    }
    
    action $timerTriggered(Activation $activation, Block_$WorkerState $workerState, any $payload) {
    
        // Find the type of the timer from the payload.
        integer timerType := <integer>$payload;
        
        // Calculate data for this worker and share with other workers.
        if timerType = TIMERTYPE_SHAREDATA_RECUR {
            shareData($workerState);
        }
    
        // Calculate final values by combining values from all workers and generate outputs for each device.
        if timerType = TIMERTYPE_GENOUTPUT { 
            generateOutput($activation, $workerState);
        }
    }
    
    action shareData(Block_$WorkerState $workerState) {
        /*
            Your code to compute data for the current worker.
        */
    
        // Share the computed data with all workers.
        // send WorkerData($base.getWorkerId(), $base.getBlockId(), $base.getModelId(), calculatedData) to Partitioner.ALL_WORKERS;
    }
    
    action generateOutput(Activation $activation, Block_$WorkerState $workerState) {
        /*
         Your code to calculate the final values by combining values received from all workers and generate outputs for each device.
        */
    }
}
```

See the **GroupStatistics.mon** sample for a complete example on sharing data across partitions and workers.

[< Prev: Migrating input and output blocks to the version 2 API](150-MigrateInputOutputBlocks.md) | [Contents](000-contents.md)
