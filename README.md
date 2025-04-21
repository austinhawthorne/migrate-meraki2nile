# migrate-meraki2nile
Script to migrate Meraki Device to VLAN mappings to a Nile Segment Authorization

Will poll the Meraki Dashboard API for all wired clients, along with VLAN settings, and convert into a customized CSV for import into Nile.  You will need the following:

- API Key
- orgID
- networkID

Once you have that, run the script.  It will prompt you to enter a Nile segment name to use for the discovered VLANs and then create the CSV.  Once you have this, import the CSV into Nile to pre-approve all devices to be migrated.

Sample:

root@netserv:/home/foo# python get-meraki-clients.py --api-key REDACTED --org-id REDACTED --network-id REDACTED \
Fetching all clients... \
Total clients retrieved: 5 \
Discovered VLANs: \
  VLAN 1000: Enter segment name: Internet-Only \
  VLAN 40: Enter segment name: Acme-Devices \
Writing migration CSV... \
Done — migration CSV exported to migration_clients.csv 


