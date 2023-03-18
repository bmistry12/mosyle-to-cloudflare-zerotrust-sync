Mosyle Cloudflare Sync
=============

Automatically syncs serial numbers for managed devices that are enrolled in Mosyle MDM to a serial number list in Cloudflare Zero Trust.

This includes adding any new devices and removing unregistered devices.

It can also support uploading a report containing details of devices registered in Mosyle to a specified S3 bucket. The format for each device will be as follows:

```
{'serialNumber': xxx, 'deviceName': xxx, 'deviceModel': xxx, 'osVersion': xxx, 'userID': xxx, 'username': xxx, 'userType': 'xxx'}
```

Issues:
- CF API seems to only allow fetching of the first 50 serial numbers in a list (a.k.a pagination doesn't work for that endpoint). The job has functionality to skip serials that already exist, but will not be able to remove serial numbers that exist past this initial 50.
- As we can only fetch 50 from CF any serial numbers that Mosyle has above that 50 that aren't in that initial 50 will be attempted to be re-added, hence the requirement for skipping serial numbers in the job.
