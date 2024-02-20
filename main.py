# -*- coding: utf-8 -*-
# Project : DEASQL
# File    : main.py
# Author  :
# Email   :
# Time    : 2023/10/18 17:44
import sys

sys.path.append(".")
from gen_sql import Text2SQL

if __name__ == '__main__':
    from argsparser import parser

    args = parser.parse_args()

    from logger import setup_logger

    # directory name -> output
    logger = setup_logger(output="logs", name="test")

    text2sql = Text2SQL(logger_name="test", filter_mode=args.filter_mode, prompt_mode=args.prompt_mode,
                        n_shots=args.n_shots, few_shot_mode=args.few_shot_mode)

    save_file_name = args.save_file_name

    text2sql.main(root_dir='data', dataset=args.dataset, file=args.dataset_file,
                  save_file_name=save_file_name, mode=args.mode, lang_mode=args.lang_mode, sample=args.sample,
                  data_fold=args.data_fold, test_id=args.test_id, insert_value=args.insert_value,
                  step_name=args.step_name)
