import pathlib
import socket

import pyflare
import yaml


s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('8.8.8.8', 53))
myip = s.getsockname()[0]
s.close()

with (pathlib.Path(__file__).resolve().parent / 'config.yaml').open('r') as r:
    update_list = yaml.load(r)

for account in update_list:
    records = {}
    p = pyflare.PyflareClient(account['email'], account['token'])
    for target in account['targets']: 
        if target['subdomain'].count('.') < 2:
            zone = target['subdomain']
        else:
            zone = target['subdomain'][target['subdomain'].rfind('.', 0, target['subdomain'].rfind('.'))+1:]
        if zone not in records:
            records[zone] = list(p.rec_load_all(zone))
        for record in records[zone]:
            if record['rec_id'] == target['id']:
                target_record = record
                break
        p.rec_edit(zone, 'A', target['id'], target_record['name'], myip, 1, 0)
        print('Successfully updated {} to {}'.format(target['subdomain'], myip))
