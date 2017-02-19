#!/usr/bin/python3
import json
import sys


def canonical_json(payload):
    return json.dumps(payload, sort_keys=True, separators=(',', ':'))


print(canonical_json(json.loads(sys.stdin.read())), end='')
