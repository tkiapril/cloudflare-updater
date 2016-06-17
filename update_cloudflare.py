import pathlib
import socket
from pprint import pprint

import requests
from yaml import load


def api(endpoint):
    return 'https://api.cloudflare.com/client/v4{}'.format(endpoint)


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 53))
    myip = s.getsockname()[0]
    s.close()

    with (
        pathlib.Path(__file__).resolve().parent / 'config.yaml'
    ).open('r') as r:
        update_list = load(r)

    for user in update_list:
        session = requests.Session()
        session.headers.update(
            {
                'X-Auth-Email': user['email'],
                'X-Auth-Key': user['token'],
                'DNT': 1,
            }
        )
        for target in user['targets']:
            endpoint = api(
                '/zones/{zone_id}/dns_records/{id}'.format(
                    zone_id=target['zone_id'],
                    id=target['id']
                )
            )
            record = session.get(endpoint).json()['result']
            if record['type'] != 'A':
                print(
                    'zone_id {}, id {} ({} {}) is not an A record; '
                    'not doing anything.'.format(
                        record['zone_id'],
                        record['id'],
                        record['type'],
                        record['name']
                    )
                )
                continue
            result = session.put(
                endpoint,
                json={
                    'type': 'A',
                    'name': record['name'],
                    'content': myip
                }
            ).json()
            if result['success']:
                record = result['result']
                print(
                    'Successfully updated {} to {}'.format(
                        record['name'], myip
                    )
                )
            else:
                print(
                    'An error occurred while updating {}: '
                    'Please see below for details.\n'.format(record['name'])
                )
                pprint(result)

if __name__ == '__main__':
    main()
