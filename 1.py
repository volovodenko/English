import json
from sys import argv

txt = open("statistic.json").read()
txt2 = json.loads(txt)['data']

learned = []

# for atr, value in txt2.items():
#     if value['en_to_ru'][4] >= 100:
#         learned.append((atr, value))

print(argv[1])
