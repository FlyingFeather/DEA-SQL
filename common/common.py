# -*- coding: utf-8 -*-
# Project : DEASQL
# File    : common.py
# Author  : 
# Email   : 
# Time    : 2023/10/16 19:58
import json
import os
import pickle
import re

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate


def run_chain(llm, prompt, param_dicts):
    chain = LLMChain(llm=llm, prompt=prompt)
    output = chain.run(**param_dicts)
    return output


def get_prompt(inputs, template):
    prompt = PromptTemplate(
        input_variables=inputs,
        template=template
    )
    return prompt


def get_prompt_content(prompt, param_dicts):
    formatted_text = prompt.format(**param_dicts)
    return formatted_text


def save_obj(obj, name):
    """
    save pickle

    :param obj: The data that needs to be stored.
    :param name: file path
    """
    with open(name, "wb") as file:
        pickle.dump(obj, file)


def load_obj(name):
    """load pickle"""
    with open(name, "rb") as file:
        return pickle.load(file)


def get_lower_list(temp_list):
    target_list = [word.lower() for word in temp_list]
    return target_list


def extract_references(sql):
    pattern = r"REFERENCES\s+(\w+)\s+\((\w+)\)"
    matches = re.findall(pattern, sql)
    return matches


def extract_label(text):

    pattern = r"Label: ([\w-]+), ([\w-]+)"

    result = re.search(pattern, text)
    return_label = []

    if result:
        labels = result.groups()
        if "NON-JOIN" in labels and "NON-NESTED" in labels:
            return_label.append("EASY")
        elif "JOIN" in labels and "NON-NESTED" in labels:
            return_label.append("JOIN")
        elif "NESTED" in labels and "NON-JOIN" in labels:
            return_label.append("NESTED")
        elif "NESTED" in labels and "JOIN" in labels:
            return_label.append("JOIN-NESTED")
        else:
            return_label.append("EASY")

        if "MAX" in labels:
            return_label.append("MAX")
        elif "MIN" in labels:
            return_label.append("MIN")
        elif "SUM" in labels:
            return_label.append("SUM")
        elif "AVG" in labels:
            return_label.append("AVG")
        elif "COUNT" in labels:
            return_label.append("COUNT")
        else:
            return_label.append("NON")
        return return_label[0], return_label[1]
    return "EASY", "NON"


def extract_sql(text, init_sql):
    pattern = r'The modified SQL: (.*)'

    result = re.search(pattern, text)
    if "not an extremum problem" in text:
        return init_sql

    if result:
        modified_sql = result.group(1)
        return modified_sql
    else:
        print("No match found.")
        return init_sql


def get_dict_from_str(content):
    content = content.replace("\n", " ")
    content = content.replace("，", ",")
    result = json.loads(content)
    return result


def load_or_save(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            data = json.load(f)
        return data
    else:
        with open(filename, 'w') as f:
            json.dump(data, f)


def ensure_dir(dir_path):
    r"""Make sure the directory exists, if it does not exist, create it

    Args:
        dir_path (str): directory path

    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
