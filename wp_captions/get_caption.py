"""Gets all images in a category and for each gets all global usages and associated captions.

Limitations:
* Not all Wikimedia wikis support returning captions.
* Captions in <gallery>-tags are only returned if retrieve_gallery is set to True.
* It does not filter by Namespace (but namespace is displayed in the results)

This loops over all the images in the category and then over all pages which they appear on,
so it isn't fast and doesn't make use of e.g. combined Action-API calls.
"""
import argparse
import json
import urllib.parse
import os
from collections import defaultdict
from datetime import date

import pywikibot
import requests
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
from pywikibot.exceptions import APIError
from tqdm import tqdm

DEFAULT_OUTPUT = 'caption_output.json'
HEADERS = {
    'User-Agent': 'get_caption_pywiki.py/1.0 (https://gist.github.com/lokal-profil/ea58e2b8563cdf4ab4ccdbe75a701fa2; {})'
}
RETRIES = Retry(total=5, backoff_factor=0.1)


def get_category_captions(
        cat_name: str, limit: int = None, recursion: int = 0,
        retrieve_gallery: bool = False, debug: bool = False) -> (dict, dict):
    """Retrieve captions from the provided category."""
    commons = pywikibot.Site('commons', 'commons')
    category = pywikibot.Category(commons, cat_name)
    file_usages, stats = process_cat_members(category, recurse=recursion, limit=limit)
    captions = get_multiple_captions(file_usages, retrieve_gallery=retrieve_gallery, debug=debug)
    return captions, stats


def process_cat_members(cat: pywikibot.Category, recurse: int = 0, limit: int = None) -> (dict, dict):
    """Process each member file of a category and its global usage."""
    usage = {}
    used = 0  # differs from len(files) in that it only counts files with captions
    files = set()
    category_members = cat.members(recurse=recurse, member_type='file', total=limit)
    total = (limit or cat.categoryinfo.get('files') if not recurse else None)
    for file_page in tqdm(category_members, desc="Processing category members", total=total):
        if file_page in files:
            continue  # since same file can occur in recursive categories
        files.add(file_page)
        counted = False
        file_usages = file_page.globalusage()  # would be great to discard transcluded pages
        for file_usage in file_usages:
            if not counted:
                used += 1
                counted = True
            fu_site = file_usage.site.dbName()
            if fu_site not in usage:
                usage[fu_site] = defaultdict(list)
            usage[fu_site][file_usage.title()].append(file_page.title(with_ns=False))

    num_pages = sum([len(us) for us in usage.values()])
    num_usages = sum([sum([len(pages) for pages in us.values()]) for us in usage.values()])
    pywikibot.output(
        f'Found {used} files used {num_usages} times across {num_pages} pages on {len(usage)} sites.')
    stats = {
        'used files': used,
        'usages': num_usages,
        'pages': num_pages,
        'sites': len(usage)
    }
    return usage, stats


def get_multiple_captions(
        file_usages: dict, retrieve_gallery: bool = False, debug: bool = False) -> dict:
    """For a given list of file_usages, retrieve all of the captions.
    
    retrieve_gallery checks for <gallery> contents if a file did not appear in the regular
    captions. This might be slow.
    """

    # Run connection through a session to limit hammering
    s = requests.Session()
    s.mount(
        'https://',
        HTTPAdapter(max_retries=RETRIES))
    s.headers.update(HEADERS)

    captions = defaultdict(list)
    for site, pages in file_usages.items():
        site_obj = pywikibot.APISite.fromDBName(site)
        site_url = site_obj.siteinfo.get('servername')
        for page, files in tqdm(pages.items(), desc=f"Processing captions on {site}"):
            missing_captions = False
            try:
                media = get_media_list(
                    s, page, site_url, drop_empty=not(retrieve_gallery), debug=debug)
            except APIError:
                pywikibot.log(f"{site} does not support page/media-list endpoint.")
                break  # also skips gallery retrieval for these
            for file in files:
                caption = media.get(file)
                if caption:
                    captions[file].append({
                        'caption': caption,
                        'site': site,
                        'page': page})
                elif caption is None:
                    missing_captions = True

            if retrieve_gallery and missing_captions:
                try:
                    gallery_caps = get_gallery_content(s, page, site_url, debug=debug)
                except APIError:
                    pywikibot.log(f"{site} does not support page/html endpoint.")
                    break
                for file in files:
                    caption = gallery_caps.get(file)
                    if caption:
                        captions[file].append({
                            'caption': caption,
                            'site': site,
                            'page': page})
    return captions


def get_media_list(
        s: requests.Session, page: str, site_url: str,
        drop_empty: bool = True, debug: bool = True) -> dict:
    """Return a simplified list of filenames and captions.

    Note that this does not capture captions inside <gallery>, T346352.
    
    drop_empty removes entries with blank or missing captions from the output. If not provided
    empty strings are used for blank captions and None is used for missing captions (e.g. for files
    appearing inside <gallery>).
    """
    if debug:
        print(f"I'm looking up: {page}")
    url = f'https://{site_url}/api/rest_v1/page/media-list/{urllib.parse.quote(page, safe="")}'
    res = s.get(url, timeout=30)
    if debug:
        print(f"request_result: {res.status_code}")
    if res.status_code == 404:
        raise APIError('999', 'Rest-API endpoint not found')
    data = res.json()
    outdata = {}
    for image in data.get('items'):
        caption = image.get('caption', {}).get('text')
        if caption:
            caption = caption.strip()
        if not caption and drop_empty:
            continue
        image = image.get('title').partition(':')[2]
        outdata[image.replace('_', ' ')] = caption
        if debug and caption:
            print(f"{image} -- Found caption: {caption}")

    return outdata


def get_gallery_content(
        s: requests.Session, page: str, site_url: str,
        gallery_id: str = None, debug: bool = True) -> dict:
    """Retrieve all files and captions which appear in galleries on a page.
    
    This can either loop over all galleries or be restricted to only those galleries that match
    a given id, as provided by the page/media-list/ REST-API.

    If a file appears in a gallery but does not have a caption it will appear in the output with
    a None-value.
    """
    # fetch data
    if debug:
        print(f"I'm doing a gallery look-up of: {page}")
    url = f'https://{site_url}/api/rest_v1/page/html/{urllib.parse.quote(page, safe="")}'
    res = s.get(url, timeout=30)
    if debug:
        print(f"request_result: {res.status_code}")
    if res.status_code == 404:
        raise APIError('999', 'Rest-API endpoint not found')

    # prepp beautiful soup
    html = res.text
    soup = BeautifulSoup(html, features='html5lib')
    #
    captions = {}  # assume no image appears more than once
    for gb in soup.find_all('li', class_='gallerybox'):
        if gallery_id and gb.parent.id != gallery_id:
            continue
        for mfd in gb.find_all('a', class_='mw-file-description'):
            file = mfd.get('href').partition(':')[2]
            captions[file.replace('_', ' ')] = mfd.get('title')
    return captions


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
        description=('Select a category on Commons and download associated captions across '
                    'all Wikimedia projects.'))
    parser.add_argument('-c', '--category', action='store', metavar='CAT',
                        required=True, dest='cat_name',
                        help='Commons category to process (with or without Category:-prefix)')
    parser.add_argument('--no_gallery', action='store_true',
                        help='do not retrieve captions from galleries (faster)')
    parser.add_argument('-r', '--recurse', type=int, default=None,
                        action='store', metavar='N',
                        help='sub category depth to include. Defaults to 0')
    parser.add_argument('-l', '--limit', type=int, action='store', metavar='N',
                        help='limit the number of files to analyse. Defaults to no limit.')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='verbose debugging info')
    parser.add_argument('-o', '--output', action='store', metavar='PATH',
                        default=DEFAULT_OUTPUT, dest='out_file',
                        help=f'output json file. Defaults to {{cwd}}/{DEFAULT_OUTPUT}')
    parser.add_argument('-u', '--user', action='store', required=True,
                        help='username/e-mail to add to User-Agent. See m:User-Agent_policy.')

    return parser.parse_args(argv)


# consider sticking results under results to not have _meta at the same level
def main() -> None:
    """Command line entrypoint."""
    args = handle_args()
    results, stats = get_category_captions(
        args.cat_name, limit=args.limit, recursion=args.recurse,
        retrieve_gallery=not(args.no_gallery), debug=args.debug)
    out_data = {
        'meta': make_meta(args),
        'stats': stats,
        'results': results
        }
    output_result(out_data, args.out_file)


if __name__ == "__main__":
    main()
