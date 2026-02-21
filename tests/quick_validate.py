#!/usr/bin/env python3
import tomllib

with open('/output/test_special/pyproject.toml', 'rb') as f:
    data = tomllib.load(f)

desc = data['tool']['poetry']['description']
print('Description:', repr(desc))
print('Length:', len(desc))

# Validate
assert '\n' not in desc
assert '\t' not in desc  
assert len(desc) <= 200
print('ALL VALIDATIONS PASSED')
