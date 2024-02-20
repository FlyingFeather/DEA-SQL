import sys
import json
import argparse
import sqlite3
import multiprocessing as mp
from func_timeout import func_timeout, FunctionTimedOut


def load_json(dir):
    with open(dir, 'r') as j:
        contents = json.loads(j.read())
    return contents


def result_callback(result):
    exec_result.append(result)


def execute_sql(predicted_sql, ground_truth, db_path):
    conn = sqlite3.connect(db_path)
    # Connect to the database
    cursor = conn.cursor()
    cursor.execute(predicted_sql)
    predicted_res = cursor.fetchall()
    cursor.execute(ground_truth)
    ground_truth_res = cursor.fetchall()
    res = 0
    if set(predicted_res) == set(ground_truth_res):
        res = 1
    return res


def execute_model(predicted_sql, ground_truth, db_place, idx, meta_time_out):
    try:
        res = func_timeout(meta_time_out, execute_sql, args=(predicted_sql, ground_truth, db_place))
    except KeyboardInterrupt:
        sys.exit(0)
    except FunctionTimedOut:
        result = [(f'timeout',)]
        res = 0
    except Exception as e:
        result = [(f'error: {e}',)]  # possibly len(query) > 512 or not executable
        res = 0
    # print(result)
    # result = str(set([ret[0] for ret in result]))
    result = {'sql_idx': idx, 'res': res}
    # print(result)
    return result


def package_sqls(sql_path, db_root_path, mode='gpt', data_mode='dev'):
    clean_sqls = []
    db_path_list = []
    if mode == 'gpt':
        sqls = open(sql_path)
        sql_txt = sqls.readlines()
        for index, sql_str in enumerate(sql_txt):
            if isinstance(sql_str, str):
                try:
                    sql, db_name = sql_str.strip().split('\t----- bird -----\t')
                # sql, db_name = sql_str.strip().split('\t')
                except:
                    sql, db_name = " ", "financial"
            clean_sqls.append(sql)
            db_path_list.append(db_root_path + db_name + '/' + db_name + '.sqlite')
        sqls.close()
        # print(clean_sqls)
    elif mode == 'gt':
        sqls = open(sql_path)
        sql_txt = sqls.readlines()
        # sql_txt = [sql.split('\t')[0] for sql in sql_txt]
        for idx, sql_str in enumerate(sql_txt):
            sql, db_name = sql_str.strip().split('\t')
            clean_sqls.append(sql)
            db_path_list.append(db_root_path + db_name + '/' + db_name + '.sqlite')
        sqls.close()

    return clean_sqls, db_path_list


def run_sqls_parallel(sqls, db_places, num_cpus=1, meta_time_out=30.0):
    pool = mp.Pool(processes=num_cpus)
    for i, sql_pair in enumerate(sqls):

        predicted_sql, ground_truth = sql_pair
        pool.apply_async(execute_model, args=(predicted_sql, ground_truth,
                         db_places[i], i, meta_time_out), callback=result_callback)
    pool.close()
    pool.join()


def sort_results(list_of_dicts):
    return sorted(list_of_dicts, key=lambda x: x['sql_idx'])


def compute_acc_by_diff(exec_results, diff_json_path):
    num_queries = len(exec_results)
    results = [res['res'] for res in exec_results]
    contents = load_json(diff_json_path)
    simple_results, moderate_results, challenging_results = [], [], []

    for i, content in enumerate(contents):
        if content['difficulty'] == 'simple':
            simple_results.append(exec_results[i])

        if content['difficulty'] == 'moderate':
            moderate_results.append(exec_results[i])

        if content['difficulty'] == 'challenging':
            challenging_results.append(exec_results[i])

    simple_acc = sum([res['res'] for res in simple_results]) / len(simple_results)
    moderate_acc = sum([res['res'] for res in moderate_results]) / len(moderate_results)
    # try except is for debug
    try:
        challenging_acc = sum([res['res'] for res in challenging_results]) / len(challenging_results)
    except:
        challenging_acc = 0
    all_acc = sum(results) / num_queries
    count_lists = [len(simple_results), len(moderate_results), len(challenging_results), num_queries]
    return simple_acc * 100, moderate_acc * 100, challenging_acc * 100, all_acc * 100, count_lists


def compute_acc_by_diff_sample(exec_results, query_pairs, diff_json_path, sample=True, test_id=None, fold="1", whether_print=False, print_file_name=""):
    num_queries = len(exec_results)
    results = [res['res'] for res in exec_results]
    contents = load_json(diff_json_path)
    if sample:
        import sys
        sys.path.append("..")
        import os
        from sample import get_sample_idx
        idx = get_sample_idx(fold, "bird", root_dir=os.path.realpath(".."))
        contents = [contents[i] for i in idx]
    if test_id is not None:
        contents = [load_json(diff_json_path)[test_id]]

    # xzjin add
    if whether_print:
        details = open(print_file_name, mode='r').readlines()
    # xzjin add

    simple_results, moderate_results, challenging_results = [], [], []

    for i, content in enumerate(contents):
        if content['difficulty'] == 'simple':
            simple_results.append(exec_results[i])

        if content['difficulty'] == 'moderate':
            moderate_results.append(exec_results[i])

        if content['difficulty'] == 'challenging':
            challenging_results.append(exec_results[i])

        # xzjin add
        if whether_print:
            dirname, basename = os.path.dirname(print_file_name), os.path.basename(print_file_name)
            file_name = os.path.join(dirname, f"processed_{basename}")
            p_str, g_str = query_pairs[i]
            with open(file_name, mode='a') as f:
                data = json.loads(details[i])
                for k, v in data.items():
                    if k != "init_table_infos":
                        f.write(f"{k}: {v}\n")
                    if k == 'query':
                        f.write(f"-----------------------------------------------\n")
                    if k == "init_table_infos":
                        f.write(f"{k}: {v}-----------------------------------------------\n")
                    if k == "table_info":
                        f.write(f"-----------------------------------------------\n")
                    if k == "features":
                        f.write(f"-----------------------------------------------\n")
                    # f.write(f"{k}: {v}\n")
                f.write(f"pred: {p_str}\ngroud_truth: {g_str}\nresult: {exec_results[i]['res']}\n\n\n")
                f.write(f"################################################################\n")
        # xzjin add

    # try except is for debug
    try:
        simple_acc = sum([res['res'] for res in simple_results]) / len(simple_results)
    except:
        simple_acc = 0
    try:
        moderate_acc = sum([res['res'] for res in moderate_results]) / len(moderate_results)
    except:
        moderate_acc = 0
    try:
        challenging_acc = sum([res['res'] for res in challenging_results]) / len(challenging_results)
    except:
        challenging_acc = 0
    all_acc = sum(results) / num_queries
    count_lists = [len(simple_results), len(moderate_results), len(challenging_results), num_queries]
    return simple_acc * 100, moderate_acc * 100, challenging_acc * 100, all_acc * 100, count_lists


def print_data(score_lists, count_lists):
    levels = ['simple', 'moderate', 'challenging', 'total']
    print("{:20} {:20} {:20} {:20} {:20}".format("", *levels))
    print("{:20} {:<20} {:<20} {:<20} {:<20}".format('count', *count_lists))

    print('======================================    ACCURACY    =====================================')
    print("{:20} {:<20.2f} {:<20.2f} {:<20.2f} {:<20.2f}".format('accuracy', *score_lists))


if __name__ == '__main__':
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--predicted_sql_path', type=str, required=True, default='')
    args_parser.add_argument('--ground_truth_path', type=str, required=True, default='')
    args_parser.add_argument('--data_mode', type=str, required=True, default='dev')
    args_parser.add_argument('--db_root_path', type=str, required=True, default='')
    args_parser.add_argument('--num_cpus', type=int, default=1)
    args_parser.add_argument('--meta_time_out', type=float, default=30.0)
    args_parser.add_argument('--mode_gt', type=str, default='gt')
    args_parser.add_argument('--mode_predict', type=str, default='gpt')
    args_parser.add_argument('--difficulty', type=str, default='simple')
    args_parser.add_argument('--diff_json_path', type=str, default='')
    args_parser.add_argument('--sample', default=False, action='store_true', help='whether to sample')
    args_parser.add_argument('--test_id', type=int, default=None, help='the test id')
    args_parser.add_argument("--data_fold", type=str, default="1", help="1, 2, 3")
    args_parser.add_argument('--whether_print', default=False, action='store_true', help='whether to print processed file')
    args_parser.add_argument('--print_file_name', type=str, help='the name of processed file')
    args = args_parser.parse_args()
    exec_result = []

    pred_queries, db_paths = package_sqls(args.predicted_sql_path, args.db_root_path, mode=args.mode_predict,
                                          data_mode=args.data_mode)
    # generate gt sqls:
    gt_queries, db_paths_gt = package_sqls(args.ground_truth_path, args.db_root_path, mode='gt',
                                           data_mode=args.data_mode)

    query_pairs = list(zip(pred_queries, gt_queries))
    run_sqls_parallel(query_pairs, db_places=db_paths, num_cpus=args.num_cpus, meta_time_out=args.meta_time_out)
    exec_result = sort_results(exec_result)

    print('start calculate')
    # simple_acc, moderate_acc, challenging_acc, acc, count_lists = \
    #     compute_acc_by_diff(exec_result, args.diff_json_path)
    simple_acc, moderate_acc, challenging_acc, acc, count_lists = \
        compute_acc_by_diff_sample(exec_result, query_pairs, args.diff_json_path, args.sample, args.test_id, args.data_fold, args.whether_print, args.print_file_name)
    score_lists = [simple_acc, moderate_acc, challenging_acc, acc]
    print_data(score_lists, count_lists)
    print('===========================================================================================')
    print("Finished evaluation")
