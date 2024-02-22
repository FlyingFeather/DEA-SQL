# -*- coding: utf-8 -*-
# Project : DEASQL
# File    : gen_sql.py
# Author  : 
# Email   : 
# Time    : 2023/10/16 15:11
import json
import os
from concurrent.futures import ThreadPoolExecutor

from common.common import (
    get_prompt_content,
    extract_label,
    get_dict_from_str,
    extract_sql
)
from common.enumeration.sql import (
    SqlType,
    FilterType,
    QuestionType,
    AggrType,
    AggregationType
)
from common.wrapper import self_consistency
from correct_sql import correct_sql_self, correct_sql_by_case
from fewshot.auto_selection import get_fewshots
from filter_characters import FilterCharacters
from get_ner import NER
from llm.chat import ask_llm
from logger import get_logger
from prompt.get_prompt import (
    get_single_sql_prompt,
    get_multi_sql_prompt,
    get_nested_sql_prompt,
    get_join_nested_sql_prompt,
    get_features_prompt,
    get_features_prompt_cn,
    get_features_prompt_simple,
    get_questions_label_prompt,
    add_aggr_prompt
)
from prompt.get_sql_prompt_for_fewshot import SQLPromptError
from prompt.get_sql_prompt_for_fewshot import SQLPromptFewshot

special_for_bird = False
from argsparser import parser

args = parser.parse_args()


def generate_dictionary(entities):
    dictionary = {}
    for i, entity in enumerate(entities):
        key = f"Table and field required by {entity}"
        value = "yyy" + str(i + 1)
        dictionary[key] = value
    return dictionary


def generate_dictionary_for_complex(entities):
    dictionary = {}
    for i, entity in enumerate(entities):
        key = f"the most related fields of {entity}"
        value = "yyy" + str(i + 1)
        dictionary[key] = value
    return dictionary


class Text2SQL:
    def __init__(self, logger_name, filter_mode="complex", prompt_mode="v2", n_shots=2,
                 few_shot_mode="masked_ques_sim"):
        self.model = 'gpt-3.5-turbo'
        self.ner = NER()
        self.filter_characters = FilterCharacters()
        self.sql_type = SqlType.SINGLE_TABLE.value
        self.table_character_dict = {}
        self.filter_characters_mode = args.filter_mode
        self.logger = get_logger(logger_name)
        self.question_type = QuestionType.EASY.value
        self.aggregation_type = AggregationType.NON.value
        self.dataset = ""
        self.n_shots = args.n_shots
        self.few_shot_mode = args.few_shot_mode
        self.sql_prompt_fewshot = SQLPromptFewshot()
        self.sql_prompt_error = SQLPromptError()

    def get_features_by_llm(self, query, table_info, limitation, metric, main_metric, mode="en"):
        numbers = len(limitation.split(","))
        entities = limitation.split(",")
        if self.filter_characters_mode == FilterType.COMPLEX.value:
            features_prompt = (get_features_prompt() if mode == 'en' else get_features_prompt_cn())
            output_format = json.dumps(generate_dictionary_for_complex(entities))
            prompt_dict = {
                "query": query,
                "table_info": table_info,
                "limitation": limitation,
                # "metric": metric,
                "main_metric": main_metric,
                "numbers": numbers,
                "output_format": output_format
            }
        else:
            features_prompt = get_features_prompt_simple()
            output_format = json.dumps(generate_dictionary(entities))
            prompt_dict = {
                "table_info": table_info,
                # "metric": metric,
                "limitation": limitation,
                "numbers": numbers,
                "output_format": output_format
            }
        features_prompt = get_prompt_content(features_prompt, prompt_dict)
        features = ask_llm(features_prompt, args.sc_filter_temp)
        try:
            features = get_dict_from_str(features)
        except Exception as e:
            print(f"==============={features}")
            print(f"==============={e.args}")
            features = ""
        return features

    @self_consistency(args.sc_nums_question_label, ["question_type"], "all")
    def get_question_type(self, query, table_info):
        sql_prompt = get_questions_label_prompt(self.dataset)
        prompt_dict = {
            "query": query,
            "table_info": table_info,
        }
        sql_prompt = get_prompt_content(sql_prompt, prompt_dict)
        question_content = ask_llm(sql_prompt, args.sc_ques_temp)
        print(f"-------question：{question_content}----------")
        results = {}
        results["question_type"], self.aggregation_type = extract_label(question_content)
        if results["question_type"] not in ["EASY", "NESTED", "JOIN", "JOIN-NESTED"]:
            print(f"-------Need to pay attention to the problem type error 2：{results['question_type']}----------")
            results["question_type"] = QuestionType.EASY.value
        return results

    def get_generate_sql_prompt(self):
        if self.few_shot_mode in ["random", "ques_sim", "masked_ques_sim", "query_sim"] and args.reduce_ql:
            return self.sql_prompt_fewshot.get_reduce_ql_sql_prompt()
        if self.few_shot_mode in ["random", "ques_sim", "masked_ques_sim", "query_sim"] and not args.has_error_case:
            if self.question_type == QuestionType.EASY.value:
                sql_prompt = self.sql_prompt_fewshot.get_single_sql_prompt()
            elif self.question_type == QuestionType.NESTED.value:
                sql_prompt = self.sql_prompt_fewshot.get_nested_sql_prompt()
            elif self.question_type == QuestionType.JOIN_NESTED.value:
                sql_prompt = self.sql_prompt_fewshot.get_join_nested_sql_prompt()
            else:
                sql_prompt = self.sql_prompt_fewshot.get_multi_sql_prompt()
            return sql_prompt

        if args.has_error_case:
            if self.question_type == QuestionType.EASY.value:
                sql_prompt = self.sql_prompt_error.get_single_sql_prompt()

            elif self.question_type == QuestionType.NESTED.value:
                sql_prompt = self.sql_prompt_error.get_nested_sql_prompt()
            elif self.question_type == QuestionType.JOIN_NESTED.value:
                sql_prompt = self.sql_prompt_error.get_join_nested_sql_prompt()
            else:
                sql_prompt = self.sql_prompt_error.get_multi_sql_prompt()
            return sql_prompt

        if self.question_type == QuestionType.EASY.value:
            sql_prompt = get_single_sql_prompt()
        elif self.question_type == QuestionType.NESTED.value:
            sql_prompt = get_nested_sql_prompt()
        elif self.question_type == QuestionType.JOIN_NESTED.value:
            sql_prompt = get_join_nested_sql_prompt()
        else:
            sql_prompt = get_multi_sql_prompt()
        return sql_prompt

    @self_consistency(args.sc_nums, ["sql"], "each")
    def get_sql_by_llm(self, query, table_info, limitation, metric, main_metric, suggestion, few_shots,
                       aggr_type=AggrType.NON_NEEDED):

        sql_prompt = self.get_generate_sql_prompt()
        aggr_prompt = add_aggr_prompt()

        if aggr_type == AggrType.NEEDED:
            sql_prompt += aggr_prompt
        prompt_dict = {
            "query": query,
            "table_info": table_info,
            "limitation": limitation,
            "metric": metric,
            "suggestion": suggestion,
            "main_metric": main_metric,
            "few_shots": few_shots
        }
        sql_prompt = get_prompt_content(sql_prompt, prompt_dict)
        sql = ask_llm(sql_prompt, args.sc_sql_temp)
        try:
            sql = get_dict_from_str(sql)
            print(sql)
        except Exception as e:
            sql = ask_llm(sql_prompt, args.sc_sql_temp)
            print(sql)
            print(f"==============={e.args}")
            sql = {"sql": "error"}
        return sql

    def filter_characters_main(self, features, table_list, table_info_list, mode="cn"):
        table_list = [i.lower() for i in table_list]
        if self.filter_characters_mode == FilterType.COMPLEX.value:
            table_info, new_table_list, target_character, add_table_info, add_new_table_list = \
                self.filter_characters.get_table_info_for_complex(mode, features, table_list,
                                                                  table_info_list, args.sc_filter_nums)
        elif self.filter_characters_mode == FilterType.SIMPLE.value:
            table_info, new_table_list, target_character, add_table_info, add_new_table_list = \
                self.filter_characters.get_table_info_for_simple(features, table_list, table_info_list)
        else:
            table_info, new_table_list, target_character, add_table_info, add_new_table_list = \
                self.filter_characters.filter_characters_for_simple_v2(features, table_list, table_info_list)
        return table_info, new_table_list, target_character, add_table_info, add_new_table_list

    def save_to_file(self, json_data, file_name):
        with open(file_name, "a+", encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False)
            f.write("\n")

    def step_get_ner_results(self, input_dict, mode):
        """step 1： get ner"""
        input_dict["ner_results"] = self.ner.run(input_dict["query"], self.dataset)
        if mode == "debug":
            print(input_dict["init_table_infos"])
            print(input_dict["query"])
        if mode == "debug":
            print("---------------step 1: ner_results are---------------------")
            print(input_dict["ner_results"])
        return input_dict

    def get_features_by_llm_concurrent(self, query, init_table_infos, limitation, metric, main_metric, lang_mode):
        results = []
        with ThreadPoolExecutor() as executor:
            futures = []
            for _ in range(args.sc_filter_nums):
                future = executor.submit(self.get_features_by_llm, query, init_table_infos, limitation, metric,
                                         main_metric, lang_mode)
                futures.append(future)
            for future in futures:
                if future.result() != "":
                    results.append(future.result())
        return results

    def step_get_filter_infos(self, input_dict, lang_mode, table_list, table_info_list, mode):
        """step 2： get filter infos"""
        limitation = ",".join(input_dict["ner_results"]["limitation"])
        metric = ",".join(input_dict["ner_results"]["metric"])
        main_metric = input_dict["ner_results"]["query"]

        query = input_dict["query"]
        init_table_infos = input_dict["init_table_infos"]
        cur_idx = input_dict["cur_idx"]
        origin_idx = input_dict["origin_idx"]
        stop_flag = False

        input_dict["features"] = self.get_features_by_llm_concurrent(
            query, init_table_infos, limitation, metric, main_metric, lang_mode)

        if not input_dict["features"]:
            self.filter_characters_mode = FilterType.SIMPLE.value
            input_dict["features"] = self.get_features_by_llm(
                query, init_table_infos, limitation, metric, main_metric, lang_mode)

        if input_dict["features"] == "":
            self.logger.info(f"cur_idx:{cur_idx}, origin_idx:{origin_idx} error, stop at step 2, query is {query}")
            stop_flag = True

        if mode == "debug":
            print("---------------step2-1：features are---------------------")
            print(input_dict.get("features", ""))

        ############### step 3 #################
        if not stop_flag:
            input_dict["table_info"], input_dict["target_table"], input_dict["target_characters"], input_dict[
                "add_table_info"], new_table_list = \
                self.filter_characters_main(input_dict["features"], table_list, table_info_list, lang_mode)
            self.filter_characters_mode = FilterType.COMPLEX.value

        if input_dict.get("table_info", "") == "":
            self.logger.info(f"cur_idx:{cur_idx}, origin_idx:{origin_idx} error, stop at step 3, query is {query}")
            input_dict["table_info"] = input_dict["init_table_infos"]

        if mode == "debug":
            print("--------------step2-2：The simplified and reorganized tables and fields are--------------")
            print(f"add_table_info： {input_dict.get('add_table_info', '')}")

        return input_dict

    def step_question_classification(self, input_dict, mode):
        query = input_dict["query"]
        sc_results = self.get_question_type(query, input_dict["table_info"])
        self.question_type = sc_results[0]["question_type"]
        input_dict["question_type"] = self.question_type

        # The effect is not good and I haven’t used it yet.
        input_dict["new_aggr_type"] = self.aggregation_type

        if mode == "debug":
            print("---------------The question type is identified as---------------------")
            print(sc_results)
            print(self.question_type)

        return input_dict

    def step_get_fewshots(self, input_dict, pre_sql, mode):
        query = input_dict["query"]
        limitation = ",".join(input_dict["ner_results"]["limitation"])
        if args.has_error_case:
            input_dict["few_shots"] = self.sql_prompt_error.error_case
            return input_dict

        embedding_base_model = args.embedding_base_model
        if self.few_shot_mode in ["random", "ques_sim", "masked_ques_sim", "query_sim"]:
            if not args.reduce_ql:
                few_shots_dict = get_fewshots(
                    question=query,
                    entities=limitation,
                    sql=pre_sql,
                    question_type=list(set([self.question_type])),
                    mode=self.few_shot_mode,
                    n_shots=self.n_shots,
                    model=embedding_base_model,
                    index_version=args.few_shot_data,
                    ques_type_mode='all'
                )
            else:
                few_shots_dict = get_fewshots(
                    question=query,
                    entities=limitation,
                    sql=pre_sql,
                    question_type=[QuestionType.EASY.value, QuestionType.NESTED.value,
                                   QuestionType.JOIN.value, QuestionType.JOIN_NESTED.value],
                    mode=self.few_shot_mode,
                    n_shots=self.n_shots,
                    model=embedding_base_model,
                    index_version=args.few_shot_data,
                    ques_type_mode='all'
                )
            few_shots = "Some example questions and corresponding SQL queries are provided based on similar problems:\n"
            # few_shots_dict.reverse()
            for item_ in few_shots_dict:
                few_shots += f'{item_["query"]}\n'
                temp_sql = {"sql": item_["gold_sql"]}
                few_shots += f'{json.dumps(temp_sql, ensure_ascii=False)}\n\n'

        else:
            few_shots = ""
        input_dict["few_shots"] = few_shots

        if mode == "debug":
            print("---------------get fewshots---------------------")
            print(few_shots)

        return input_dict

    def step_get_pre_sql(self, input_dict, mode):
        """Generate SQL for fewshot=query_sim to use"""
        limitation = ",".join(input_dict["ner_results"]["limitation"])
        metric = ",".join(input_dict["ner_results"]["metric"])
        main_metric = input_dict["ner_results"]["query"]
        few_shots = ""
        query = input_dict["query"]
        if self.question_type == QuestionType.EASY.value:
            table_info_sql = input_dict["table_info"]
        else:
            table_info_sql = input_dict["add_table_info"]

        input_dict["suggestions"] = ""
        sc_results = self.get_sql_by_llm(query, table_info_sql, limitation, metric,
                                         main_metric, input_dict["suggestions"], few_shots)
        input_dict["pre_sql_results"] = sc_results[0]

        if input_dict["pre_sql_results"].get("sql", "") != "":
            pre_sql = input_dict["pre_sql_results"]["sql"]
        elif list(input_dict["pre_sql_results"].values()):
            pre_sql = list(input_dict["pre_sql_results"].values())[0]
        elif input_dict["features"].get("sql", "") != "":
            pre_sql = input_dict["features"]["sql"]
        else:
            pre_sql = "error"

        input_dict["pre_sql_results"]["sql"] = pre_sql
        return input_dict

    def step_get_sql(self, input_dict, mode):
        limitation = ",".join(input_dict["ner_results"]["limitation"])
        metric = ",".join(input_dict["ner_results"]["metric"])
        main_metric = input_dict["ner_results"]["query"]
        few_shots = input_dict["few_shots"]
        query = input_dict["query"]

        if self.question_type == QuestionType.EASY.value:
            table_info_sql = input_dict["table_info"]
        else:
            table_info_sql = input_dict["add_table_info"]
        # Pre-prompt is empty
        input_dict["suggestions"] = ""
        sc_results = self.get_sql_by_llm(query, table_info_sql, limitation, metric,
                                         main_metric, input_dict["suggestions"], few_shots)
        input_dict["init_sql_results"] = sc_results[0]
        input_dict["sql_results"] = {}

        # self-check
        if input_dict["init_sql_results"].get("sql", "") != "":
            init_sql = input_dict["init_sql_results"]["sql"]
        elif list(input_dict["init_sql_results"].values()):
            init_sql = list(input_dict["init_sql_results"].values())[0]
        elif input_dict["features"].get("sql", "") != "":
            init_sql = input_dict["features"]["sql"]
        else:
            init_sql = "error"
        input_dict["init_sql_results"]["sql"] = init_sql
        try:
            correct_sql = correct_sql_self(query, table_info_sql, init_sql)
        except:
            init_sql = "error"
            correct_sql = correct_sql_self(query, table_info_sql, init_sql)
        if "error" not in correct_sql:
            input_dict["sql_results"]["sql"] = f"SELECT {correct_sql}"

        if mode == "debug":
            print("---------------The result of sc is---------------------")
            print(sc_results)
            print("---------------The result of correct-sql is---------------------")
            print(input_dict["sql_results"])

        try:
            final_sql = input_dict["init_sql_results"]["sql"]
        except Exception as e:
            print(f"1、Generated sql_results json parsing error：{e.__str__()}")
            final_sql = "error"

        try:
            if "CAST" in correct_sql:  # trick
                final_correct_sql = final_sql
            else:
                final_correct_sql = input_dict["sql_results"]["sql"]
        except Exception as e:
            print(f"2、Generated sql_results json parsing error：{e.__str__()}")
            final_correct_sql = final_sql

        input_dict["sql_results"]["sql"] = final_correct_sql

        return input_dict

    def step_activate_learning(self, input_dict, mode):
        query = input_dict["query"]
        if self.question_type == QuestionType.EASY.value:
            table_info = input_dict["table_info"]
        else:
            table_info = input_dict["add_table_info"]
        init_sql = input_dict["sql_results"]["sql"]
        try:
            correct_sql_by_case_result = correct_sql_by_case(query, table_info, init_sql)
            correct_sql = extract_sql(correct_sql_by_case_result, init_sql)
        except Exception as e:
            init_sql = "error"
            correct_sql_by_case_result = correct_sql_by_case(query, table_info, init_sql)
            correct_sql = extract_sql(correct_sql_by_case_result, init_sql)
            print(e.__str__())
        if "error" not in correct_sql and "CAST" not in correct_sql:
            sql = f"{correct_sql}"
        else:
            print(correct_sql)
            sql = input_dict["init_sql_results"].get("sql", "error")
        input_dict["act_sql_results"] = {"sql": sql, "correct_sql_by_case_result": correct_sql_by_case_result}
        if mode == "debug":
            print("-------error case--------")
            print(input_dict["act_sql_results"])
        return input_dict

    def save_sql_txt(self, save_file_name, suffix_name, sql, dataset, db_id):
        filename, ext = os.path.splitext(save_file_name)
        filename = filename + suffix_name
        new_path = filename + ext
        new_path = os.path.join("outputs", dataset, new_path)

        with open(new_path, "a+") as f:
            if dataset == "spider":
                f.write(sql.replace("\n", " "))
                f.write("\n")
            elif dataset == "bird":
                f.write((sql.replace("\n", " ") + '\t----- bird -----\t' + db_id))
                f.write("\n")

    def save_file(self, save_file_name, dataset, final_sql, final_correct_sql, final_des_sql, mode, item, db_id):
        filename, ext = os.path.splitext(save_file_name)
        filename = filename + '_clean'
        new_path = filename + ext
        new_path = os.path.join("outputs", dataset, new_path)

        filename_2 = filename + '_correct'
        new_path_2 = filename_2 + ext
        new_path_2 = os.path.join("outputs", dataset, new_path_2)
        with open(new_path, "a+") as f:
            if dataset == "spider":
                f.write(final_sql.replace("\n", " "))
                f.write("\n")
            elif dataset == "bird":
                f.write((final_sql.replace("\n", " ") + '\t----- bird -----\t' + db_id))
                f.write("\n")

        with open(new_path_2, "a+", encoding='utf-8') as f:
            if dataset == "spider":
                f.write(final_correct_sql.replace("\n", " "))
                f.write("\n")

        suffix_name = "_des"
        self.save_sql_txt(save_file_name, suffix_name, final_des_sql, dataset, db_id)

        ############# single evaluate #################
        # only evaluting exact match needs this argument
        if mode == "debug":
            from single_eval import build_foreign_key_map_from_json, evaluate
            kmaps = None
            if args.etype in ['all', 'match']:
                assert args.table is not None, 'table argument must be non-None if exact set match is evaluated'
                kmaps = build_foreign_key_map_from_json(args.table)

            gold_sql = item['query'] + '\t' + item['db_id']
            pred_sql = final_sql.replace("\n", " ")
            final_correct_sql = final_correct_sql.replace("\n", " ")
            print(f"gold_sql: {item['query']}")
            print(f"pred_sql: {pred_sql}")
            evaluate(gold_sql, pred_sql, args.db, args.etype, kmaps, args.plug_value, args.keep_distinct,
                     args.progress_bar_for_each_datapoint)
            print(f"final_correct_sql: {final_correct_sql}")
            evaluate(gold_sql, final_correct_sql, args.db, args.etype, kmaps, args.plug_value, args.keep_distinct,
                     args.progress_bar_for_each_datapoint)

            print(f"final_des_sql: {final_des_sql}")
            evaluate(gold_sql, final_des_sql, args.db, args.etype, kmaps, args.plug_value, args.keep_distinct,
                     args.progress_bar_for_each_datapoint)

    def main(self, root_dir, dataset, file, save_file_name, mode="dev", lang_mode="cn", prompt_mode='openai',
             sample="True", data_fold="1", test_id=46, insert_value=0, step_name="all"):
        assert mode in ["debug", "dev"]
        assert dataset in ["spider", "bird"]
        assert lang_mode in ["cn", "en"]
        assert prompt_mode in ["create", "openai"]
        from data_preprocess import generate_db_prompt_spider, generate_db_prompt_bird
        import os
        from tqdm import tqdm
        self.dataset = dataset
        if dataset == "bird":
            dataset = "dev"
            global special_for_bird
            special_for_bird = True
        with open(os.path.join(root_dir, dataset, file)) as f:
            data = json.load(f)
            idx = list(range(len(data)))
        if dataset == "dev":
            dataset = "bird"
        if mode == "debug":
            data = [data[test_id]]

        """Start using after test failure"""
        if args.re_run:
            data = data[args.re_run_idx:]
            idx = idx[args.re_run_idx:]

        new_data = list(zip(idx, data))
        for cur_idx, items in enumerate(tqdm(new_data)):
            if args.re_run:
                cur_idx += args.re_run_idx
            origin_idx, item = items
            db_id, query = item['db_id'], item['question']
            hint, question_id = None, None
            if dataset == "spider":
                init_table_infos, table_list = generate_db_prompt_spider(
                    root_dir='data', dataset='spider', db_id=db_id, prompt_db=args.schema_mode,
                    normalization=args.fk_mode, limit_value=insert_value)
                table_info_list = init_table_infos.split("\n\n")
                table_info_list = [i for i in table_info_list if i.strip() != ""]
            elif dataset == "bird":
                init_table_infos, table_list = generate_db_prompt_bird(
                    root_dir='data', dataset='dev', db_id=db_id, limit_value=0)
                table_info_list = init_table_infos.split("\n\n\n")
                table_info_list = [i.strip() for i in table_info_list if i.strip() != ""]
                hint = str(item["evidence"])

            input_dict = {}
            input_dict["table_list"] = table_list
            input_dict["table_info_list"] = table_info_list
            # Easy to debug
            input_dict['cur_idx'] = str(cur_idx)
            input_dict['origin_idx'] = str(origin_idx)

            if hint is not None:
                input_dict["hint"] = hint
            input_dict["query"] = query
            input_dict["init_table_infos"] = init_table_infos

            # 1、Feature extraction
            input_dict = self.step_get_ner_results(input_dict, mode)
            # 2、Information filtering
            if self.filter_characters_mode == FilterType.NONE.value:
                input_dict["table_info"] = init_table_infos
                input_dict["add_table_info"] = init_table_infos
            else:
                input_dict = self.step_get_filter_infos(input_dict, lang_mode, table_list, table_info_list, mode)

            if not args.reduce_ql:
                # 3、question_classification
                input_dict = self.step_question_classification(input_dict, mode)
            else:
                # After removal, use a specific prompt and change all problems to take effect in the fewshot module.
                input_dict["question_type"] = QuestionType.JOIN.value

            # 4、get_fewshots
            if self.few_shot_mode == "query_sim":
                input_dict = self.step_get_pre_sql(input_dict, mode)
                pre_sql = input_dict["pre_sql_results"]["sql"]
            else:
                pre_sql = ""
            input_dict = self.step_get_fewshots(input_dict, pre_sql, mode)
            # 5、get_sql
            input_dict = self.step_get_sql(input_dict, mode)

            # 6、activate_learning
            input_dict = self.step_activate_learning(input_dict, mode)

            os.makedirs(f"outputs/{dataset}", exist_ok=True)

            self.save_to_file(input_dict, os.path.join("outputs", dataset, save_file_name))

            self.save_file(save_file_name, dataset, input_dict["init_sql_results"]["sql"],
                           input_dict["sql_results"]["sql"], input_dict["act_sql_results"]["sql"], mode, item, db_id)
