from fcntl import ioctl
from socket import AF_INET, SOCK_DGRAM, inet_ntoa, socket
from struct import pack
from pathlib import Path
from pprint import pprint

from requests import Session
from requests.adapters import DEFAULT_POOLSIZE
from yaml import load, BaseLoader


def api(endpoint):
    return 'https://api.cloudflare.com/client/v4{}'.format(endpoint)


def main():
    interface_ips = {}
    
    with (
        Path(__file__).resolve().parent / 'config.yaml'
    ).open('r') as r:
        update_list = load(r, Loader=BaseLoader)

    for user in update_list:
        session = Session()
        session.headers.update(
            {
                'Authorization': 'Bearer {}'.format(user['token']),
                'DNT': '1',
            }
        )
        for target in user['targets']:
            internal = 'internal' not in target.keys() or bool(int(target['internal']))
            target_interface = target['interface'] if internal else target['interface'] + '_internal'
            if (target_interface not in interface_ips.keys()):
                s = socket(AF_INET, SOCK_DGRAM)
                internal_ip = inet_ntoa(
                    ioctl(
                        s.fileno(),
                        0x8915,  # SIOCGIFADDR
                        pack('256s', bytes(target['interface'][:15], 'utf-8')),
                    )[20:24]
                )
                if internal:
                    interface_ips[target_interface] = internal_ip
                else:
                    bound_sess = Session()
                    bound_sess.get_adapter('https://').init_poolmanager(
                        connections=DEFAULT_POOLSIZE,
                        maxsize=DEFAULT_POOLSIZE,
                        source_address=(internal_ip, 0),
                    )
                    interface_ips[target_interface] = bound_sess.get('https://api.ipify.org/').text
            myip = interface_ips[target_interface]
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
