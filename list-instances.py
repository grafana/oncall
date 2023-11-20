import json
from collections import defaultdict


def write_lines(filename, data):
    with open(filename, 'w') as f:
        for line in data:
            f.write(f"{line}\n")

def active_or_not(status):
    if status == "active":
        return "active"
    else:
        return "non_active"


with open('instances.json') as f:
    instances = json.load(f)

groups = defaultdict(set)
for i in instances["items"]:
    groups[active_or_not(i["status"])].add(i["slug"])


for key, value in groups.items():
    print(f"{key}: {len(value)}")
    write_lines(f"{key}_instances", value)
