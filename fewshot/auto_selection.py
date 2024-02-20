# -*- coding: utf-8 -*-
# @Author : 
# @Email : 
# @Time : 2023/11/23 10:25
import numpy as np
import random
import pickle
from typing import Dict, List, Union
from sklearn.neighbors import NearestNeighbors

from fewshot.processor import mask_query_by_entities
from fewshot.embedding import embed_by_openai, embed_by_transformers


def get_random_samples(train: Dict, n_samples=1) -> List[Dict]:
    """
    Randomly samples from train set

    :param train: the train set
    :param n_samples: the num of samples
    :return: a list of samples
    """
    if n_samples > len(train):
        raise ValueError("n_samples should be less than or equal to len(train)")

    # random n sample
    samples = random.sample(list(train.values()), n_samples)

    return samples


def get_similar_text_embed_by_knn(train: Dict, text: str, model='transformer', n_samples=1) -> List[Dict]:
    """
    Get similar samples from train set based on text embedding

    :param train: the train set
    :param text: the text to embed, which can be the original question, masked question or SQL query
    :param model: the embedding model to use, which can be transformer or openai
    :param n_samples: the num of samples
    :return: a list of samples
    """

    text2vec = embed_by_transformers if model == 'transformer' else embed_by_openai
    candidate_embeds = list(train.keys())
    target_embed = text2vec(text)
    target_embed = np.array(target_embed)
    print('candidate_embeds', len(candidate_embeds), len(candidate_embeds[0]))
    print('target_embeds', target_embed.shape)

    # Fit KNN model
    knn = NearestNeighbors(n_neighbors=n_samples, metric="cosine")
    knn.fit(candidate_embeds)

    # Find the nearest neighbors for the given question
    distances, indices = knn.kneighbors(target_embed.reshape(1, -1))

    # Get instances of most similar questions
    most_similar_questions = [train[candidate_embeds[idx]] for idx in indices.flatten()]

    return most_similar_questions


def get_shots_by_mode(mode, train, question, entities, sql, model, n_shots):
    """
    Get top-n few-shots by mode
    """
    shots = []
    if mode == 'random':
        shots = get_random_samples(train, n_samples=n_shots)
    elif mode == 'ques_sim':
        shots = get_similar_text_embed_by_knn(train, question, model=model, n_samples=n_shots)
    elif mode == 'masked_ques_sim':
        mask_question = mask_query_by_entities(question, entities)
        shots = get_similar_text_embed_by_knn(train, mask_question, model=model, n_samples=n_shots)
    elif mode == 'query_sim':
        shots = get_similar_text_embed_by_knn(train, sql, model=model, n_samples=n_shots)

    return shots


def get_train_set(question_type: List[str], mode='random', model='transformer',
                  index_version='train_fold1_v1', ques_type_mode='each'):
    """
    Obtain train set according to different input parameters
    """

    output_dir = f'fewshot/index_{index_version}/'
    output_file_map = {
        'random': f'query_embed_{model}.pkl',
        'ques_sim': f'query_embed_{model}.pkl',
        'masked_ques_sim': f'masked_query_embed_{model}.pkl',
        'query_sim': f'pred_embed_{model}.pkl',
    }
    output_file = output_file_map.get(mode, '')

    if not output_file:
        return {}

    with open(output_dir + output_file, 'rb') as f:
        data = pickle.load(f)

    if ques_type_mode == 'each':
        all_train = {q_type: {} for q_type in question_type}
        for emb, sample in data.items():
            q_type = sample.get('question_type', '')
            if q_type in question_type:
                all_train[q_type][emb] = sample
    else:
        all_train = {}
        for emb, sample in data.items():
            q_type = sample.get('question_type', '')
            if q_type in question_type:
                all_train[emb] = sample
    return all_train


def get_fewshots(question: str, entities: List[str], sql: str, question_type: List[str],
                 n_shots=1, mode='random', model='transformer',
                 index_version='train_fold1_v1', ques_type_mode='each') -> Union[Dict, List]:
    """
    Get fewshots according to different input parameters

    :param question: the question
    :param entities: the entities
    :param sql: the sql
    :param question_type: the question type
    :param n_shots: the num of shots
    :param mode: the retrieval mode, which can be random, ques_sim, masked_ques_sim, query_sim
    :param model: the embedding model, which can be transformer or openai
    :param index_version: the version name of index library
    :param ques_type_mode: the question type recall mode, each for separate recall, all is combined recall
    :return: the fewshot samples
    -ques_type_mode=each
         - Type: Dict
         - key is the question type
         - value is a list of few shots recalled corresponding to the question type, each element is a sample, and each sample is a Dict
    -ques_type_mode=all
         - Type: List
         - Each element is a sample and each sample is a Dict
    """

    assert mode in ['random', 'ques_sim', 'masked_ques_sim', 'query_sim']
    assert model in ['transformer', 'openai']
    assert ques_type_mode in ['each', 'all']

    all_train = get_train_set(question_type, mode, model, index_version, ques_type_mode)

    if ques_type_mode == 'each':
        all_shots = {}
        for q_type in question_type:
            train = all_train[q_type]
            shots = get_shots_by_mode(mode, train, question, entities, sql, model, n_shots)
            all_shots[q_type] = shots
    else:
        all_shots = get_shots_by_mode(mode, all_train, question, entities, sql, model, n_shots)

    return all_shots


if __name__ == '__main__':

    fewshots = get_fewshots(
        question='find the name of employee who was awarded the most times in the evaluation.',
        entities=["name of employee", "awarded the most times", "evaluation"],
        sql="SELECT Name FROM EMPLOYEE WHERE Employee_ID IN (SELECT Employee_ID FROM EVALUATION GROUP BY Employee_ID HAVING COUNT(*) = (SELECT MAX(count) FROM (SELECT COUNT(*) as count FROM EVALUATION GROUP BY Employee_ID)))",
        question_type=['JOIN-NESTED'],
        mode='ques_sim',
        n_shots=2,
        model='transformer'
    )

    print(fewshots)

    fewshots = get_fewshots(
        question='find the name of employee who was awarded the most times in the evaluation.',
        entities=["name of employee", "awarded the most times", "evaluation"],
        sql="SELECT Name FROM EMPLOYEE WHERE Employee_ID IN (SELECT Employee_ID FROM EVALUATION GROUP BY Employee_ID HAVING COUNT(*) = (SELECT MAX(count) FROM (SELECT COUNT(*) as count FROM EVALUATION GROUP BY Employee_ID)))",
        question_type=['JOIN-NESTED'],
        mode='masked_ques_sim',
        n_shots=2,
        model='openai'
    )

    print(fewshots)

    fewshots = get_fewshots(
        question='find the name of employee who was awarded the most times in the evaluation.',
        entities=["name of employee", "awarded the most times", "evaluation"],
        sql="SELECT Name FROM EMPLOYEE WHERE Employee_ID IN (SELECT Employee_ID FROM EVALUATION GROUP BY Employee_ID HAVING COUNT(*) = (SELECT MAX(count) FROM (SELECT COUNT(*) as count FROM EVALUATION GROUP BY Employee_ID)))",
        question_type=['JOIN-NESTED'],
        mode='query_sim',
        n_shots=2,
        model='openai',
        index_version='train_fold2_v1'
    )

    print(fewshots)

    fewshots = get_fewshots(
        question='find the name of employee who was awarded the most times in the evaluation.',
        entities=["name of employee", "awarded the most times", "evaluation"],
        sql="SELECT Name FROM EMPLOYEE WHERE Employee_ID IN (SELECT Employee_ID FROM EVALUATION GROUP BY Employee_ID HAVING COUNT(*) = (SELECT MAX(count) FROM (SELECT COUNT(*) as count FROM EVALUATION GROUP BY Employee_ID)))",
        question_type=['JOIN-NESTED'],
        mode='masked_ques_sim',
        n_shots=2,
        model='openai',
        ques_type_mode='all'
    )

    print(fewshots)
