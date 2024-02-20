import os
import json
import sqlite3


def is_number(token):
    """Check if token is a SQL number literal."""
    try:
        float(token)
        return True
    except ValueError:
        return False


def normalize_create_table(table_name, create_table_statement):
    create_table_statement = create_table_statement.strip()
    create_table_statement = create_table_statement.replace("`", "\"").replace("'", "\"").replace("[", "\"").replace("]", "\"")
    create_table_statement = create_table_statement.replace("\"", '')
    create_table_statement = create_table_statement.replace('\t', ' ').replace('\n', ' ')
    create_table_statement = ' '.join(create_table_statement.split())
    create_table_statement_split = [""]
    num_left = 0
    for tok in create_table_statement:
        if tok == "(":
            num_left += 1
            create_table_statement_split[-1] += tok
        elif tok == ")":
            num_left -= 1
            create_table_statement_split[-1] += tok
        elif tok != ',':
            create_table_statement_split[-1] += tok
        if tok == ',':
            if num_left == 1:
                create_table_statement_split.append("")
                continue
            else:
                create_table_statement_split[-1] += tok
                continue
    create_table_statement = create_table_statement_split
    new_create_table_statement = []
    for i, x in enumerate(create_table_statement):
        if i == 0:
            x = x.split('(')
            x1 = x[0].strip()
            x2 = ','.join(x[1:]).strip()
            new_create_table_statement.append(x1 + " (")
            new_create_table_statement.append(x2 + ",")
        elif i == len(create_table_statement) - 1:
            x = x.split(')')
            x1 = ')'.join(x[:-1]).strip()
            x2 = x[-1].strip()
            new_create_table_statement.append(x1)
            new_create_table_statement.append(x2 + ")")
        else:
            new_create_table_statement.append(x.strip() + ",")

    return '\n'.join(new_create_table_statement)


def get_foreign_keys(db_id, table, create_table_statement, table_upper=False):
    foreign_keys = []
    for row in create_table_statement.split('\n'):
        if row.lower().startswith("foreign key") and row.lower().count("foreign key") == 1:
            if " on " in row:
                row = row.split(" on ")[0]
            if " ON " in row:
                row = row.split(" ON ")[0]
            # row.replace(" ON DELETE CASCADE", "")
            # row.replace(" on delete cascade", "")
            row = row.replace(",", " ").replace("(", "  ").replace(")", "  ")
            row = row.split()
            if len(row) != 6:  # multiple keys
                # print(db_id, create_table_statement)
                for i, tok in enumerate(row):
                    if tok.lower() == "references":
                        references_pos = i
                num_keys = references_pos - 2
                # print(num_keys)
                # print(row)
                for i in range(num_keys):
                    if table_upper == True:
                        key = f"{table.upper()}.{row[2 + i].lower()} = {row[4 + num_keys - 1].upper()}.{row[4 + num_keys + i].lower()}"
                    else:
                        key = f"{table}.{row[2 + i]} = {row[4 + num_keys - 1]}.{row[4 + num_keys + i]}"
                    foreign_keys.append(key)
                # print(foreign_keys)
                continue
            else:
                # assert len(row) == 6
                if table_upper == True:
                    key = f"{table.upper()}.{row[2].lower()} = {row[4].upper()}.{row[5].lower()}"
                else:
                    key = f"{table}.{row[2]} = {row[4]}.{row[5]}"
                foreign_keys.append(key)
    return foreign_keys


def extract_tablecolumn_prompt(prompt_db, db_id, db_path, limit_value=3, normalization=True):
    table_query = "SELECT * FROM sqlite_master WHERE type='table';"
    tables = sqlite3.connect(db_path).cursor().execute(table_query).fetchall()
    prompt = ""
    foreign_keys = []
    table_names = []
    for table in tables:
        table_name = table[1]
        if table_name == 'sqlite_sequence':
            continue
        table_names.append(table_name)
        if normalization:
            table_name = table_name.lower()
        create_table_statement = table[-1]
        create_table_statement = normalize_create_table(table_name, create_table_statement)
        foreign_keys_one_table = get_foreign_keys(db_id, table_name, create_table_statement)
        table_info_query = f"PRAGMA table_info({table_name});"
        headers = [x[1] for x in sqlite3.connect(db_path).cursor().execute(table_info_query).fetchall()]
        if normalization:
            foreign_keys_one_table = [x.lower() for x in foreign_keys_one_table]
            headers = [x.lower() for x in headers]
        foreign_keys.extend(foreign_keys_one_table)
        table_statement = ""
        if prompt_db.startswith("Table(Columns)"):
            table_statement += f"{table_name}({', '.join(headers)});\n"
        if prompt_db.startswith("Columns=[]"):
            table_statement += f"Table {table_name}, Columns = [{', '.join(headers)}];\n"
        prompt += table_statement
    if "+FK" in prompt_db:
        prompt += "Foreign_keys = [" + ', '.join(foreign_keys) + "];\n"
    prompt += '\n'
    return prompt, table_names


def extract_create_table_prompt(prompt_db, db_id, db_path, limit_value=3, normalization=True):
    table_query = "SELECT * FROM sqlite_master WHERE type='table';"
    tables = sqlite3.connect(db_path).cursor().execute(table_query).fetchall()
    prompt = ""
    table_names = []
    foreign_keys = []
    for table in tables:
        table_name = table[1]
        if table_name == 'sqlite_sequence':
            continue
        table_names.append(table_name)
        if normalization:
            table_name = table_name.lower()
        create_table_statement = table[-1]

        # xzjin 解决 'CREATE TABLE rankings("ranking_date" DATE,"ranking" INT,"player_id" INT,"ranking_points" INT,"tours" INT,FOREIGN KEY(player_id) REFERENCES players(player_id))'
        original_sql = create_table_statement.split("\n")
        if len(original_sql) == 1:
            original_sql = original_sql[0]
            formatted_sql = re.sub(r'\((.*)\)', lambda match: f'(\n{match.group(1)}\n)', original_sql, flags=re.DOTALL)
            # 在最后一个右括号前添加换行符
            formatted_sql = re.sub(r'(?<=\))$', '\n', formatted_sql)
            formatted_sql = formatted_sql.replace(",", ",\n")
            create_table_statement = formatted_sql

        # 外键表
        fk_create_table_statement = normalize_create_table(table_name, create_table_statement)

        # xzjin add 解决空行问题
        create_table_statement = create_table_statement.split("\n")
        new_lines = []
        for line in create_table_statement:
            if line.strip():  # 判断去除空白字符后是否还有内容
                new_lines.append(line)
        create_table_statement = "\n".join(new_lines)

        table_info_query = f"PRAGMA table_info({table_name});"
        top_k_row_query = f"SELECT * FROM {table_name} LIMIT {limit_value};"
        headers = [x[1] for x in sqlite3.connect(db_path).cursor().execute(table_info_query).fetchall()]

        if "fk" in prompt_db.lower():
            if normalization.startswith("upper") or normalization.startswith("newupper"):
                foreign_keys_one_table = get_foreign_keys(db_id, table_name, fk_create_table_statement, True)
            else:
                foreign_keys_one_table = get_foreign_keys(db_id, table_name, fk_create_table_statement, False)
            foreign_keys.extend(foreign_keys_one_table)

        # xzjin add 控制空行和大小写
        if normalization == "upper":
            create_table_statement = create_table_statement.split("\n")
            new_lines = []
            for line in create_table_statement:
                if "create table" in line.lower():
                    line = line.upper()
                line = re.sub(r'[`"\']', '', line)
                new_lines.append(line)
            create_table_statement = "\n".join(new_lines)

        if isinstance(normalization, str) and normalization.startswith("newupper"):
            # table_name is upper, others is lower, including insert.
            create_table_statement = create_table_statement.split("\n")
            new_lines = []
            length = len(create_table_statement)
            for idx_, line in enumerate(create_table_statement):
                line = re.sub(r'[`"\',]', '', line)
                if "fk" not in normalization:
                    if "foreign key" in line.lower():
                        continue
                if "create table" in line.lower():
                    line = line.strip()
                    line = list(line)
                    if line[-2] == " ":
                        line.pop(-2)
                    line = ''.join(line)
                    line = line.upper()
                else:
                    line = line.lower()
                    line = line.strip()
                    line = line.replace("\t", " ")
                    while "  " in line:
                        line = line.replace("  ", " ")

                    # 修复 foreign key (document_id) references documents (document_id) 为
                    # foreign key (document_id) references DOCUMENTS(document_id)
                    if "foreign key" in line:
                        # 去括号里的空格
                        line = re.sub(r'\s*\(\s*(.*?)\s*\)', r'(\1)', line)
                        if "references" not in line:
                            continue
                        try:
                            ref_idx = line.index("references")
                            temp_line = line[ref_idx + len("references"):].replace(" ", "")
                            spilt_idx = temp_line.index("(")
                            temp_line = temp_line[:spilt_idx].upper() + temp_line[spilt_idx:]
                            line = line[:ref_idx + len("references")] + " " + temp_line
                        except:
                            pass
                    if idx_ != length - 1:
                        line = "    " + line
                line = re.sub(r'[`"\',]', '', line)
                if idx_ != 0 and idx_ != length - 2 and idx_ != length - 1:
                    line = line.rstrip()
                    line += ","
                new_lines.append(line)
            create_table_statement = "\n".join(new_lines)
            headers = [x.lower() for x in headers]

        if normalization == "lower":
            create_table_statement = create_table_statement.split("\n")
            new_lines = []
            for line in create_table_statement:
                if "create table" in line.lower():
                    line = line.lower()
                    line = line.replace("create table", "CREATE TABLE")
                line = re.sub(r'[`"\']', '', line)
                new_lines.append(line)
            create_table_statement = "\n".join(new_lines)
            # headers = [x.lower() for x in headers]

        if normalization == True:
            create_table_statement = normalize_create_table(table_name, create_table_statement)
            create_table_statement = create_table_statement.lower()
            top_k_row_query = top_k_row_query.lower()
            headers = [x.lower() for x in headers]

        top_k_rows = sqlite3.connect(db_path).cursor().execute(top_k_row_query).fetchall()

        # print(create_table_statement)
        # print(headers)
        prompt += create_table_statement + ";\n"

        if limit_value > 0:
            if prompt_db.startswith("CreateTableSelectRow"):
                prompt += f"/*\n3 example rows:\n{top_k_row_query}\n{'    '.join(headers)}\n"
                for row in top_k_rows:
                    row = [str(x) for x in row]
                    row = [x if x is not None else "" for x in row]

                    prompt += '    '.join(row) + "\n"
                prompt += "*/\n"
            elif prompt_db.startswith("CreateTableInsertRow"):
                for row in top_k_rows:
                    if normalization:
                        insert_statement = f"insert into {table_name} (" + ', '.join(headers) + ") values "
                    elif normalization == "newupper":
                        insert_statement = f"insert into {table_name.upper()} (" + ', '.join(headers) + ") values "
                    else:
                        insert_statement = f"INSERT INTO {table_name} (" + ', '.join(headers) + ") VALUES "
                    row = [x if x is not None else "" for x in row]
                    row = [str(x) if is_number(x) else '"' + str(x) + '"' for x in row]
                    insert_statement += "(" + ', '.join(row) + ");"
                    prompt += insert_statement + "\n"
        prompt += "\n"

    if "fk" in prompt_db.lower():
        prompt += "Foreign_keys = [" + ', '.join(foreign_keys) + "];\n"
    return prompt, table_names


def extract_create_table_prompt_column_example(prompt_db, db_id, db_path, limit_value=3, normalization=True):
    table_query = "SELECT * FROM sqlite_master WHERE type='table';"
    tables = sqlite3.connect(db_path).cursor().execute(table_query).fetchall()
    prompt = ""
    table_names = []
    for table in tables:
        table_name = table[1]
        if table_name == 'sqlite_sequence':
            continue
        table_names.append(table_name)
        if normalization:
            table_name = table_name.lower()
        create_table_statement = table[-1]

        table_info_query = f"PRAGMA table_info({table_name});"
        headers = [x[1] for x in sqlite3.connect(db_path).cursor().execute(table_info_query).fetchall()]
        if normalization:
            create_table_statement = normalize_create_table(table_name, create_table_statement)
            create_table_statement = create_table_statement.lower()
            headers = [x.lower() for x in headers]
        prompt += create_table_statement + ";\n"
        if limit_value > 0:
            prompt_columns = []
            for col_name in headers:
                if col_name.lower() == "index":
                    top_k_rows = list(range(limit_value))
                    top_k_rows = '    '.join([str(x) for x in top_k_rows])
                else:
                    top_k_row_query = f"SELECT distinct \"{col_name}\" FROM {table_name} LIMIT {limit_value};"
                    top_k_rows = sqlite3.connect(db_path).cursor().execute(top_k_row_query).fetchall()
                    top_k_rows = [x[0].strip() if isinstance(x[0], str) else x[0]
                                  for x in top_k_rows]  # remove \n and space prefix and suffix in cell value
                    top_k_rows = [x if x is not None else "" for x in top_k_rows]
                    top_k_rows = ', '.join([str(x) if is_number(x) else '"' + str(x) + '"' for x in top_k_rows][:limit_value])

                prompt_columns.append(f"{col_name}: {top_k_rows};")

            prompt += "/*\n"
            prompt += f"Columns in {table_name} and {limit_value} distinct examples in each column:\n"
            prompt += "\n".join(prompt_columns)
            prompt += "\n*/\n"
        prompt += "\n"

    return prompt, table_names


def generate_db_prompt_spider(root_dir, dataset, db_id, prompt_db="CreateTableSelect", limit_value=3, normalization=True):
    DATA_PATH = root_dir
    db_dir = f"{DATA_PATH}/{dataset}/database"
    table_path = f"{DATA_PATH}/{dataset}/tables/tables.json"
    table_names = None

    db_path = os.path.join(db_dir, db_id, db_id + ".sqlite")
    if prompt_db.startswith("Table(Columns)") or prompt_db.startswith("Columns=[]"):
        schema_prompt = extract_tablecolumn_prompt(
            prompt_db, db_id, db_path, limit_value=limit_value, normalization=normalization)
    elif prompt_db.startswith("CreateTable"):
        if prompt_db.startswith("CreateTableSelectCol"):
            schema_prompt, table_names = extract_create_table_prompt_column_example(
                prompt_db, db_id, db_path, limit_value=limit_value, normalization=normalization)
        else:
            schema_prompt, table_names = extract_create_table_prompt(
                prompt_db, db_id, db_path, limit_value=limit_value, normalization=normalization)
    else:
        print(prompt_db)
        raise NotImplementedError
    # prompt = schema_prompt + "-- Using valid SQLite, answer the following questions for the tables provided above.\n"
    prompt = schema_prompt
    if table_names is not None:
        return prompt, table_names
    return prompt


######################################## bird schema #########################################
import re
import glob
import pandas as pd
from langchain.sql_database import SQLDatabase


def table_descriptions_parser(root_dir, dataset, db_id):
    DATA_PATH = root_dir
    dev_db_path = f"{DATA_PATH}/{dataset}/dev_databases"
    database_dir = dev_db_path + "/" + db_id + "/" + "database_description"  # noqa: E501
    csv_files = glob.glob(f"{database_dir}/*.csv")
    # Iterate over the CSV files
    db_descriptions = ""
    for file_path in csv_files:
        table_name: str = os.path.basename(file_path).replace(".csv", "")
        db_descriptions += f"Table: {table_name}\n"
        table_df = pd.read_csv(file_path, encoding='utf-8')
        for _, row in table_df.iterrows():
            try:
                if pd.notna(row[2]):
                    col_description = re.sub(r'\s+', ' ', str(row[2]))  # noqa: E501
                    val_description = re.sub(r'\s+', ' ', str(row[4]))
                    if pd.notna(row[4]):
                        db_descriptions += f"Column {row[0]}: column description -> {col_description}, value description -> {val_description}\n"  # noqa: E501
                    else:
                        db_descriptions += f"Column {row[0]}: column description -> {col_description}\n"  # noqa: E501
            except Exception as e:
                print(e)
                db_descriptions += "No column description"
        db_descriptions += "\n"
    return db_descriptions


def generate_db_prompt_bird(root_dir, dataset, db_id, limit_value=3) -> str:
    """Get the database schema from the database URI
    """
    DATA_PATH = root_dir
    dev_db_path = f"{DATA_PATH}/{dataset}/dev_databases"
    db_uri = dev_db_path + "/" + db_id + "/" + db_id + ".sqlite"
    # table_path = f"{DATA_PATH}/{dataset}/dev_tables.json"
    # with open(table_path, "r") as f:
    #     tables = json.load(f)
    # table_names = tables[db_id]["table_names"]
    conn = sqlite3.connect(db_uri)

    # Create a cursor object
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    table_names = []
    for table in tables:
        if table == 'sqlite_sequence':
            continue
        if isinstance(table, tuple):
            table_name = table[0]
            table_names.append(table_name)
    db = SQLDatabase.from_uri("sqlite:///" + db_uri)
    db._sample_rows_in_table_info = limit_value
    return db.get_table_info_no_throw(), table_names


def get_db_schemas(bench_root: str, db_name: str):
    """
    Read an sqlite file, and return the CREATE commands for each of the tables in the database.
    """
    asdf = 'database' if bench_root == 'spider' else 'databases'
    with sqlite3.connect(f'file:{bench_root}/{asdf}/{db_name}/{db_name}.sqlite?mode=ro', uri=True) as conn:
        # conn.text_factory = bytes
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        schemas = {}
        for table in tables:
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='{}';".format(table[0]))
            schemas[table[0]] = cursor.fetchone()[0]

        return schemas


def nice_look_table(column_names: list, values: list):
    rows = []
    # Determine the maximum width of each column
    widths = [max(len(str(value[i])) for value in values + [column_names]) for i in range(len(column_names))]

    # Print the column names
    header = ''.join(f'{column.rjust(width)} ' for column, width in zip(column_names, widths))
    # print(header)
    # Print the values
    for value in values:
        row = ''.join(f'{str(v).rjust(width)} ' for v, width in zip(value, widths))
        rows.append(row)
    rows = "\n".join(rows)
    final_output = header + '\n' + rows
    return final_output


def generate_db_prompt_bird_v2(root_dir, dataset, db_id, limit_value=3):
    # extract create ddls
    '''
    :param root_place:
    :param db_name:
    :return:
    '''
    DATA_PATH = root_dir
    dev_db_path = f"{DATA_PATH}/{dataset}/dev_databases"
    db_uri = dev_db_path + "/" + db_id + "/" + db_id + ".sqlite"
    full_schema_prompt_list = []
    table_names = []
    conn = sqlite3.connect(db_uri)
    # Create a cursor object
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    schemas = {}
    for table in tables:
        if table == 'sqlite_sequence':
            continue
        if isinstance(table, tuple):
            table_name = table[0]
            table_names.append(table_name)
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='{}';".format(table[0]))
        create_prompt = cursor.fetchone()[0]
        schemas[table[0]] = create_prompt
        if limit_value:
            cur_table = table[0]
            if cur_table in ['order', 'by', 'group']:
                cur_table = "`{}`".format(cur_table)

            cursor.execute("SELECT * FROM {} LIMIT {}".format(cur_table, limit_value))
            column_names = [description[0] for description in cursor.description]
            values = cursor.fetchall()
            rows_prompt = nice_look_table(column_names=column_names, values=values)
            verbose_prompt = "/* \n {} example rows: \n SELECT * FROM {} LIMIT {}; \n {} \n */".format(
                limit_value, cur_table, limit_value, rows_prompt)
            schemas[table[0]] = "{} \n {}".format(create_prompt, verbose_prompt)

    for k, v in schemas.items():
        full_schema_prompt_list.append(v)

    schema_prompt = "\n\n".join(full_schema_prompt_list)

    return schema_prompt, table_names


if __name__ == "__main__":
    file1 = "train_spider.json"
    file2 = "train_others.json"
    with open(os.path.join("data", "spider", file1)) as f:
        data = json.load(f)
    with open(os.path.join("data", "spider", file2)) as f:
        data2 = json.load(f)
        data.extend(data2)

    print(data[53])
    db_id = data[53]['db_id']
    init_table_infos, table_list = generate_db_prompt_spider(
        root_dir='data', dataset='spider', db_id=db_id, prompt_db="CreateTableInsertRowFK", normalization="newupper", limit_value=0)
    print(init_table_infos)
