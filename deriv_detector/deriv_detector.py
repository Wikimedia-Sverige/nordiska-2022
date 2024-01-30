# https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=linkshere&continue=gcmcontinue%7C%7C&generator=categorymembers&formatversion=2&lhprop=pageid%7Ctitle%7Credirect&lhnamespace=6&lhshow=!redirect&lhlimit=max&gcmtitle=Category%3A100%20000%20Bildminnen&gcmtype=file&gcmlimit=max
import json
import pywikibot
from tqdm import tqdm


def get_infiles(fp):
    links = fp.backlinks(filter_redirects=False, namespaces=['file'])
    return [link for link in links]

def output_results(cat, data):
    clean_cat = cat.replace(' ','_').split(':')[-1]
    out_file = f'{clean_cat.replace("/", "-")}_backlinks.json'
    with open(out_file, 'w', encoding ='utf8') as fp:
        json.dump(data, fp, sort_keys=True, indent=2, ensure_ascii=False)
        pywikibot.output(f'Data saved to {out_file}')

def count_relations(data):
    relations = set()
    for k, v in data.items():
        for vv in v:
            relations.add(frozenset([k, vv]))
    print(f'There were {len(relations)} unique relations detected')

def detect_derivatives(category_name):
    site = pywikibot.Site('commons', 'commons')
    cat = pywikibot.Category(site, category_name)
    data = {}

    for file_page in tqdm(cat.members(member_type=['file']), desc="Processing category members", total=cat.categoryinfo.get('files')):
        in_files = get_infiles(file_page)
        if in_files:
            data[file_page.title()] = [in_file.title() for in_file in in_files]

    count_relations(data)
    return data


category = input('category name: ')
out_data = detect_derivatives(category)
output_results(category, out_data)
