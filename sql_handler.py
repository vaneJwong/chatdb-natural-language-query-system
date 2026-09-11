import os
import pandas as pd
import mysql.connector
from console_utils import ConsoleFormatter as cf
from tabulate import tabulate
import random
from datetime import datetime
import re


class SQLDatabaseHandler:
    def __init__(self, host, port, user, password, database):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database

    def create_database_and_tables(self, folder_path, selected_files):
        """
        Create database and import selected CSV files as tables.
        """
        print(cf.header("DATABASE IMPORT PROCESS"))
        
        connection = mysql.connector.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password
        )
        cursor = connection.cursor()
        
        print(f"\n{cf.info('Creating database:')} {cf.highlight(self.database)}")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
        cursor.execute(f"USE {self.database}")

        for file in selected_files:
            file_path = os.path.join(folder_path, file)
            table_name = file.replace(" ", "_").replace(".csv", "").lower()
            
            print(f"\n{cf.info('Processing file:')} {cf.highlight(file)}")
            print(f"{cf.info('Table name:')} {cf.highlight(table_name)}")
            
            df = pd.read_csv(file_path)
            print(f"{cf.info('Records read from CSV:')} {cf.highlight(len(df))}")

            # Drop table if it exists
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")


            columns = ["id INT AUTO_INCREMENT PRIMARY KEY"]
            
            # Dynamically determine column types
            def determine_column_type(column):
                max_length = df[column].astype(str).map(len).max()
                if max_length <= 255:
                    return f"{column.replace(' ', '_')} VARCHAR(255)"
                elif max_length <= 65535:
                    return f"{column.replace(' ', '_')} TEXT"
                else:
                    return f"{column.replace(' ', '_')} LONGTEXT"

            columns.extend([determine_column_type(col) for col in df.columns])
            columns_str = ", ".join(columns)
            
            print(f"{cf.info('Creating table with columns:')}\n{cf.highlight(columns_str)}")
            cursor.execute(f"CREATE TABLE {table_name} ({columns_str})")

            # Insert data into the table
            records_inserted = 0
            for _, row in df.iterrows():
                try:
                    escaped_values = []
                    for val in row:
                        if pd.isna(val):
                            escaped_values.append("NULL")
                        else:
                            escaped_val = str(val).replace("'", "''")
                            escaped_values.append(f"'{escaped_val}'")
                    values = ", ".join(escaped_values)

                    query = f"INSERT INTO {table_name} ({', '.join(df.columns)}) VALUES ({values})"
                    cursor.execute(query)
                    records_inserted += 1
                except Exception as e:
                    print(cf.error(f"Failed to insert row: {e}"))
                    continue

            print(cf.success(f"Successfully inserted {records_inserted} records"))

        connection.commit()
        connection.close()
        print(f"\n{cf.success(f'Successfully imported all files into SQL database `{self.database}`')}")

    def format_value(self, value, field_name):
        """Format value based on field type"""
        try:
            if field_name == 'ratings':
                # 处理评分，如果转换失败返回 '0'
                return f"{float(value):.1f}" if value is not None else '0'
            elif field_name == 'no_of_ratings':
                # 处理评论数，如果转换失败返回 '0'
                return f"{int(value.replace(',', '')):,}" if value is not None else '0'
            elif field_name in ['discount_price', 'actual_price']:
                # 处理价格，如果转换失败返回 '0'
                if value is None:
                    return '0'
                if not str(value).startswith('₹'):
                    return f"₹{value}"
                return value
            else:
                return str(value) if value is not None else '0'
        except (ValueError, AttributeError, TypeError):
            return '0'

    def get_random_sql_examples(self, table_name):
        """Get random SQL query examples based on current query type"""
        examples = [
            # 基础分组统计示例
            {
                "query": f"show total number of {table_name.replace('_', ' ')} group by category",
                "sql": f"SELECT sub_category, COUNT(*) as count FROM {table_name} GROUP BY sub_category ORDER BY count DESC",
                "explanation": "This query groups records by category and shows the count in each group."
            },
            # 条件分组统计示例
            {
                "query": f"show total number of {table_name.replace('_', ' ')} with rating greater than 4 group by category",
                "sql": f"""SELECT 
                    sub_category, 
                    COUNT(*) as count
                    FROM {table_name}
                    WHERE ratings > 4
                    GROUP BY sub_category
                    ORDER BY count DESC""",
                "explanation": "This query counts high-rated products (rating > 4) in each category."
            },
            # 评分统计示例
            {
                "query": f"show me average ratings by category for {table_name.replace('_', ' ')}",
                "sql": f"SELECT sub_category, AVG(ratings) AS average_rating FROM {table_name} GROUP BY sub_category ORDER BY average_rating DESC",
                "explanation": "This query calculates the average rating for each category."
            }
        ]
        return random.sample(examples, 3)

    def query(self, table_name, condition=None, order_by=None, limit=None, group_by=None, aggregate=None, 
              join_table=None, join_type=None, join_condition=None):
        """
        Perform SQL query with optional filtering, grouping, aggregation and joins.
        """
        print(cf.header("QUERY EXECUTION"))

        # Get random examples
        examples = self.get_random_sql_examples(table_name)
        for i, example in enumerate(examples, 1):
            print(f"\n{cf.info(f'Example Query {i}:')}")
            print(example["query"])
            print(f"{cf.info('Generated SQL:')}")
            print(cf.highlight(example["sql"]))
            print(f"{cf.info('SQL Explanation:')}")
            print(cf.highlight(example["explanation"]))

        # 当前查询
        print(f"\n{cf.info('Current Query:')}")
        # 修改查询构建部分
        if group_by:  # 优先处理分组查询
            if aggregate == "COUNT(*)":
                query = f"""
                    SELECT {group_by}, COUNT(*) as count 
                    FROM {table_name}
                    {f'WHERE CAST(ratings AS DECIMAL(10,2)) > 4' if 'ratings > 4' in condition else f'WHERE {condition}' if condition else ''}
                    GROUP BY {group_by}
                    ORDER BY count DESC
                """
            elif "AVG" in str(aggregate):  # 处理平均值查询
                query = f"""
                    SELECT {group_by}, {aggregate} as average_rating
                    FROM {table_name}
                    {f'WHERE {condition}' if condition else ''}
                    GROUP BY {group_by}
                    ORDER BY average_rating DESC
                """
            else:
                query = f"""
                    SELECT {group_by}, {aggregate}
                    FROM {table_name}
                    {f'WHERE {condition}' if condition else ''}
                    GROUP BY {group_by}
                """
        elif join_table and join_type:  # 其次处理联表查询
            if "," in join_table:  # 三表连接
                tables = join_table.split(",")
                query = f"""SELECT 
                    t1.id as {table_name}_id,
                    t1.name,
                    t1.ratings,
                    t1.no_of_ratings,
                    t1.discount_price,
                    t1.actual_price,
                    t1.sub_category as main_category,
                    t2.id as {tables[0]}_id,
                    t2.sub_category as related_category1,
                    t3.id as {tables[1]}_id,
                    t3.sub_category as related_category2
                FROM {table_name} t1
                {join_type} {tables[0]} t2 ON t1.sub_category = t2.sub_category
                {join_type} {tables[1]} t3 ON t1.main_category = t3.main_category"""
                # 修改条件中的字段引用
                if condition:
                    condition = condition.replace("discount_price", "t1.discount_price")
                    condition = condition.replace("actual_price", "t1.actual_price")
                    condition = condition.replace("ratings", "t1.ratings")
                    condition = condition.replace("no_of_ratings", "t1.no_of_ratings")
                    condition = condition.replace("sub_category", "t1.sub_category")
                    query += f" WHERE {condition}"
            else:  # 两表连接
                query = f"""
                    SELECT 
                        t1.id as {table_name}_id,
                        t1.name,
                        t1.ratings,
                        t1.no_of_ratings,
                        t1.discount_price,
                        t1.actual_price,
                        t1.sub_category as category,
                        t2.id as {join_table}_id,
                        t2.sub_category as related_category
                    FROM {table_name} t1
                    {join_type} {join_table} t2 ON t1.sub_category = t2.sub_category
                """
                # 修改条件中的字段引用
                if condition:
                    # 使用正则表达式进行精确替换
                    modified_condition = condition
                    field_mappings = {
                        r'\bno_of_ratings\b': "t1.no_of_ratings",
                        r'\bdiscount_price\b': "t1.discount_price",
                        r'\bactual_price\b': "t1.actual_price",
                        r'\bratings\b': "t1.ratings",
                        r'\bsub_category\b': "t1.sub_category"
                    }
                    for pattern, replacement in field_mappings.items():
                        modified_condition = re.sub(pattern, replacement, modified_condition)
                    query += f" WHERE {modified_condition}"
        else:  # 最后处理普通查询
            query = f"SELECT * FROM {table_name}"
            if condition:
                query += f" WHERE {condition}"
            if order_by:
                query += f" ORDER BY {order_by}"
            if limit:
                query += f" LIMIT {limit}"

        print(cf.highlight(query))
        
        print(f"{cf.info('Query Explanation:')}")
        explanation = "This query retrieves data"
        if condition:
            explanation += " with specified conditions"
        if order_by:
            explanation += " and sorts the results"
        if limit:
            explanation += f", returning up to {limit} records"
        print(cf.highlight(explanation + "."))

        # 修改执行确认部分
        while True:
            execute = input(cf.info("\nDo you want to execute this query? (yes/no): ")).strip().lower()
            if execute in ['yes', 'y']:
                break
            elif execute in ['no', 'n']:
                print(cf.warning("Query execution cancelled."))
                return "cancelled"
            else:
                print(cf.warning("Please enter 'yes' or 'no'"))

        # 执行查询并显示结果
        try:
            connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            cursor = connection.cursor(dictionary=True)
            
            # 打印实际执行的SQL语句，用于调试
            print(f"\nExecuting SQL: {query}")
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            print(cf.success(f"\nFound {len(results)} records"))
            print(cf.separator())
            
            if group_by:
                # 修改分组查询结果显示
                for result in results:
                    category = result.get(group_by)  # 直接获取分组字段
                    if category is None:
                        continue
                    
                    if 'count' in result:
                        count = result.get('count', 0)
                        print(cf.highlight(f"Category: {category}, Count: {count}"))
                    elif 'average_rating' in result:
                        avg_rating = result.get('average_rating', 0)
                        print(cf.highlight(f"Category: {category}, Average Rating: {avg_rating:.2f}"))
                    else:
                        # 处理其他聚合结果
                        value = next((v for k, v in result.items() if k != group_by), None)
                        if value is not None:
                            print(cf.highlight(f"Category: {category}, Value: {value}"))

            else:
                # 普通查询结果显示
                for result in results:
                    formatted_result = {
                        "Name": result.get("name", "")[:50] + "..." if len(result.get("name", "")) > 50 else result.get("name", ""),
                        "Rating": self.format_value(result.get("ratings"), "ratings"),
                        "Reviews": self.format_value(result.get("no_of_ratings"), "no_of_ratings"),
                        "Price": self.format_value(result.get("discount_price"), "discount_price"),
                        "Original": self.format_value(result.get("actual_price"), "actual_price")
                    }
                    print(cf.highlight(formatted_result))
            
            print(cf.separator())

            # 显示结果后添加交互选项
            while True:
                print(f"\n{cf.info('What would you like to do next?')}")
                print(cf.highlight("1. Modify this query"))
                print(cf.highlight("2. Run a similar query"))
                print(cf.highlight("3. Show SQL explanation again"))
                print(cf.highlight("4. Enter a new query"))
                print(cf.highlight("5. Return to main menu"))
                print(cf.highlight("6. Export query to file"))

                choice = input(cf.info("\nEnter your choice (1-6): ")).strip()
                
                if choice == "1":
                    print(cf.info("\nPlease enter your modified query:"))
                    return "modify"
                elif choice == "2":
                    template = f"show me {table_name.replace('_', ' ')}"
                    if condition:
                        template += " with similar conditions"
                    if order_by:
                        template += " and sorting"
                    if limit != 5:
                        template += f" limit {limit} records"
                    print(cf.info(f"\nTemplate: {template}"))
                    print(cf.info("Please enter your similar query:"))
                    return "similar"
                elif choice == "3":
                    print(f"\n{cf.info('SQL Explanation:')}")
                    print(cf.highlight(explanation + "."))
                    continue
                elif choice == "4":
                    print(cf.info("\nPlease enter your new query:"))
                    return "new"
                elif choice == "5":
                    return "exit"
                elif choice == "6":
                    # 导出查询到文件
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"query_{table_name}_{timestamp}.sql"
                    with open(filename, 'w') as f:
                        f.write(query)
                    print(cf.success(f"\nQuery exported to {filename}"))
                    continue
                else:
                    print(cf.error("Invalid choice. Please enter a number between 1 and 6."))

            return results
            
        except mysql.connector.Error as e:
            print(cf.error(f"Database error: {e}"))
            return "error"
        finally:
            if 'connection' in locals() and connection.is_connected():
                connection.close()
