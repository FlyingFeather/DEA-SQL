# -*- coding: utf-8 -*-
# Project : DEASQL 
# File    : filter_characters.py
# Author  : 
# Email   : 
# Time    : 2023/12/25 20:57
import concurrent.futures
import re

from sql_metadata import Parser

from common.common import (
    get_prompt_content,
    get_lower_list,
    extract_references,
    get_dict_from_str
)
from llm.chat import ask_llm
from prompt.get_prompt import get_characters_from_sql_prompt


def get_simple_table_infos(table_info, target_characters, special_for_bird=False):
    print("detail", target_characters)
    if special_for_bird:
        if target_characters == [""]:
            return
        target_characters = [re.sub(r'[,\-;:"\']', '', i) for i in target_characters]
        lines = table_info.split('\n')
        result = [lines[0]]
        for line in lines[1:]:
            if ("insert" in line.lower()) or (");" in line) or ("foreign key" in line.lower()) or (
                    "primary key" in line.lower()):
                result.append(line.replace("\"", ''))
            else:
                new_line = re.sub(r'[,\-;:"\']', '', line)
                for character in target_characters:
                    if character.lower() in new_line.lower():
                        result.append(re.sub(r'[;:]', '', line))
                        break
        result.append(");")
    else:
        lines = table_info.split('\n')
        result = [lines[0]]
        for line in lines[1:]:
            if ("insert" in line.lower()) or (");" in line) or ("foreign key" in line.lower()) or (
                    "primary key" in line.lower()):
                result.append(line)
            else:
                new_line = re.sub(r'[`,\-;:"\']', '', line)
                characters = new_line.strip().split()[0].strip()
                if characters.lower() in target_characters:
                    result.append(re.sub(r'[\-;:]', '', line))
    return '\n'.join(result)


def get_characters_in_table(table_info):
    all_characters = []
    lines = table_info.split('\n')
    for line in lines[1:]:
        if ("insert" in line.lower()) or (");" in line) or ("foreign key" in line.lower()) or (
                "primary key" in line.lower()):
            continue
        else:
            new_line = re.sub(r'[`,\-;:"\']', '', line)
            characters = new_line.strip().split()[0].strip()
            all_characters.append(characters)
    return all_characters


def get_single_table_info(table_info_list, table_name, target_characters, table_list):
    table_name = table_name.lower()
    # There may be separate characters other than list when using foreign keys.
    if not isinstance(target_characters, list):
        target_characters = [target_characters]
    target_characters = [i.lower() for i in target_characters if i != ""]
    table_list = [i.lower() for i in table_list]
    simple_table_info = ""
    for table_info, table_list_temp in zip(table_info_list, table_list):
        if table_name == table_list_temp:
            simple_table_info = get_simple_table_infos(table_info, target_characters)
    return simple_table_info


def split_characters(original_list):
    new_list = [item.split('.')[-1].strip().lower() for item in original_list]
    return new_list


def split_characters_table_name(original_list):
    new_list = [item.split('.')[0].strip().lower() for item in original_list]
    return new_list


class FilterCharacters:
    def __init__(self):
        self.id_characters = []
        self.time_characters = []

        # Expose the final field filtering results and perform field filtering integration on the outer layer
        self.col_list = []
        self.table_list = []

    def get_merge_infos(self, mode, features, table_list, table_info_list, nums):
        executor = concurrent.futures.ThreadPoolExecutor()
        function_args = [
            (mode, feature, table_list, table_info_list) for feature in features
        ]

        results = []
        for args in function_args:
            future = executor.submit(self.filter_characters_for_complex, *args)
            results.append(future)

        concurrent.futures.wait(results)

        target_table_set = set()
        target_character_set = set()

        for future in results:
            target_table, target_character = future.result()
            target_table_set.update(target_table)
            target_character_set.update(target_character)

        target_table = list(target_table_set)
        target_character = list(target_character_set)
        return target_table, target_character

    def get_characters_from_sql_for_complex(self, sql):
        sql_prompt = get_characters_from_sql_prompt()
        prompt_dict = {
            "sql": sql
        }
        sql_prompt = get_prompt_content(sql_prompt, prompt_dict)
        sql = ask_llm(sql_prompt)
        try:
            sql = get_dict_from_str(sql)
        except Exception as e:
            print("---------------get_characters_from_sql---------------------")
            print(f"==============={e.args}")
            sql = {"All field names": [""]}
        return sql

    def get_table_characters_from_foreign_key(self, table_info, new_table_list):
        foreign_table_list = {}
        all_foreign_key_infos = extract_references(table_info)
        for item in all_foreign_key_infos:
            if item:
                if item[0] not in new_table_list:
                    foreign_table_list[item[0]] = item[1]
        return foreign_table_list

    def flatten(self, lst):
        result = []
        for item in lst:
            if isinstance(item, list):
                result.extend(self.flatten(item))
            else:
                result.append(item)
        return result

    def filter_characters_for_complex(self, mode, features, table_list, table_info_list):
        target_table = []
        target_character = []
        if mode == "en":
            sql_code = features.get("sql", "")
            try:
                new_table_list_ = Parser(sql_code).tables
                all_sql_character_ = split_characters(Parser(sql_code).columns)
            except:
                all_sql_infos = self.get_characters_from_sql_for_complex(features.get("sql", "")).get("All field names",
                                                                                                      [])
                all_sql_character_ = split_characters(all_sql_infos)
                new_table_list_ = split_characters_table_name(all_sql_infos)

            # Obtained from disassembly
            entity_character_list = list(features.get("Element matching", {}).values())
            entity_character_list = self.flatten(entity_character_list)
            entity_character_list = [i for i in entity_character_list if (i != "" and i != 'n/a' and i != 'N/A')]
            for item in entity_character_list:
                item = item.split(",")
                target_character.extend(split_characters(item))

            for item in features["Required table information"]:
                if item["Table name"].lower() in get_lower_list(table_list):
                    target_table.append(item["Table name"].lower())
                all_sql_character = split_characters(features.get("All fields", []))
                # Table names are converted to lowercase for special processing. LLMs sometimes use lowercase table names.
                for table_name in new_table_list_:
                    if table_name.lower() in get_lower_list(table_list) and table_name.lower() not in target_table:
                        target_table.append(table_name.lower())

                target_character.extend(list(
                    set(split_characters(
                        item.get("All field names required by SQL under this table", [])) + self.id_characters +
                        self.time_characters)))
            target_character = list(set(target_character + all_sql_character + all_sql_character_))
            target_table = list(set(target_table))
            # Duplicate processing caused by case
            target_character = list(set([i.lower() for i in target_character]))
        else:
            assert 1 == 0
            print("Currently only supports en")

        return target_table, target_character

    def get_table_info_for_complex(self, mode, features, table_list, table_info_list, nums):
        """Field filtering and splitting logic: splicing and splitting field and tableinfo information
        to facilitate the integration of multiple solutions in the field/table part"""
        self.table_list, self.col_list = self.get_merge_infos(mode, features, table_list, table_info_list, nums)

        """Filter the required table information based on the filtered self.table_list and self.col_list"""
        fk_info = table_info_list[-1]
        target_character_list = []
        for table_name in self.table_list:
            # Field conversion to lowercase matching
            target_character_list.append(get_single_table_info(
                table_info_list, table_name.lower(), self.col_list, table_list))
        table_info = "\n\n".join(target_character_list)

        # Supplementary operations for foreign keys
        add_new_table_list = self.table_list
        foreign_table_list = self.get_table_characters_from_foreign_key(table_info, self.table_list)
        for key, value in foreign_table_list.items():
            if key.lower() not in add_new_table_list:
                add_new_table_list.append(key.lower())
                target_character_list.append(get_single_table_info(
                    table_info_list, key.lower(), value, table_list))
        add_table_info = "\n\n".join(target_character_list)

        add_table_info += "\n\n"
        add_table_info += fk_info.strip()
        return table_info, self.table_list, self.col_list, add_table_info, add_new_table_list

    def get_table_info_for_simple(self, features, table_list, table_info_list):
        target_table, target_character = self.filter_characters_for_simple(features)
        new_table_list = []
        target_character_list = []
        fk_info = table_info_list[-1]
        # Check table and field matching information
        for table in table_list:
            table_name = table
            if table_name.lower() in target_table:
                new_table_list.append(table)
                target_character_list.append(get_single_table_info(
                    table_info_list, table, target_character, table_list))
        table_info = "\n\n".join(target_character_list)

        add_new_table_list = new_table_list
        foreign_table_list = self.get_table_characters_from_foreign_key(table_info, new_table_list)
        for key, value in foreign_table_list.items():
            if key.lower() not in add_new_table_list:
                add_new_table_list.append(key.lower())
                target_character_list.append(get_single_table_info(
                    table_info_list, key.lower(), value, table_list))
        add_table_info = "\n\n".join(target_character_list)

        add_table_info += "\n\n"
        add_table_info += fk_info.strip()

        return table_info, new_table_list, target_character, add_table_info, add_new_table_list

    def filter_characters_for_simple(self, features):
        target_character = []
        target_table = []
        entity_character_list = list(features.values())
        entity_character_list = [i for i in entity_character_list if (i != "" and i != 'n/a' and i != 'N/A')]
        for item in entity_character_list:
            item = item.split(",")
            target_character.extend(split_characters(item))
            # Table names are converted to lowercase for special processing. LLMs sometimes use lowercase table names.
            target_table.extend(split_characters_table_name(item))
        target_character = list(set(target_character + self.id_characters + self.time_characters))
        target_table = list(set(target_table))

        return target_table, target_character

    def filter_characters_for_simple_v2(self, features, table_list, table_info_list):
        target_character_list = []
        new_table_list = []

        target_character = []
        entity_character_list = list(features.values())
        entity_character_list = [i for i in entity_character_list if (i != "" and i != 'n/a' and i != 'N/A')]
        for item in entity_character_list:
            item = item.split(",")
            target_character.extend(split_characters(item))
        target_character = list(set(target_character + self.id_characters + self.time_characters))
        target_table = self.return_table_if_has_characters(target_character, table_info_list, table_list)
        target_table = list(set(target_table))

        # Check table and field matching information
        for table in table_list:
            table_name = table
            if table_name.lower() in target_table:
                new_table_list.append(table)
                target_character_list.append(get_single_table_info(
                    table_info_list, table, target_character, table_list))
        table_info = "\n\n".join(target_character_list)
        return table_info, new_table_list, target_character, table_info, new_table_list

    def return_table_if_has_characters(self, target_character, table_info_list, table_list):
        target_table = []
        for table_info, table_name in zip(table_info_list, table_list):
            all_characters = get_lower_list(get_characters_in_table(table_info))
            for character in all_characters:
                if character in target_character:
                    target_table.append(table_name)
        return target_table
