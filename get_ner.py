# -*- coding: utf-8 -*-
# Project : DEASQL 
# File    : get_ner.py
# Author  : 
# Email   : 
# Time    : 2023/10/16 19:47

import datetime
import re

from common.common import get_prompt_content
from common.config.static_config import CONFIG
from llm.chat import ask_llm
from prompt.get_prompt import get_ner_prompt


class NER(object):
    """
    extract Main Entity from the query
    """

    def __init__(self, engine=CONFIG["methods"]["engine"], model_name=CONFIG["methods"]["model_name"],
                 temperature=CONFIG["methods"]["temperature"]):
        self.engine = engine
        self.max_tokens = CONFIG["max_tokens"]
        self.model_name = model_name
        self.temperature = temperature
        self.today = datetime.date.today().strftime("%Y%m%d")
        self.yesterday = (datetime.date.today() + datetime.timedelta(days=-1)).strftime("%Y%m%d")

    def parse_custom_string(self, input_str):
        input_str = input_str.replace(' ', '').replace('\n', '').replace('"', '')
        key_value_pattern = r"(\w+):\s*({.*?}|[^,{}]+)"
        matches = re.findall(key_value_pattern, input_str)

        result = {}
        for key, value in matches:
            if value.startswith("{"):
                result[key] = self.parse_custom_string(value)
            else:
                result[key] = value
        return result

    def parse_json(self, input_str):
        res = {}
        try:
            pattern = r"\{.*?\}"
            match = re.search(pattern, input_str)
            if match:
                res = eval(match.group())
        except:
            try:
                res = self.parse_custom_string(input_str)
            except Exception as e:
                print(f"=========eval fail==========={e}", exc_info=True)
        return res

    def run(self, query, dataset):
        """
        get NER of users' query, and classify the label of entity
        :param query: user input
        :return: llm output, consist of entity and its entity label within []
        """

        generate_sql_prompt = get_ner_prompt(dataset)

        prompt_dict = {
            "query": query
        }

        prompt = get_prompt_content(generate_sql_prompt, prompt_dict)
        res = ask_llm(prompt)
        res = self.parse_json(res)
        if "entities" in res:
            res["limitation"] = res["entities"]
        for i in ["limitation", "metric", "query"]:
            if i not in res:
                res[i] = []
        return res
