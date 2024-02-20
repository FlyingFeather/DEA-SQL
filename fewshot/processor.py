# -*- coding: utf-8 -*-
# @Author : 
# @Email : 
# @Time : 2023/11/23 14:26
import json
import numpy as np
import os
import pickle
import re
import sys
from typing import List

from fewshot.embedding import embed_by_openai
from fewshot.embedding import embed_by_transformers


def mask_query_by_entities(query: str, entities: List[str]) -> str:
    """masked query by entities"""
    masked_query = query
    for entity in entities:
        masked_query = masked_query.replace(entity, '<MASK>')
    return masked_query


def gen_mask_samples(input_file):

    print(f'Start masking...')
    print(f'data: {input_file}')

    # Read and process the input data
    input_file = input_file
    samples = []
    with open(input_file, 'r') as f:
        for line in f:
            sample = json.loads(line)  # Parse JSON text
            query = sample.get('query', '')  # Extract key to embed
            entities = sample.get('ner_results', {}).get('entities', [])
            masked_query = mask_query_by_entities(query, entities)
            sample['masked_query'] = masked_query
            samples.append(sample)

    output_file = re.sub(r"(\w+)\.txt$", r"masked_\1.txt", input_file)
    with open(output_file, 'w') as f:
        for sample in samples:
            f.write(json.dumps(sample) + '\n')
    print(f'Saved masked samples to: {output_file}')


def gen_embed_and_save(input_file, version, key, model='transformer'):

    # validate keys
    assert key in ['query', 'pred', 'masked_query']
    assert model in ['openai', 'transformer']

    print(f'Start embedding...')
    print(f'data: {input_file}')
    print(f'key: {key}')
    print(f'model: {model}')

    # Read and process the input data
    input_file = input_file
    data = {}
    queries = []
    samples = []
    with open(input_file, 'r') as f:
        for line in f:
            sample = json.loads(line)  # Parse JSON text
            query = sample[key]  # Extract key to embed
            queries.append(query)
            samples.append(sample)

    # Convert queries to vectors in a batch
    query_vectors = []
    if model == 'openai':
        query_vectors = []
        max_batch_size = 16
        for i in range(0, len(queries), max_batch_size):
            sub_queries = queries[i:i + max_batch_size]
            sub_query_vectors = embed_by_openai(sub_queries)
            query_vectors += sub_query_vectors
    elif model == 'transformer':
        query_vectors = None
        max_batch_size = 200
        print(f'batch size: {max_batch_size}')
        for i in range(0, len(queries), max_batch_size):
            print(f'current batch {i}:{i + max_batch_size}')
            sub_queries = queries[i:i + max_batch_size]
            sub_query_vectors = embed_by_transformers(sub_queries)
            if query_vectors is None:
                query_vectors = sub_query_vectors
            else:
                query_vectors = np.vstack((query_vectors, sub_query_vectors))

    query_vectors = np.array(query_vectors)
    print(query_vectors.shape)

    # generate key-value pair {embedding: sample}
    for query_vector, sample in zip(query_vectors, samples):
        data[tuple(query_vector)] = sample

    # Save the results to file
    output_file = f'{key}_embed_{model}.pkl'
    output_dir = f'fewshot/index_{version}/'

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Save embedding results to {output_dir + output_file}.")
    with open(output_dir + output_file, "wb") as f:
        pickle.dump(data, f)


if __name__ == '__main__':

    if len(sys.argv) != 5:
        print('Usage: python -m fewshot.processor <file_path> <mode> <key> <model>')
        sys.exit(1)

    file_path = sys.argv[1]
    mode = sys.argv[2]
    key = sys.argv[3]
    model = sys.argv[4]

    # get file_path's parent dir name
    file_dir = os.path.dirname(file_path)
    version = os.path.basename(file_dir)

    if mode == 'emb':
        gen_embed_and_save(file_path, version=version, key=key, model=model)

    if mode == 'mask':
        gen_mask_samples(file_path)
