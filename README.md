Mosyle MDM - Cloudflare Zero Trust Sync
=======================================

Automatically syncs serial numbers for managed devices enrolled in Mosyle MDM to a serial number list in Cloudflare Zero Trust.

## Overview
The Mosyle MDM - Cloudflare Zero Trust Sync is a tool that enables synchronisation of device serial numbers between Mosyle MDM and a Cloudflare Zero Trust device list.  The tool handles the addition of new devices and removal of unregistered device.

**Who is this useful for?**</br>
Anyone that manage devices using Mosyle MDM and rely on serial number lists in Cloudflare Zero Trust for managing VPN access or split tunnels, or implementing HTTP + DNS rules etc.

**Why is that useful?**</br>
Well, the short version...it saves manual effort, maintains an up-to-date Cloudflare serial number list, ensures proper device setup, and streamlines device management for enhanced security and convenience.

The longer version...
- Automation </br>
  Eiminates the need for manual insertion / removal of device information into Cloudflare. When a new device is purchased and enrolled in Mosyle MDM, it automatically detects and adds it to the serial number list in Cloudflare Zero Trust. This automation saves time and effort, ensuring that Cloudflare is always up to date.
- Synchronisation: </br>
  By keeping the Cloudflare synced with Mosyle we are certain every device has the necessary setup and configurations before being logged into for the first time. This guarantees a smooth user experience and reduces the risk of inconsistencies or access issues.
- Centralised Management:  </br>
  With Mosyle MDM and Cloudflare Zero Trust integration, device management becomes centralised - all you need to do is purchase the device and ensure it is enrolled in one place. If anything, it makes your job easier.
- Built in Reporting: </br>
  People love asking questions about device posture to ensure device fleets are secure and not harbouring 10 year old OS versions. By having this data readily available in an S3 bucket, we can facilitate a more self-serviced approach to fetching data and monitoring security.

## Features
- Automatic syncing of serial numbers between Mosyle MDM and Cloudflare Zero Trust.
- Addition of new devices to the Cloudflare Zero Trust serial number list.
- Removal of unregistered devices from the Cloudflare Zero Trust serial number list.
- Optional support for uploading a detailed device report to a specified S3 bucket.

### Device Reportting
If enabled, a device report can be uploaded on each run to an S3 bucket, containing details of devices registered in Mosyle. The format for each device entry in the report is as follows

```bash
{'serialNumber': xxx, 'deviceName': xxx, 'deviceModel': xxx, 'osVersion': xxx, 'userID': xxx, 'username': xxx, 'userType': 'xxx'}
```

<hr>

## Usage

```bash
docker build -t mosyle-to-cf-ztn -f Dockerfile .
docker run -d -it mosyle-to-cf-ztn
```

### Configuration
The main configuration file is `./app/config/configuration.toml`.

```toml
[cloudflare]
api_token = '' <- cloudflare api token
account_id = '' <- the cloudflare account id
team_list = '' <- the name of the serial number list to sync to

[mosyle]
api_token = '' <- mosyle api token
email = '' <- email address of an admin user
password = '' <- password of ^ user

[s3]
reports_bucket = '' <- S3 bucket to send reports to
```

## Known Issues *(and work arounds)*:
- Cloudflare API Limitations</br>
  The CF API seems to only allow fetching of the first 50 serial numbers in a list (a.k.a pagination doesn't work for that endpoint). The job has functionality to skip serials that already exist, but will not be able to remove serial numbers that exist past this initial 50.</br>
  As we can only fetch 50 from CF any serial numbers that Mosyle has above that 50 that aren't in that initial 50 will be attempted to be re-added, hence the requirement for skipping serial numbers in the job.
- Mosyle API IAuthentication</br>
  Unfortunately, Mosyle enforces email+password for API auth, so you will need to have an API token, email, and password for an admin user.

## To-Do
- Reporting
  - Make generating a report optional
  - Make pushing to S3 optional
  - Allow pushing to elsewhere
- Allow syncing to multiple CF lists
