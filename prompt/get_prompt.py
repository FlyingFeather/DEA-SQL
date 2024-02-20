# -*- coding: utf-8 -*-
# Project : DEASQL
# File    : get_prompt.py
# Author  : 
# Email   : 
# Time    : 2023/10/16 19:55
import sys

sys.path.append("..")

from common.enumeration.sql import DatasetType
from prompt.questions_label_prompt import QUESTION_LABEL_MULTI


def get_ner_prompt(dataset):
    spider_ner_prompt = """Assuming that you are a natural language processing expert and statistician, and a data analyst, please understand the business requirements and break down the requirements description into statistical elements. It is required to break down user problems into entities, and the main information in the original problem cannot be lost.

### Here are some examples:
What is the name of the staff that is in charge of the attraction named 'US museum'?
output: {{"entities": ["staff", "the attraction named 'US museum'"], "query": "the name of the staff that is in charge of the attraction named \"US museum\""}}

How many heads of the departments are older than 56 ?
output: {{"entities": ["age older than 56", "number of heads of the departments"], "query": "Number of department heads over 56 years old"}}

List the name, born state and age of the heads of departments ordered by age.
output: {{"entities": ["name of the heads of departments", "born state of the heads of departments", "age of the heads of departments", "age"], "query": "List the name, born state and age of the heads of departments ordered by age."}}

what is the average, minimum, and maximum age of all singers from Chinese?
output: {{"entities": ["Chinese", "age of all singers"], "query": "The average, minimum, and maximum age of all singers from Chinese"}}

Return the different descriptions of formulas that has been used in the textbook.
output: {{"entities": ["the different descriptions of formulas", "formulas", "used in the textbook"], "query": "The different descriptions of formulas that has been used in the textbook"}}

What are the details of the markets that can be accessed by walk or bus?
output: {{"entities": ["the details of the markets", "can be accessed by walk or busk"], "query": "The details of the markets that can be accessed by walk or bus"}}

Show the name of colleges that have at least two players.
output: {{"entities": ["the name of colleges", "players"], "query": "The name of colleges that have at least two players"}}

How many gold medals has the club with the most coaches won?
output: {{"entities": ["gold medals", "club", "coaches"], "query": "The number of gold medals has the club with the most coaches won"}}

List the nominees that have been nominated more than two musicals.
output: {{"entities": ["nominees", "nominees that have been nominated", "musicals"], "query": "The nominees that have been nominated more than two musicals"}}

### Please be sure to follow the following specifications:
1."entities" refers to all entities in the requirements,  including all description information in the requirements.
2.Your output must be output in json format, and only this json needs to be returned. It needs to include all fields in json. The json format is as follows: 
{{"entities":[entities], "query":"Rewritten question, removing unnecessary content"}}

{query}
output:
"""
    bird_ner_prompt = """Assuming that you are a natural language processing expert and statistician, and a data analyst, please understand the business requirements and break down the requirements description into statistical elements. It is required to break down user problems into entities, and the main information in the original problem cannot be lost.

### Here are some examples:
What is the name of the staff that is in charge of the attraction named 'US museum'?
output: {{"entities": ["staff", "the attraction named 'US museum'"], "query": "the name of the staff that is in charge of the attraction named \"US museum\""}}

How many heads of the departments are older than 56 ?
output: {{"entities": ["age older than 56", "number of heads of the departments"], "query": "Number of department heads over 56 years old"}}

List the name, born state and age of the heads of departments ordered by age.
output: {{"entities": ["name of the heads of departments", "born state of the heads of departments", "age of the heads of departments", "age"], "query": "List the name, born state and age of the heads of departments ordered by age."}}

what is the average, minimum, and maximum age of all singers from Chinese?
output: {{"entities": ["Chinese", "age of all singers"], "query": "The average, minimum, and maximum age of all singers from Chinese"}}

Return the different descriptions of formulas that has been used in the textbook.
output: {{"entities": ["the different descriptions of formulas", "formulas", "used in the textbook"], "query": "The different descriptions of formulas that has been used in the textbook"}}

What are the details of the markets that can be accessed by walk or bus?
output: {{"entities": ["the details of the markets", "can be accessed by walk or busk"], "query": "The details of the markets that can be accessed by walk or bus"}}

### Please be sure to follow the following specifications:
1."entities" refers to all entities in the requirements,  including all description information in the requirements.
2.Your output must be output in json format, and only this json needs to be returned. It needs to include all fields in json. The json format is as follows: 
{{"entities":[entities], "query":"Rewritten question, removing unnecessary content"}}

{query}
output:
"""
    if dataset == DatasetType.BIRD.value:
        ner_prompt = bird_ner_prompt
    else:
        ner_prompt = spider_ner_prompt
    return ner_prompt


def get_aggr_label_prompt(dataset):
    spider_prompt = """
    if need aggregation operations like COUNT, SUM, AVG, MAX, MIN: predict `NEED-AGGREGATION`, else predict `NONE`.
        "Q: {query}" \
        "A: "
    """

    bird_prompt = """"""

    if dataset == DatasetType.BIRD.value:
        prompt = bird_prompt
    else:
        prompt = spider_prompt

    return prompt


def add_aggr_prompt():
    prompt = """\n \
        ### note: You need to be careful to add some aggregation operations like COUNT, SUM, AVG, MAX, MIN when you write sql."""
    return prompt


def get_questions_label_prompt(dataset):
    spider_prompt = QUESTION_LABEL_MULTI
    # todo
    bird_prompt = QUESTION_LABEL_MULTI

    if dataset == DatasetType.BIRD.value:
        prompt = bird_prompt
    else:
        prompt = spider_prompt
    return prompt


def get_features_prompt_cn():
    prompt = ""
    return prompt


def get_features_prompt():
    suggestions_prompt = """{table_info}

User question: {query}
Entity information: {limitation}

### need
You are a data analyst. In business, you need to use the above table information to complete a SQL query code to solve user problems. I would like to ask you to first match the table fields or calculation methods required by the [{limitation}] entity, and then determine the calculation method of {main_metric}, and finally determine the required table and all related field information and give some key information for writing SQL.
Note that all table names must be their original names, and the output of field names must be the original field names in the table.

### Please be sure to comply with the following specifications
1. Element matching needs to output the most related table fields (one or more) or calculation methods and required field names required by the entities; yyy1 is the table field that needs to be selected to calculate the entity and the answer is in the form of ```colunm_name```. Note that an entity may require multiple fields;
2. bbb is the calculation method of {main_metric};
3. Required table information: Not all tables may need to be selected, depending on the specific problem.
3.1. Select the table and related fields based on the user questions, entity information and element matching information you have given above;
3.2. The where statement condition only gives the conditions of the corresponding table;
3.3. All field names required by SQL under the table must include the fields actually needed under the corresponding table. Note that you cannot select fields that are not under the previous table name, and do not select all fields. You must include all the fields that are needed for the table;
4. Multi-table joint fields and conditions need to find out the associated fields and conditions between multiple tables from the above table information;
5. "All fields" must to include all the fields actually used in sql !!! You must include all the fields that are needed for the table;
6. Think step by step, and finally summarize that your output is only in the given json format: {{"Element matching": {output_format}, "{main_metric} calculation method": "bbb", "Required table information": [{{"Table name": "xxx", "where statement condition": "ccc", "All field names required by SQL under this table": ["yyy1", "yyy2", "yyy3"]}}, {{"Table name": "xxx", "where statement condition": "ccc", "All field names required by SQL under this table": ["yyy1", "yyy2", "yyy3"]}}], "Multiple table joint fields and conditions": "ccc", "sql": "ddd", "All fields": ["yyy1", "yyy2", "yyy3"]}}"""
    return suggestions_prompt


def get_features_prompt_simple():
    suggestions_prompt = """{table_info}

Entity information: {limitation}

### need
You are a natural language processing expert and a data analyst. Please match the table fields that entities need to use in data analysis.
Please note that an entity requires at least one or more fields, and the fields should be as comprehensive as possible.

### Please be sure to comply with the following specifications:
1. The number of elements in json is {numbers}, which corresponds to {limitation}.
2. Note that all table names must be their original names, and the output of field names must be the original field names in the table.
3. Do not answer 'N/A' in yyy1, which is required to match one or more fields;
4. In json, yyy1 is the table field that needs to be selected to calculate the entity. The answer is in the form of ```table_name.colunm_name```!!!.
5. Please summarize your output to the given json format only: {output_format}"""

    return suggestions_prompt


def get_single_sql_prompt():
    suggestions_prompt = """{few_shots}### Database scheme: {table_info}

### Please think carefully about the related fields or calculation methods of '{main_metric}', then write valid SQLite to solve the following questions based on the above table information, and do not select extra columns that are not explicitly requested in the query.

### Query: {query}

### specification
1.In sql, just select columns that are explicitly requested in the query.
2.The output format must strictly meet the given json specification: {{"the most related fields or calculation methods of '{main_metric}'": "zzz", "sql": "ccc"}}
"""

    return suggestions_prompt


def get_multi_sql_prompt():
    sql_prompt = """{few_shots}### Database scheme: {table_info}

### Please think carefully about the related fields or calculation methods of '{main_metric}', then write valid SQLite to solve the following questions based on the above table information, and do not select extra columns that are not explicitly requested in the query.

### Query: {query}
### HINT: The question may needs connection operation like JOIN.

### specification
1."LIMIT" just is used when explicitly requesting how much to retrieve in the query.
2.In sql, just select columns that are explicitly requested in the query.
3.The output format must strictly meet the given json specification: {{"the most related fields or calculation methods of '{main_metric}'": "zzz", "sql": "ccc"}}
"""
    return sql_prompt


def get_join_nested_sql_prompt():
    sql_prompt = """{few_shots}### Database scheme: 
{table_info}

### Please think carefully about the related fields or calculation methods of '{main_metric}', then write valid SQLite to solve the following questions based on the above table information, and do not select extra columns that are not explicitly requested in the query.

### Query: {query}
### HINT: The question may needs nested queries like INTERSECT, UNION, EXCEPT, NOT IN.

### specification
1."LIMIT" just is used when explicitly requesting how much to retrieve in the query.
2.Don't use "IN", "OR", "LEFT JOIN" in sql because they aren't supported in execution engine, you can use "INTERSECT" or "EXCEPT" instead.
3.In sql, just select columns that are explicitly requested in the query.
4.The output format must strictly meet the given json specification: {{"the most related fields or calculation methods of '{main_metric}'": "zzz", "sql": "ccc"}}
"""
    return sql_prompt


def get_nested_sql_prompt():
    sql_prompt = """{few_shots}### Database scheme: 
{table_info}

### Please think carefully about the related fields or calculation methods of '{main_metric}', then write valid SQLite to solve the following questions based on the above table information, and do not select extra columns that are not explicitly requested in the query.

### Query: {query}
### HINT: The question may needs nested queries like INTERSECT, UNION, EXCEPT, NOT IN.

### specification
1."LIMIT" just is used when explicitly requesting how much to retrieve in the query.
2.Don't use "IN", "OR", "LEFT JOIN" in sql because they aren't supported in execution engine, you can use "INTERSECT" or "EXCEPT" instead.
3.In sql, just select columns that are explicitly requested in the query.
4.The output format must strictly meet the given json specification: {{"the most related fields or calculation methods of '{main_metric}'": "zzz", "sql": "ccc"}}
"""
    return sql_prompt


def get_characters_from_sql_prompt():
    prompt = """{sql}

Please help me return all table names and field names involved in the above SQL, including all tables and fields involved in SELECT clauses, WHERE statements, aggregate statements, etc.
Your answer must be only the given json: {{"All field names": [yyy1, yyy2, yyy3]}}, and yyy must be in the form of `table_name.field_name`!!!.
"""

    return prompt
