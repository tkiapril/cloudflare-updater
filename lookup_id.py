import sys
from pathlib import Path
from re import search, MULTILINE

import requests
from yaml import load, dump, BaseLoader


def api(endpoint):
    return 'https://api.cloudflare.com/client/v4{}'.format(endpoint)


def main():
    try:
        with (
            Path(__file__).resolve().parent / 'config.yaml'
        ).open('r') as r:
            update_list = load(r, Loader=BaseLoader)
    except Exception:
        print('Could not load config file. Make sure you have permission to read the file.')
        sys.exit(1)

    with Path('/proc/net/route').open('r') as r:
        s = search(r"^(.+?)\s00000000", r.read(), MULTILINE)
        default_iface = s.group(1) if s else ''

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
                'Authorization': 'Bearer {}'.format(user['token']),
                'DNT': '1',
            }
        )
        sessions.append(session)

    for zone_name in zone_names:
        find_type = None
        if ':' in zone_name:
            find_type = zone_name[zone_name.find(':')+1:].upper()
            zone_name = zone_name[:zone_name.find(':')]
            if find_type == '':
                print('Record type should be written after the colon.')
                continue
        for session in sessions:
            print('\nToken {}... :\n\n'.format(session.headers['Authorization'][7:15]))
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
                        '  {yaml}\n'.format(
                            type=item['type'],
                            name=item['name'],
                            content=item['content'],
                            yaml=dump(
                                [
                                    {
                                        'zone_id': item['zone_id'],
                                        'id': item['id'],
                                        'interface': default_iface
                                    }
                                ]
                            ).strip().replace('\n','\n  ')
                        )
                    )

if __name__ == '__main__':
    main()
