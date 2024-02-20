# -*- coding: utf-8 -*-
# Project : DEASQL 
# File    : get_sql_prompt_for_fewshot.py
# Author  : 
# Email   : 
# Time    : 2023/12/29 10:48


class SQLPromptError:
    def __init__(self):
        self.error_case = "Here are the questions you didn’t get right sql:\n" \
                          "Q: What is first names of the top 5 staff who have handled the greatest " \
                          "number of complaints?\n" \
                          "sql: SELECT t1.first_name FROM staff AS t1 JOIN complaints AS t2 ON t1.staff_id = "\
                          "t2.staff_id GROUP BY t2.staff_id ORDER BY count(*) LIMIT 5\n\n" \
                          "Q: What are the first name and major of the students who are able to consume soy?\n" \
                          "sql: SELECT fname, major FROM Student WHERE StuID NOT IN (SELECT StuID FROM " \
                          "Has_allergy WHERE Allergy = 'Soy')\n\n" \
                          "Q: What is the name of the instructor who advises the student with the  greatest number " \
                          "of total credits?\n" \
                          ": SELECT T2.name FROM advisor AS T1 JOIN instructor AS T2 ON T1.i_id = T2.id JOIN student " \
                          "AS T3 ON T1.s_id = T3.id ORDER BY T3.tot_cred DESC LIMIT 1\n\n" \
                          "Q: How many countries do not have an roller coaster longer than 3000?\n" \
                          "SELECT LastName FROM CUSTOMER EXCEPT SELECT T1.LastName FROM CUSTOMER AS T1 JOIN " \
                          "Invoice AS T2 ON T1.CustomerId = T2.CustomerId WHERE T2.total > 20\n\n"

    def get_multi_sql_prompt(self):
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

    def get_join_nested_sql_prompt(self):
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

    def get_nested_sql_prompt(self):
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

    def get_single_sql_prompt(self):
        sql_prompt = """{few_shots}### Database scheme: {table_info}

### Please think carefully about the related fields or calculation methods of '{main_metric}', then write valid SQLite to solve the following questions based on the above table information, and do not select extra columns that are not explicitly requested in the query.

### Query: {query}

### specification
1.In sql, just select columns that are explicitly requested in the query.
2.The output format must strictly meet the given json specification: {{"the most related fields or calculation methods of '{main_metric}'": "zzz", "sql": "ccc"}}
"""
        return sql_prompt


class SQLPromptFewshot:
    def get_multi_sql_prompt(self):
        sql_prompt = """{few_shots}### Database scheme: {table_info}

### Please think carefully about the related fields or calculation methods of '{main_metric}', then write valid SQLite to solve the following questions based on the above table information, and do not select extra columns that are not explicitly requested in the query.

### Query: {query}
### HINT: The question may needs connection operation like JOIN.

### specification
1."LIMIT" just is used when explicitly requesting how much to retrieve in the query.
2.In sql, just select columns that are explicitly requested in the query.
3.The output format must strictly meet the given json specification: {{"sql": "ccc"}}
"""
        return sql_prompt


    def get_join_nested_sql_prompt(self):
        sql_prompt = """{few_shots}### Database scheme: 
{table_info}

### Please think carefully about the related fields or calculation methods of '{main_metric}', then write valid SQLite to solve the following questions based on the above table information, and do not select extra columns that are not explicitly requested in the query.

### Query: {query}
### HINT: The question may needs nested queries like INTERSECT, UNION, EXCEPT, NOT IN.

### specification
1."LIMIT" just is used when explicitly requesting how much to retrieve in the query.
2.Don't use "IN", "OR", "LEFT JOIN" in sql because they aren't supported in execution engine, you can use "INTERSECT" or "EXCEPT" instead.
3.In sql, just select columns that are explicitly requested in the query.
4.The output format must strictly meet the given json specification: {{"sql": "ccc"}}
"""
        return sql_prompt

    def get_nested_sql_prompt(self):
        sql_prompt = """{few_shots}### Database scheme: 
{table_info}

### Please think carefully about the related fields or calculation methods of '{main_metric}', then write valid SQLite to solve the following questions based on the above table information, and do not select extra columns that are not explicitly requested in the query.

### Query: {query}
### HINT: The question may needs nested queries like INTERSECT, UNION, EXCEPT, NOT IN.

### specification
1."LIMIT" just is used when explicitly requesting how much to retrieve in the query.
2.Don't use "IN", "OR", "LEFT JOIN" in sql because they aren't supported in execution engine, you can use "INTERSECT" or "EXCEPT" instead.
3.In sql, just select columns that are explicitly requested in the query.
4.The output format must strictly meet the given json specification: {{"sql": "ccc"}}
"""
        return sql_prompt

    def get_single_sql_prompt(self):
        sql_prompt = """{few_shots}### Database scheme: {table_info}

### Please think carefully about the related fields or calculation methods of '{main_metric}', then write valid SQLite to solve the following questions based on the above table information, and do not select extra columns that are not explicitly requested in the query.

### Query: {query}

### specification
1.In sql, just select columns that are explicitly requested in the query.
2.The output format must strictly meet the given json specification: {{"sql": "ccc"}}
"""
        return sql_prompt

    def get_reduce_ql_sql_prompt(self):
        sql_prompt = """{few_shots}### Database scheme: 
{table_info}

### Please think carefully about the related fields or calculation methods of '{main_metric}', then write valid SQLite to solve the following questions based on the above table information, and do not select extra columns that are not explicitly requested in the query.

### Query: {query}

### specification
1."LIMIT" just is used when explicitly requesting how much to retrieve in the query.
2.Don't use "IN", "OR", "LEFT JOIN" in sql because they aren't supported in execution engine, you can use "INTERSECT" or "EXCEPT" instead.
3.In sql, just select columns that are explicitly requested in the query.
4.The output format must strictly meet the given json specification: {{"sql": "ccc"}}"""
        return sql_prompt
