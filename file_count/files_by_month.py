# List creation times for all files in a category
from collections import Counter
import pywikibot
from tqdm import tqdm


def get_creation_month(fp):
    creation_time = fp.oldest_revision.timestamp
    return creation_time.isoformat().rpartition('-')[0]

def output_results(cat, months):
    clean_cat = cat.replace(' ','_').split(':')[-1]
    out_file = f'{clean_cat.replace("/", "-")}_file_count.tsv'
    with open(out_file, 'w', encoding ='utf8') as fp:
        fp.write(f'# File count for {clean_cat}\n')
        fp.write('month\tnew_files\n')
        for month, count in sorted(months.items()):
            fp.write(f'{month}\t{count}\n')

    pywikibot.output(f'Data saved to {out_file}')

def count_new_files_by_month(category_name):
    site = pywikibot.Site('commons', 'commons')
    cat = pywikibot.Category(site, category_name)
    months = Counter()

    for file_page in tqdm(cat.members(member_type=['file']), desc="Processing category members", total=cat.categoryinfo.get('files')):
        months[get_creation_month(file_page)] += 1

    return months


category = input('category name: ')
out_data = count_new_files_by_month(category)
output_results(category, out_data)
