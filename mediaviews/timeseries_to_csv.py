# take a get_media_views.py output file and output as a csv (totals per time unit)
import json
in_file = input('path to output file: ')
out_file = f'{in_file.rpartition(".")[0]}.csv'
with open(in_file, 'r', encoding ='utf8') as fp:
    data = json.load(fp)

new_data = []

for k, v in data.items():
    if k == '_meta':
        continue
    num = len(v.get('items'))
    new_data.append((k[:-2], v.get('total'), num))

with open(out_file, 'w', encoding ='utf8') as fp:
    a= fp.write('date\tviews\tviewed_files\n')
    for d in new_data:
        a=fp.write('{0}\t{1}\t{2}\n'.format(*d))

print(f'Data saved to {out_file}')
