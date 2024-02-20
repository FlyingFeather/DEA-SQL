# -*- coding: utf-8 -*-
# Project : DEASQL 
# File    : correct_sql.py
# Author  : 
# Email   : 
# Time    : 2023/12/22 19:59
from common.common import get_prompt_content
from llm.chat import ask_llm


def correct_sql_self(query, table_info, sql):
    sql_prompt = "For the given question, use the Database scheme to fix the given SQLite QUERY for any issuses.\n" \
                 "If there are any problems, please fix them.\n" \
                 "If there are no issues, return SQLite QUERY as is.\n" \
                 "### There are some instructions for fixing the SQL query:\n" \
                 "1) In sql, just select columns that are explicitly requested in the query.\n" \
                 "2) Pay attention to the columns that are used for the SELECT clause. " \
                 "Fix possible ambiguous columns if there are the same columns in different table in the SELECT clause.\n" \
                 "3) Pay attention to the correspondence between tables and fields. " \
                 "Cannot use fields that are not in the table.\n" \
                 "4) Pay attention to the columns that are used for the JOIN." \
                 "The join table condition must be in the Foreign_keys.\n" \
                 "5) Pay attention to the use of the JOIN." \
                 "Don't use LEFT JOIN unless necessary.\n" \
                 "6) Only change the SELECT, GROUP BY and ORDER BY clause when necessary.\n" \
                 "7) " \
                 f"Database scheme: {table_info}\n" \
                 f"### Question: {query}\n" \
                 f"### SQLite SQL QUERY:\n" \
                 f"{sql}\n" \
                 f"### Fixed SQL QUERY:" \
                 f"SELECT\n"
    prompt_dict = {
        "query": query,
        "table_info": table_info,
        "sql": sql
    }
    sql_prompt = get_prompt_content(sql_prompt, prompt_dict)
    sql = ask_llm(sql_prompt)
    return sql


def correct_sql_by_case(query, table_info, sql):
    sql_prompt = "Please determine the type of question. If it is an extremum problem, modify the SQL accordingly. " \
                 "If not, use the original SQL as the modified SQL." \
                 "Q1: What is the name of the instructor who advises the student with the greatest number " \
                 "of total credits?\n" \
                 "original SQL: SELECT T2.name FROM instructor T2 JOIN advisor T1 ON T2.id = T1.i_id JOIN " \
                 "student s ON T1.s_id = T3.id WHERE T3.tot_cred = (SELECT MAX(tot_cred) FROM student)\n" \
                 "A: The question is an extremum problem, so i should modify the SQL. " \
                 "The modified SQL: SELECT T2.name FROM advisor AS T1 JOIN instructor AS T2 ON T1.i_id = T2.id JOIN " \
                 "student AS T3 ON T1.s_id = T3.id ORDER BY T3.tot_cred DESC LIMIT 1\n\n" \
                 "Q2: Return the id and full name of the customer who has the fewest accounts.\n" \
                 "original SQL: SELECT c.customer_id, c.customer_first_name, c.customer_last_name FROM CUSTOMERS c JOIN ACCOUNTS " \
                 "a ON c.customer_id = a.customer_id GROUP BY c.customer_id HAVING COUNT(a.account_id) = (SELECT " \
                 "COUNT(account_id) FROM ACCOUNTS GROUP BY customer_id ORDER BY COUNT(account_id) ASC LIMIT 1)\n" \
                 "A: The question is an extremum problem, so i should modify the SQL. " \
                 "The modified SQL: SELECT T1.customer_id, T2.customer_first_name, T2.customer_last_name FROM " \
                 "Customers_cards AS T1 JOIN Customers AS T2 ON T1.customer_id = T2.customer_id GROUP BY " \
                 "T1.customer_id ORDER BY count(*) ASC LIMIT 1\n\n" \
                 "Q3: What is the average hours across all projects?\n" \
                 "original SQL: SELECT avg(hours) FROM projects" \
                 "A: The question is not an extremum problem, so i should use the original SQL as the modified SQL." \
                 "The modified SQL: SELECT avg(hours) FROM projects\n\n" \
                 "Q4: {query}\n" \
                 "{table_info}\n\n" \
                 "original SQL: {sql}" \
                 "A: "
    prompt_dict = {
        "query": query,
        "table_info": table_info,
        "sql": sql
    }
    sql_prompt = get_prompt_content(sql_prompt, prompt_dict)
    sql_result = ask_llm(sql_prompt)
    return sql_result
