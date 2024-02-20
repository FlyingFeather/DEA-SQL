# -*- coding: utf-8 -*-
# @Author : 
# @Email : 
# @Time : 2023/11/20 10:34
import json
import os
import sys
import pandas as pd


def get_filtered_results(results, res_filter=0):
    return [result for result in results if result.get('result', None) == res_filter]


if len(sys.argv) < 2:
    print('Usage: python script.py <file_path>')
    sys.exit(1)

file_path = sys.argv[1]
data_dir = os.path.dirname(file_path)
output_file = f"{data_dir}/output.txt"

df = pd.read_csv(file_path)

# Convert each row to JSON format and save
with open(output_file, "w") as f:
    for index, row in df.iterrows():
        row_json = row.to_dict()
        try:
            row_json['ner_results'] = eval(row_json['ner_results'])
        except:
            row_json['ner_results'] = ''

        try:
            row_json['features'] = eval(row_json['features'])
        except:
            row_json['features'] = ''

        f.write(json.dumps(row_json) + '\n')

print(f'Data saved to {output_file}')