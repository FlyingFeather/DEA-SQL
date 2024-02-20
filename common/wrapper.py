# -*- coding: utf-8 -*-
# @Author : 
# @Email : 
# @Time : 2023/11/9 11:43
import random
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from functools import wraps


def self_consistency(n, keys, mode):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            try:
                self = args[0]
                nums = self.sc_number
            except:
                nums = n

            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(func, *args, **kwargs) for _ in range(nums)]
                outputs = [future.result() for future in futures]
            output, statistics = combine_json(outputs, keys, mode)
            return output, statistics

        return wrapper

    return decorator


def convert_str_to_element(input_str):
    try:
        element = eval(input_str)
    except:
        element = input_str
    return element


def get_most_voted_values(values_list, mode):
    def count_most_common(values):
        count = Counter(values)
        most_common = count.most_common()
        max_votes = most_common[0][1]
        most_common_candidates = [i[0] for i in most_common if i[1] == max_votes]
        selected_candidate = random.choice(most_common_candidates)
        return selected_candidate, dict(count)

    count_results = []
    vote_stats = []

    if mode == "all":
        count_result, vote_stat = count_most_common(values_list)
        count_results, vote_stats = count_result, vote_stat
    else:
        for values in values_list:
            count_result, vote_stat = count_most_common(values)
            count_results.append(count_result)
            vote_stats.append(vote_stat)

    return count_results, vote_stats


def combine_json(json_list, keys, mode):
    """
    combine a list of json to a single json, which is the most consistent on the given keys
    :param json_list: a list of similar json with same keys but possible different values
    :param keys: a list of keys needs to be consistent
    :param mode: consistency mode of keys, accept "all" or "each"
    :return: a consistent json and the vote statistics
    """

    if not json_list or not json_list[0]:
        return None, None

    if not keys:
        keys = list(json_list[0].keys())

    consistent_json, vote_statistics = {}, {}

    values_list = []
    for json_obj in json_list:
        key_values = [str(json_obj[key]) for key in keys if key in json_obj]
        values_list.append(tuple(key_values))

    if mode == "all":
        most_consistent_values, vote_statistics_list = get_most_voted_values(values_list, mode)
        consistent_json = dict(zip(keys, list(map(convert_str_to_element, most_consistent_values))))
        vote_statistics = vote_statistics_list

    elif mode == "each":
        values_list_transpose = list(zip(*values_list))
        most_consistent_values, vote_statistics_list = get_most_voted_values(values_list_transpose, mode)
        consistent_json = dict(zip(keys, list(map(convert_str_to_element, most_consistent_values))))
        vote_statistics = dict(zip(keys, [stat for stat in vote_statistics_list]))

    return consistent_json, vote_statistics


# examples

@self_consistency(5, keys=['name', 'age', 'city'], mode='all')
def my_function():
    name = ['Alice', 'Bob']
    age = [28, 39]
    city = ['New York', 'San Francisco']
    skills = ['Python', 'JavaScript', 'Java']
    output = {
        'name': random.choice(name),
        'age': random.choice(age),
        'city': random.choice(city),
        'skill': random.choices(skills, k=2),
    }
    print(output)
    return output


class MyClass:

    def __init__(self):
        print('inputs:')
        self.sc_number = 3
        results = self.my_function()
        print('results [mode=each]:')
        print(results)

    @self_consistency(5, keys=['name', 'age', 'city'], mode='each')
    def my_function(self):
        name = ['Alice', 'Bob']
        age = [28, 39]
        city = ['New York', 'San Francisco']
        skills = ['Python', 'JavaScript', 'Java']
        output = {
            'name': random.choice(name),
            'age': random.choice(age),
            'city': random.choice(city),
            'skill': random.choices(skills, k=2),
        }
        print(output)
        return output


if __name__ == "__main__":
    # tests

    print('inputs:')
    results = my_function()
    print('results [mode=all]:')
    print(results)

    print('='*50)

    json_list = [
        {'name': 'Bob', 'age': 39, 'city': 'San Francisco', 'skill': ['JavaScript', 'JavaScript']},
        {'name': 'Bob', 'age': 28, 'city': 'San Francisco', 'skill': ['Java', 'JavaScript']},
        {'name': 'Alice', 'age': 39, 'city': 'San Francisco', 'skill': ['JavaScript', 'Python']},
        {'name': 'Alice', 'age': 39, 'city': 'San Francisco', 'skill': ['JavaScript', 'Python']},
    ]
    sc_json, stats = combine_json(json_list, keys=['name', 'age', 'city', 'skill'], mode='all')
    print('inputs:')
    for obj in json_list:
        print(obj)
    print('results [mode=all]:')
    print(sc_json)
    print(stats)

    print('=' * 50)

    sc_json, stats = combine_json(json_list, keys=['name', 'age', 'city', 'skill'], mode='each')
    print('inputs:')
    for obj in json_list:
        print(obj)
    print('results [mode=each]:')
    print(sc_json)
    print(stats)

    print('=' * 50)

    MyClass()
