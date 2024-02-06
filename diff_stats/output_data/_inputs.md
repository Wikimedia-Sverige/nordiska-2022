# inputs for `diff_stats`

`commonsdiff.py` can be found in [Wikimedia-Sverige/commons-diff](https://github.com/Wikimedia-Sverige/commons-diff/).

All of these made use of a `config.json` defined as:

```json
{
    "info_template": {"Nordiska museet Bildminnen image" : "description"},
    "relevant_sdc": ["P180"]
}
```

## 2024-01-10.json

```console
foo@bar:~$ python commonsdiff.py --category "Category:100 000 Bildminnen" --out "diff_stats/output_data/2024-01-10.json" --config config.json --cutoff 2022-06-01 -q
```

### 2024-01-10_stats.json

```console
foo@bar:~$ python diff_stats/get_diff_stats.py 
path to output file: diff_stats/output_data/2024-01-10.json
```

## Göteborgsboken.json

```console
foo@bar:~$ python commonsdiff.py --category "Category:100 000 Bildminnen/Göteborgsboken" --out "diff_stats/output_data/Göteborgsboken.json" --config config.json --cutoff 2023-05-09 -q
```

### Göteborgsboken_stats.json

```console
foo@bar:~$ python diff_stats/get_diff_stats.py 
path to output file: diff_stats/output_data/Göteborgsboken.json
```

## SAS.json

```console
foo@bar:~$ python commonsdiff.py --category "Category:100 000 Bildminnen/SAS Scandinavian Airlines" --out "diff_stats/output_data/SAS.json" --config config.json --cutoff 2023-05-09 -q
```

### SAS_stats.json

```console
foo@bar:~$ python diff_stats/get_diff_stats.py 
path to output file: diff_stats/output_data/SAS.json
```
