import pathlib
import socket
import sys

import pyflare
import yaml


try:
    with (
        pathlib.Path(__file__).resolve().parent / 'config.yaml'
    ).open('r') as r:
        update_list = yaml.load(r)
except Exception:
    print('Could not load config file.')
    sys.exit(1)

domains = sys.argv[1:]

if len(domains) == 0:
    print('''
Please provide domain names to lookup as arguments. You can specify which
record type to find by writing one after colon after domain name:
for example, example.com:cname.
    '''.strip())
flare = []

for account in update_list:
    try:
        flare.append(pyflare.PyflareClient(account['email'], account['token']))
    except Exception:
        print('Login failed for account: {}'.format(account['email']))

for domain in domains:
    find_type = None
    if ':' in domain:
        find_type = domain[domain.find(':')+1:].upper()
        domain = domain[:domain.find(':')]
        if find_type == '':
            print('Record type should be written after the colon.')
    if find_type is None or find_type != '':
        for p in flare:
            records = p.rec_load_all(domain)
            if find_type is not None:
                records = [item for item in records if item['type'] == find_type]
            for item in records:
                print(
                        '{rec_id}:\t{type}\t{name}\t-> {content}'.format(
                        rec_id=item['rec_id'],
                        type=item['type'],
                        name=item['name'],
                        content=item['content']
                    )
            )
