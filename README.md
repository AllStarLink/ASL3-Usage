# ASL3 Usage Server
Server collector of anonymous AllStarLink usage data.

## Data Collected
The following data is anonymously collected from the `asl-telemetry`
process on AllStarLink v3+ servers. The `asl-telemetry` package
will only gather and send data about ASL servers that are configured
to register with allstarlink.org. Private nodes and such are ignored.

* A UUID Version 4 random unique ID
* Asterisk and app\_rpt version information
* List of nodes on the server
* Registration type of each node (HTTP or IAX2)
* Channel type of each node
* Asterisk uptime and reload time
* OS Platform information
* Architecture type
* List of installed packages related to ASL3 (allmon3, asl3\*, dahdi\*)

And example of the data collected via `asl-telemetry -d`

```bash
RANDOM_UUID = d56da682-f200-4307-a97c-e67ab393c69c
ASL_AST_VER = Asterisk 20.7.0+asl3-1.3-1.deb12
ASL_NODES = [ 460181 ]
ASL_HTTP_NODES = [ 460181 ]
ASL_IAX_NODES = [  ]
ASL_CHANS = [{ "460181" : "SimpleUSB" }]
ASL_UPTIME = 1:8:22
ASL_RELOAD_TIME= 1:8:22
OS_OS = Linux
OS_DISTRO = Debian
OS_RELEASE = 12
OS_KERNEL = 6.6.31+rpt-rpi-v8
OS_ARCH = aarch64
PKGS = [{ "allmon3" : "1.2.1-2" , "asl-apt-repos" : "1.4-1.deb12" , "asl3" : "3.0.0-3.deb" , "asl3-asterisk" : "2:20.7.0+asl3-1.3-1.deb12" , "asl3-asterisk-config" : "2:20.7.0+asl3-1.3-1.deb12" , "asl3-asterisk-config-custom" : "" , "asl3-asterisk-dev" : "" , "asl3-asterisk-doc" : "2:20.7.0+asl3-1.3-1.deb12" , "asl3-asterisk-modules" : "2:20.7.0+asl3-1.3-1.deb12" , "asl3-menu" : "1.3-1.deb12" , "asl3-pi-appliance" : "1.5-1.deb12" , "asl3-update-nodelist" : "1.2-4.deb12" , "dahdi" : "1:3.1.0-2" , "dahdi-dkms" : "1:3.3.0-5+asl" , "dahdi-linux" : "1:3.3.0-5+asl" , "dahdi-source" : ""  }]
```

## Server Architecutre
This server process loads data into a MySQL database for
further processing and reporting. See https://repo.allstarlink.org/usage/reports/

## Updating the daily_event

How to update the daily_event should modification be needed.

The daily_usage event is included in the full schema but having it separate eases workflow and insures history is not lost when/if the event is updated.

To update the daily_usage event edit this file and do `mariadb aslusage < add_daily_event.sql

Be sure to update the full schema with `mysqldump --no-data alsusage >  aslusage.sql` if any changes are made to the daily_usage event.
