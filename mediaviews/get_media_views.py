"""Get all media-views/mediarequests for files in a category for a time span.

Returns only human views.

Limitations:
* Does a Rest-API call per file (and one to the Action API).
* If the time span includes the current month the results will likely be partial.
* Assumes a file has always been a member of the category if it is a member of it today.
* The statistics only go back to 2015.
"""
import argparse
import json
import urllib.parse
import os
from collections.abc import Iterator
from datetime import date

import pywikibot
import requests
from requests.adapters import HTTPAdapter, Retry
from pywikibot.exceptions import APIError
from tqdm import tqdm

DEFAULT_OUTPUT = 'stats_output.json'
HEADERS = {
    'User-Agent': 'get_media_views.py/1.0 (https://gist.github.com/lokal-profil/4a807aaf56e6af8171df5d8cfb8950b2; {})'
}
RETRIES = Retry(total=5, backoff_factor=0.1)


def get_cat_media_views(
        cat_name: str, start: str, end: str, limit: int = None, recursion: int = 0,
        output_type: str = 'file', debug: bool = False) -> dict:
    """Command line entrypoint."""
    commons = pywikibot.Site('commons', 'commons')
    #cat_name = "100 000 Bildminnen"
    category = pywikibot.Category(commons, cat_name)
    files = get_cat_members(category, recurse=recursion, limit=limit)
    stats = {}

    # Run connection through a session to limit hammering
    s = requests.Session()
    s.mount(
        'https://wikimedia.org',
        HTTPAdapter(max_retries=RETRIES))
    s.headers.update(HEADERS)

    for file_page in files:
        freq = 'daily' if output_type == 'day' else 'monthly'
        try:
            file_stats = get_media_requests(s, file_page, start, end, frequency=freq, debug=debug)
        except APIError as error:
            if error.code == "999":
                if debug:
                    pywikibot.output(f"{error.info}")
                continue
            else:
                pywikibot.output(f"{error.info}")
                exit()
        stats[file_page.title()] = file_stats
    if not stats:
        # e.g. empty category or all entries resulting in 999 errors
        pywikibot.output('Found no stats for the category.')
        exit()
    else:
        pywikibot.output(f'Found stats for {len(stats)} files.')

    if output_type == 'file':
        return {  # filename: total_media_views
            k: sum([vv.get('requests') for vv in v.get('items')]) for k, v in stats.items()
        }
    elif output_type in ('month', 'day'):
        return per_time_stats(stats)
    else:
        return stats


def per_time_stats(stats: dict) -> dict:
    """Collate the statistics per unit of time.
    
    Data is outputted in the format 
    {
        timestamp: {
            total: total_media_views,
            items: [media_views per file]
        }
    }
    """
    time_stats = {}
    for value in stats.values():
        for unit in value.get('items'):
            datestamp = unit.get('timestamp')[:-2]
            if datestamp not in time_stats:
                time_stats[datestamp] = {'total': 0, "items": []}
            time_stats[datestamp]['total'] += unit.get('requests')
            time_stats[datestamp]['items'].append(unit.get('requests'))
    return time_stats


def get_cat_members(
        cat: pywikibot.Category, recurse: int = 0,
        limit: int = None) -> Iterator[pywikibot.FilePage]:
    """Yield category members but ensuring no duplication due to subcategory membership."""
    files = set()
    category_members = cat.members(recurse=recurse, member_type='file', total=limit)
    total = (limit or cat.categoryinfo.get('files') if not recurse else None)
    for file_page in tqdm(category_members, desc="Processing category members", total=total):
        if file_page in files:
            continue  # since same file can occur in recursive categories
        files.add(file_page)
        yield file_page


def get_media_requests(
        s: requests.Session, file: pywikibot.FilePage, start: str, end: str,
        agent: str = 'user', frequency: str = 'monthly', debug: bool = True):
    """Return media requests per month for a single file.
    
    @param start: start date in the format YYYYMMDD
    @param end: end date in the format YYYYMMDD
    @param agent: user, spider or all-agents.
        See https://wikimedia.org/api/rest_v1/#/Mediarequests%20data/ for documentation.
    """
    if debug:
        print(f"I'm looking up: {file.title()}")
    file_path = file.get_file_url().partition('.org')[2]
    url = (
        f'https://wikimedia.org/api/rest_v1/metrics/mediarequests/per-file/all-referers/'
        f'{agent}/{urllib.parse.quote(file_path, safe="")}/{frequency}/{start}/{end}')
    res = s.get(url, timeout=30)

    if debug:
        print(url)
        print(f"request_result: {res.status_code}")
    if res.status_code == 404:
        raise APIError('999', f'No page views for the provided time period. [{file.title()}]')
    if res.status_code == 400:
        raise APIError('666', f'Bad request: {res.json().get("detail")}')
    data = res.json()
    return data


def make_meta(args: argparse.Namespace) -> dict:
    """Output metadata about the run."""
    meta = {arg: getattr(args, arg) for arg in vars(args)}
    del meta['out_file']
    del meta['user']
    meta['today'] = date.today().strftime("%Y%m%d")
    return meta


def set_user_agent(user: str):
    """Set a contact point in the User-Agent"""
    HEADERS['User-Agent'] = HEADERS.get('User-Agent').format(user)
    HEADERS['From'] = user


def output_result(result: dict, out_file: str) -> None:
    """Output result to file."""
    if not os.path.exists(os.path.split(out_file)[0]+'/'):
        os.makedirs(os.path.split(out_file)[0]+'/')
    with open(out_file, 'w', encoding ='utf8') as fp:
        json.dump(result, fp, sort_keys=True, indent=2, ensure_ascii=False)
        pywikibot.output(f'Data saved to {out_file}')


def handle_args(argv: list = None) -> argparse.Namespace:
    """
    Parse and handle command line arguments.

    @param argv: arguments to parse. Defaults to sys.argv[1:].
    """

    parser = argparse.ArgumentParser(
        description=('Select a category on Commons and fetch the media-views statistics for '
                     'a given time span.'))
    parser.add_argument('-c', '--category', action='store', metavar='CAT',
                        required=True, dest='cat_name',
                        help='Commons category to process (with or without Category:-prefix)')
    # TODO: drop DD requirement?
    parser.add_argument('-s', '--start', action='store', metavar='YYYYMMDD', required=True,
                        help='start date')
    parser.add_argument('-e', '--end', action='store', metavar='YYYYMMDD',
                        default=f'{date.today().strftime("%Y%m%d")}00',
                        help='end date defaults to this month')
    parser.add_argument('-r', '--recurse', type=int, default=None,
                        action='store', metavar='N',
                        help='sub category depth to include. Defaults to 0')
    parser.add_argument('-l', '--limit', type=int, action='store', metavar='N',
                        help='limit the number of files to analyse. Defaults to no limit.')
    parser.add_argument('-t', '--output_type', action='store',
                        choices=['raw', 'file', 'month', 'day'], default='file',
                        help='collate data per file/month/day, or return raw data. Default "file')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='verbose debugging info')
    parser.add_argument('-o', '--output', action='store', metavar='PATH',
                        default=DEFAULT_OUTPUT, dest='out_file',
                        help=f'output json file. Defaults to {{cwd}}/{DEFAULT_OUTPUT}')
    parser.add_argument('-u', '--user', action='store', required=True,
                        help='username/e-mail to add to User-Agent. See m:User-Agent_policy.')

    return parser.parse_args(argv)


def main() -> None:
    """Command line entrypoint."""
    args = handle_args()
    set_user_agent(args.user)
    result = get_cat_media_views(
        args.cat_name, limit=args.limit, recursion=args.recurse, start=args.start,
        end=args.end, output_type=args.output_type, debug=args.debug)
    result['_meta'] = make_meta(args)
    output_result(result, args.out_file)


if __name__ == "__main__":
    main()
