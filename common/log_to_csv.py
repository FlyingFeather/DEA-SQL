# -*- coding: utf-8 -*-
# @Author : 
# @Email : 
# @Time : 2023/11/20 10:34
import re
import sys
import os
import pandas as pd
import sqlparse


def get_filtered_results(results, res_filter=None):
    if not res_filter:
        return results

    return [result for result in results if result.get('result', None) == res_filter]


if len(sys.argv) < 2:
    print('Usage: python script.py <file_path>')
    sys.exit(1)

file_path = sys.argv[1]

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

sections = content.split('################################################################')

results = []

for sec in sections:
    sec = sec.replace('-----------------------------------------------', '')
    section_data = {}
    cur_idx_match = re.search(r'cur_idx: (\d+)', sec)
    if cur_idx_match:
        section_data['cur_idx'] = int(cur_idx_match.group(1))

    origin_idx_match = re.search(r'origin_idx: (\d+)', sec)
    if origin_idx_match:
        section_data['origin_idx'] = int(origin_idx_match.group(1))

    query_match = re.search(r'query: (.+)', sec)
    if query_match:
        section_data['query'] = query_match.group(1)

    init_table_info = re.search(r"init_table_info:(.*?)(?=add_table_info|$)", sec, flags=re.DOTALL)
    if init_table_info:
        section_data['init_table_info'] = init_table_info.group(1).strip()

    ner_results = re.search(r'ner_results: (.+?)\n', sec)
    if ner_results:
        section_data['ner_results'] = ner_results.group(1)

    features = re.search(r'features: (.+?)\n', sec)
    if features:
        section_data['features'] = features.group(1)

    table_info = re.search(r"table_info:(.*?)(?=add_table_info|$)", sec, flags=re.DOTALL)
    if table_info:
        section_data['table_info'] = table_info.group(1).strip()

    add_table_info = re.search(r"add_table_info:(.*?)(?=suggestions:|$)", sec, flags=re.DOTALL)
    if add_table_info:
        section_data['add_table_info'] = add_table_info.group(1).strip()

    question_type = re.search(r'question_type: (.+?)\n', sec)
    if question_type:
        section_data['question_type'] = question_type.group(1)

    ground_truth = re.search(r'groud_truth: (.+?)\n', sec)
    if ground_truth:
        gold_sql = sqlparse.format(ground_truth.group(1), reindent=True, keyword_case='upper')
        section_data['gold_sql'] = gold_sql

    pred_sql = re.search(r'pred: (.+?)\n', sec)
    if pred_sql:
        pred_sql = sqlparse.format(pred_sql.group(1), reindent=True, keyword_case='upper')
        section_data['pred'] = pred_sql

    result = re.search(r'result: (\d+)\n', sec)
    if result:
        section_data['result'] = int(result.group(1))

    if section_data:
        results.append(section_data)

# filter results
filtered_results = get_filtered_results(results, res_filter=None)

# convert to dataframe
df = pd.DataFrame(filtered_results)

# get dir path of file
data_dir = os.path.dirname(file_path)

# output to csv
output_file_name = os.path.basename(file_path).split(".")[0]
output_file = os.path.join(data_dir, f'{output_file_name}.csv')
df.to_csv(output_file, index=False, encoding='utf-8')
print(f'Data saved to {output_file}')
