# inputs for `mediaviews`

## 100kBildminne_2023.json

```console
foo@bar:~$ python mediaviews/get_media_views.py -c "100 000 Bildminnen" -s 20230101 -e 20240101 -t month -o "mediaviews/output_data/100kBildminne_2023.json" -u "<username>"
```

### 100kBildminne_2023.csv

```console
foo@bar:~$ python mediaviews/timeseries_to_csv.py
path to output file: mediaviews/output_data/100kBildminne_2023.json
```

## NM_stats_2022.json

```console
foo@bar:~$ python mediaviews/get_media_views.py -c "Images from Nordiska museet" -s 20220101 -e 20230101 -t month -o "mediaviews/output_data/NM_stats_2022.json" -u "<username>"
```

### NM_stats_2022.csv

```console
foo@bar:~$ python mediaviews/timeseries_to_csv.py
path to output file: mediaviews/output_data/NM_stats_2022.json
```

## NM_stats_2023.json

```console
foo@bar:~$ python mediaviews/get_media_views.py -c "Images from Nordiska museet" -s 20230101 -e 20240101 -t month -o "mediaviews/output_data/NM_stats_2023.json" -u "<username>"
```

### NM_stats_2023.csv

```console
foo@bar:~$ python mediaviews/timeseries_to_csv.py
path to output file: mediaviews/output_data/NM_stats_2023.json
```
