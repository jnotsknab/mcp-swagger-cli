import yaml
import json
import os

files = [
    'openapi_2.0_sample.yaml',
    'openapi_3.0_sample.yaml',
    'special_description.yaml'
]

base_path = '/output/test_specs/'

for f in files:
    path = os.path.join(base_path, f)
    with open(path, 'r') as file:
        try:
            content = yaml.safe_load(file)
            print(f"Parsed {f} successfully.")
        except Exception as e:
            print(f"Error parsing {f}: {e}")
