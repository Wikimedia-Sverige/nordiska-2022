"""Takes a commons-diff output file and outputs some statistics."""
import json

def check_changes(d, key, stats_data):
    key_data = d.get(key)
    if(key_data.get('added') or key_data.get('removed')):
        stats_data[key] += len(key_data.get('added')) - len(key_data.get('removed'))
        return True
    return False

def analyse_data(data):
    stats = {
        'changed': 0,
        'captions': 0,
        'categories': 0,
        'descriptions': 0,  # counts if changed, not number of additions
        'statements': 0,
        'all': 0
    }

    languages = set()
    for d in data:
        stats['all'] += 1
        change = False
        change = change or check_changes(d, 'captions', stats)
        change = change or check_changes(d, 'categories', stats)
        change = change or check_changes(d, 'statements', stats)

        if d.get('description').get('changed'):
            change = True
            stats['descriptions'] += 1

        if change:
            stats['changed'] += 1

        # check added caption languages
        added_captions = d.get('captions').get('added')
        languages.update([list(val.keys())[0] for val in added_captions])

    stats['caption_languages'] = len(languages)
    return stats

def output_stats(stats, filename, meta):
    outfile = f'{filename.rpartition(".")[0]}_stats.json'
    data = {'meta': meta, 'stats': stats}
    with open(outfile, 'w', encoding ='utf8') as fp:
        json.dump(data, fp, sort_keys=True, indent=2, ensure_ascii=False)
    print(f'Outputted stats to {outfile}')

def process_output(filename):
    results = None

    with open(filename, encoding='utf8') as f:
        results = json.load(f)

    meta = results.get('meta')
    stats = analyse_data(results.get('results'))
    output_stats(stats, filename, meta)


input_file = input('path to output file: ')
process_output(input_file)
