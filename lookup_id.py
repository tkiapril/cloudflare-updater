import pathlib
import sys

import requests
import yaml


def api(endpoint):
    return 'https://api.cloudflare.com/client/v4{}'.format(endpoint)


def main():
    try:
        with (
            pathlib.Path(__file__).resolve().parent / 'config.yaml'
        ).open('r') as r:
            update_list = yaml.load(r)
    except Exception:
        print('Could not load config file.')
        sys.exit(1)

    zone_names = sys.argv[1:]

    if len(zone_names) == 0:
        print('''
Please provide zone names (root domain) to lookup as arguments. You can
specify which record type to find by writing one after colon after zone name:
for example, example.com:cname.
        '''.strip())
    sessions = []

    for user in update_list:
        session = requests.Session()
        session.headers.update(
            {
                'X-Auth-Email': user['email'],
                'X-Auth-Key': user['token'],
                'DNT': 1,
            }
        )
        if session.get(api('/user')).json()['success']:
            sessions.append(session)
        else:
            print('Login failed for account: {}'.format(user['email']))

    for zone_name in zone_names:
        find_type = None
        if ':' in zone_name:
            find_type = zone_name[zone_name.find(':')+1:].upper()
            zone_name = zone_name[:zone_name.find(':')]
            if find_type == '':
                print('Record type should be written after the colon.')
                continue
        for session in sessions:
            print('\n{}:\n\n'.format(session.headers['X-Auth-Email']))
            zones = session.get(api('/zones')).json()['result']
            try:
                zone_id, = [
                    zone['id'] for zone in zones if zone['name'] == zone_name
                ]
            except ValueError:
                continue
            records = session.get(
                api('/zones/{}/dns_records'.format(zone_id))
            ).json()['result']
            if find_type is not None:
                records = [
                    item for item in records if item['type'] == find_type
                ]
            for item in records:
                print(
                        '  # {type}\t{name}\t-> {content}\n'
                        '  {yaml}  # {name}\n'.format(
                            type=item['type'],
                            name=item['name'],
                            content=item['content'],
                            yaml=yaml.dump(
                                [
                                    {
                                        'zone_id': item['zone_id'],
                                        'id': item['id']
                                    }
                                ]
                            ).strip()
                        )
                    )

if __name__ == '__main__':
    main()
