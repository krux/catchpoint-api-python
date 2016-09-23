# Catchpoint API Python Module

## Description
Catchpoint has two types of APIs, a push (subscriber) API and a pull REST API. This module is a wrapper for the [Pull API](https://support.catchpoint.com/hc/en-us/articles/208029743).

[API documentation](https://io.catchpoint.com/ui/Help) is available to Catchpoint customers.

## Requirements

Tested on Python 2.7.5

Modules: 
* pytz
* requests

## Installation

`python setup.py install`

## Usage

```python
# import the module
import catchpoint

# create a Catchpoint object
cp = catchpoint.Catchpoint(
    client_id='CLIENT_KEY_FROM_CATCHPOINT',
    client_secret='CLIENT_SECRET_FROM_CATCHPOINT',
)

# query the API
print cp.favorite_charts()
print cp.favorite_details(myfav)
```
Also, refer to [cli.py](cli.py).

### Methods

| Method  |  Description  | Parameters |
| :------ | :------------ | :--------- |
| raw     | Retrieve the raw performance chart data for a given test for a time period. | testid, startTime, endTime, tz="UTC" |
| favorite_charts | Retrieve the list of favorite charts. | |
| favorite_details | Retrieve the favorite chart details. | favid |
| favorite_data | Retrieve the data for a favorite chart, optionally overriding its timeframe or test set. | favid, startTime=None, endTime=None, tz="UTC", tests=None |
| nodes | Retrieve the list of nodes for the API consumer. | |
| node | Retrieve a given node for the API consumer. | node |

### Parameters

| Param | Type | Description |
| :---- | :--- | :---------- |
| testid | str | The Catchpoint test ID |
| favid | str | The Catchpoint favorite ID |
| startTime | str or int | Specifically formatted ("%m-%d-%Y %H:%M") time to begin requested dataset. Can be expressed as a negative integer when `endTime` = 'now'. |
| endTime | str | Specifically formatted ("%m-%d-%Y %H:%M") time to end requested dataset. Can be expressed as 'now' to use current time. |
| tz | str | Optionally set the timezone to correlate to the Catchpoint test's configuration. |
| tests | str | Specify a comma-separated list of tests when retreiving a favorite chart.
| node | str | The Catchpoint node id. |

#### Relative Time Requests
Catchpoint's API requires specifically formatted timestamps when requesting datasets. These can be made relative by setting `startTime` to a negative integer that represents number of minutes into the past, and set `endTime` to 'now'.

Example for retreiving the last 60 minutes of data:

```python
cp = catchpoint.Catchpoint()
myfav = "12345"
startTime = -60
endTime = "now"
print cp.favorite_data(myfav, startTime, endTime)
```
## License

GPL v2
