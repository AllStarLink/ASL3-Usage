# README.md

Create the backend of a system to measure ASL3 usage and selected parameters for the propose of understanding the adoption and relibality of ASL3.

## Requirements
- Nodes must be registered with register.allstarlink.org in order to participate.
- No personal or sensitive data shall be collected.
- Asterisk modules including app_rpt shall not be part of this system.
- System shall report only to AllStarLink inc.
- System shall consist of an ID and password protected web site for reporting, a proper API for collection from client, and data storage.
- System will likely reside on repo.allstarlink.org.

## Data elements
- Version number of ASL3 Debian packages.
- Per node registration via IAX and http with server generated datetimestamps.
- Asterisk up and reload times.
- Channel driver in use per node.
- Server generated datetimestamp of API post.  

## Reports
Collected data will be user ID and password protected and available only to AllStarLink personnel for the propose of understanding ASL3 adoption and reliabilty.
