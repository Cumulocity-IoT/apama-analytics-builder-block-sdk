# Asynchronous validations

Typically, a block will perform validation synchronously. By the time the action call to `$validate` is complete, the action has either thrown an exception due to an error or the action has checked that the block is in a valid state. There are cases, however, where an external lookup needs to be completed, typically by sending a request to another monitor or component external to the correlator which will later send a response. EPL does not permit an action call to block until this is complete, as this is (potentially) external to the correlator, and would block processing of other events while waiting for a response. To permit this pattern, the `$validate` call may be declared to return a `Promise` value. A `Promise` is a type that indicates future completion (or failure). If the `$validate` call returns a `Promise` object, validating the model will be suspended until the `Promise` is fulfilled, and the framework will not start executing the model until all validation steps have been completed. While `Promise` may yield a return value, for `$validate`, the value on completion should always be an empty `any` value.

A `Promise` should be completed within a reasonable amount of time. By default, the framework will wait for 60 seconds for the `Promise` to complete. If the `Promise` is not completed within the timeout duration, then the model deployment fails. The timeout duration can be changed via a tenant option. The framework also logs a warning if a `Promise` takes more than 10 seconds to complete. Refer to the Apama Analytics Builder documentation for more details.

A `Promise` is typically created with the `Promise.create` method. This takes an action which has two callback actions as parameters - for success and failure. Alternatively, `Promise.resolve` will return a `Promise` which is already resolved (unless the value passed to `resolve` is itself a `Promise` which is not fulfilled). A simplified example:

```Java
action $validate() returns Promise {
    if (needsLookup()) {
        return Promise.create(lookup);
    } else {
        return Promise.resolve(new any); // empty any 'return' value
    }
}

action lookup(action<any> success, action<Exception> failure) {
    integer id := integer.getUnique();
    send LookupRequest(id) to LookupRequest.CHANNEL;
    on LookupResponseSuccess(id=id) as response and not LookupFailed(id=id) within(timeout) {
        if not validResponse(response) {
            failure(L10N.getLocalizedException_basic("InvalidResponse"));
        } else {
            success(new any);
        }
    }
    on (LookupFailed(id=id) or wait(timeout)) and not LookupResponseSuccess(id=id) {
        failure(L10N.getLocalizedException_basic("TimeoutOrFailure"));
    }
}
```

As with simple `$validate` actions, an exception thrown from the `$validate` (or the `lookup`), as well as calling the `failure` callback, will be treated as a validation failure.

## Chaining promises

If an action API that returns a `Promise` is used to perform the lookup, then handling of the response to validate it can be easily achieved by using the `Promise.andThen` action to chain post-processing. For example:

```Java
action $validate() returns Promise {
    return helper.lookup($parameters.object).andThen(validateLookup);
}

action validateLookup(any arg) returns any {
    if not validResponse(<Response> arg) {
        throw L10N.getLocalizedException_basic("InvalidResponse");
    }
    return new any; // valid : return successful (and an empty any, as required from the $validate).
}
```

For examples, see the **DeviceLocationInput.mon** sample.

[< Prev: Cumulocity-specific helpers](105-CumulocityHelper.md) | [Contents](000-contents.md) | [Next: Migrating input and output blocks to the version 2 API >](150-MigrateInputOutputBlocks.md) 
