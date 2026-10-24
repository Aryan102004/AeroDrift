 .gitignore                            |  11 [32m+[m[31m-[m
 aerodrift/dashboard/cli.py            | 214 [32m+++++++++++++++++++++++++++++++++[m[31m-[m
 aerodrift/reports/__init__.py         |   0
 aerodrift/reports/incident_report.py  | 194 [32m++++++++++++++++++++++++++++++[m
 aerodrift/storage/__init__.py         |   0
 aerodrift/storage/comparator.py       |  65 [32m+++++++++++[m
 aerodrift/storage/snapshot_store.py   | 140 [32m++++++++++++++++++++++[m
 main.py                               |  55 [32m+++++++[m[31m--[m
 requirements.txt                      |   5 [32m+[m
 tests/reports/__init__.py             |   0
 tests/reports/test_incident_report.py |  57 [32m+++++++++[m
 tests/storage/test_comparator.py      |  67 [32m+++++++++++[m
 tests/storage/test_snapshot_store.py  |  76 [32m++++++++++++[m
 13 files changed, 868 insertions(+), 16 deletions(-)
