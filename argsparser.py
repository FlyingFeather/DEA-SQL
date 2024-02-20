import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--question", type=str)
parser.add_argument("--openai_api_key", type=str)
parser.add_argument("--openai_group_id", type=str, default="")
parser.add_argument("--model", type=str)
parser.add_argument("--start_index", type=int, default=0)
parser.add_argument("--end_index", type=int, default=1000000)
parser.add_argument("--temperature", type=float, default=0)
parser.add_argument("--mini_index_path", type=str, default="")
parser.add_argument("--batch_size", type=int, default=1)
parser.add_argument("--n", type=int, default=5, help="Size of self-consistent set")
parser.add_argument("--db_dir", type=str, default="dataset/spider/database")

# our configuration
parser.add_argument("--key_config", type=str, default='api_key1', help="api_key1, api_key2, api_key3")
parser.add_argument("--key_version", type=str, default='gpt-4', help="gpt-35-turbo, gpt-4")
parser.add_argument("--save_file_name", type=str, default="test.txt", help="sql save file")
parser.add_argument("--dataset", type=str, default="spider", help="spider or dev (bird)")
parser.add_argument("--sample", type=str, default="False", help="True or False")
parser.add_argument("--mode", type=str, default="debug", help="debug or dev")
parser.add_argument("--lang_mode", type=str, default="en", help="just en")
parser.add_argument("--filter_mode", type=str, default="complex", help="simple, complex, simple_v2, none")
parser.add_argument("--prompt_mode", type=str, default="v2", help="v1, v2, v3, v4")
parser.add_argument("--data_fold", type=str, default="1", help="1, 2, 3")
parser.add_argument('--train', default=False, action='store_true', help='train or dev')
parser.add_argument("--dataset_file", type=str, default="dev.json")
parser.add_argument("--test_id", type=int, default=46, help="1, 2, 3")

parser.add_argument("--re_run", default=False, action='store_true')
parser.add_argument('--re_run_idx', type=int, default=0)

parser.add_argument("--sc_nums_question_label", type=int, default=1, help="self-consistency numbers")
parser.add_argument("--sc_nums", type=int, default=1, help="self-consistency numbers")
parser.add_argument("--sc_filter_nums", type=int, default=2, help="self-consistency numbers")
parser.add_argument("--sc_filter_temp", type=float, default=0, help="self-consistency temperature for filter")
parser.add_argument("--sc_ques_temp", type=float, default=0, help="self-consistency temperature for question type")
parser.add_argument("--sc_sql_temp", type=float, default=0, help="self-consistency temperature for sql generation")
parser.add_argument("--insert_value", type=int, default=0, help="insert value of table schema")
parser.add_argument('--step_name', type=str, default="all",
                    help='Which step to execute? one of ["all", "ner_results", "filter_infos", "qc", "sql"]')
parser.add_argument('--step', default=False, action='store_true', help='whether open the mode step debug')
parser.add_argument('--step1', default=False, action='store_true', help='rerun step1')
parser.add_argument('--step2', default=False, action='store_true', help='skip step1')
parser.add_argument('--step3', default=False, action='store_true', help='skip step1, 2')
parser.add_argument('--step4', default=False, action='store_true', help='skip step1, 2, 3')
parser.add_argument('--step5', default=False, action='store_true', help='skip step1, 2, 3, 4')
parser.add_argument('--step6', default=False, action='store_true', help='skip step1, 2, 3, 4, 5')
parser.add_argument('--save_version', type=int, default=1, help='the step version')
parser.add_argument('--n_shots', type=int, default=3, help='the number of shots')
parser.add_argument('--few_shot_data', type=str, default='train_merge_v1',
                    help='one of ["train_merge_v1", "train_merge_v5"]')
parser.add_argument('--few_shot_mode', type=str, default='ques_sim1',
                    help='one of ["random", "ques_sim", "masked_ques_sim", "query_sim"]')
parser.add_argument('--embedding_base_model', type=str, default='openai', help='one of ["transformer", "openai"]')
parser.add_argument('--schema_mode', type=str, default='CreateTableInsertRowFK',
                    help='one of ["CreateTableInsertRow", "CreateTableInsertRowFK"]')
# Table(Columns), Columns=[], Columns=[]+FK, CreateTable, CreateTableInsertRow, CreateTableSelectRow, CreateTableSelectCol
parser.add_argument('--fk_mode', type=str, default="newupperfk", help="newupperfk means keep internal fk, newupper means not keep internal fk")

parser.add_argument('--has_error_case', default=False, action='store_true', help='has error case in generate sql')

### ablation experiment
parser.add_argument('--reduce_ql', default=False, action='store_true', help='reduce the step of question label')


################## evaluate singel sql ##########################
parser.add_argument('--db', dest='db', type=str, default="./data/spider/database",
                    help="the directory that contains all the databases and test suites")
parser.add_argument('--table', dest='table', type=str, default="./data/spider/tables.json",
                    help="the tables.json schema file")
parser.add_argument('--etype', dest='etype', type=str, default='exec',
                    help="evaluation type, exec for test suite accuracy, match for the original "
                         "exact set match accuracy",
                    choices=('all', 'exec', 'match'))
parser.add_argument('--plug_value', default=False, action='store_true',
                    help='whether to plug in the gold value into the predicted query; suitable if your model '
                         'does not predict values.')
parser.add_argument('--keep_distinct', default=False, action='store_true',
                    help='whether to keep distinct keyword during evaluation. default is false.')
parser.add_argument('--progress_bar_for_each_datapoint', default=False, action='store_true',
                    help='whether to print progress bar of running test inputs for each datapoint')
