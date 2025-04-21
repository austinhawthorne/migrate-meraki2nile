#!/usr/bin/env python3
import argparse
import csv
import sys
import requests


def get_all_clients(api_key, network_id, timespan=86400, per_page=1000):
    """
    Retrieve all clients in a network, handling pagination.
    Only returns clients seen within the given timespan (seconds).
    """
    base_url = 'https://api.meraki.com/api/v1'
    url = f"{base_url}/networks/{network_id}/clients"
    headers = {
        'X-Cisco-Meraki-API-Key': api_key,
        'Content-Type': 'application/json'
    }
    params = {
        'timespan': timespan,
        'perPage': per_page
    }

    clients = []
    while True:
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        clients.extend(batch)

        if len(batch) < per_page:
            break

        # use last MAC as pagination token
        last_mac = batch[-1]['mac']
        params['startingAfter'] = last_mac

    return clients


def prompt_for_segments(vlan_set):
    """
    Prompt the user to map each VLAN ID to a segment name.
    """
    print("Discovered VLANs:")
    mapping = {}
    for vlan in sorted(vlan_set):
        name = input(f"  VLAN {vlan}: Enter segment name: ")
        mapping[vlan] = name.strip()
    return mapping


def write_migration_csv(clients, vlan_to_segment, output_file):
    """
    Write the migration CSV with headers:
    'MAC Address (Required)', 'Segment (Required for allow state)',
    'Lock to Port (Optional)', 'Site (Optional)', 'Building (Optional)', 'Floor (Optional)',
    'Allow or Deny (Required)', 'Description (Optional)',
    'Static IP (Optional)', 'IP Address (Optional)', 'Passive IP (Optional)'
    """
    seen = set()
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'MAC Address (Required)',
            'Segment (Required for allow state)',
            'Lock to Port (Optional)',
            'Site (Optional)',
            'Building (Optional)',
            'Floor (Optional)',
            'Allow or Deny (Required)',
            'Description (Optional)',
            'Static IP (Optional)',
            'IP Address (Optional)',
            'Passive IP (Optional)'
        ])

        for c in clients:
            switchport = c.get('switchport')
            if not switchport:
                continue

            mac = c['mac']
            vlan = c.get('vlan')
            key = (mac, vlan)
            if key in seen:
                continue
            seen.add(key)

            segment = vlan_to_segment.get(vlan, '')
            writer.writerow([
                mac,
                segment,
                '',       # Lock to Port
                '',       # Site
                '',       # Building
                '',       # Floor
                'Allow',
                'Imported from migration CSV',
                'No',     # Static IP
                '',       # IP Address
                'No'      # Passive IP
            ])


def main():
    parser = argparse.ArgumentParser(
        description='Export wired clients and prepare migration CSV for Meraki network segments'
    )
    parser.add_argument('--api-key',    required=True, help='Meraki Dashboard API key')
    parser.add_argument('--org-id',     required=True, help='Meraki organization ID')
    parser.add_argument('--network-id', required=True, help='Meraki network ID')
    parser.add_argument('--output',     default='migration_clients.csv',
                        help='Output CSV file (default: migration_clients.csv)')
    parser.add_argument('--timespan',   type=int, default=86400,
                        help='History window in seconds (default: 86400)')
    args = parser.parse_args()

    # Verify network belongs to organization
    org_url = f"https://api.meraki.com/api/v1/organizations/{args.org_id}/networks"
    headers = {'X-Cisco-Meraki-API-Key': args.api_key}
    resp = requests.get(org_url, headers=headers)
    resp.raise_for_status()
    networks = {n['id'] for n in resp.json()}
    if args.network_id not in networks:
        sys.exit(f"Error: Network {args.network_id} not found in organization {args.org_id}")

    print("Fetching all clients...")
    all_clients = get_all_clients(
        api_key=args.api_key,
        network_id=args.network_id,
        timespan=args.timespan
    )

    print(f"Total clients retrieved: {len(all_clients)}")
    # Filter wired clients
    wired_clients = [c for c in all_clients if c.get('switchport')]
    unique_vlans = set(c.get('vlan') for c in wired_clients if c.get('vlan') is not None)

    # Prompt user for segment names
    vlan_to_segment = prompt_for_segments(unique_vlans)

    print("Writing migration CSV...")
    write_migration_csv(wired_clients, vlan_to_segment, args.output)
    print(f"Done — migration CSV exported to {args.output}")

if __name__ == '__main__':
    main()

