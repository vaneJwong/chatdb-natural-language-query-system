import os
import pandas as pd
from pymongo import MongoClient
from console_utils import ConsoleFormatter as cf
from tabulate import tabulate
import random
import json
from datetime import datetime
import re


class NoSQLDatabaseHandler:
    def __init__(self, connection_string, database):
        self.client = MongoClient(connection_string)
        self.db = self.client[database]

    def import_data(self, folder_path, selected_files):
        """
        Import CSV files into MongoDB collections.
        """
        print(cf.header("DATABASE IMPORT PROCESS"))
        
        for file in selected_files:
            file_path = os.path.join(folder_path, file)
            collection_name = file.replace(" ", "_").replace(".csv", "").lower()
            
            print(f"\n{cf.info('Processing file:')} {cf.highlight(file)}")
            print(f"{cf.info('Collection name:')} {cf.highlight(collection_name)}")
            
            df = pd.read_csv(file_path)
            print(f"{cf.info('Records read from CSV:')} {cf.highlight(len(df))}")
            
            self.db[collection_name].drop()
            result = self.db[collection_name].insert_many(df.to_dict("records"))
            print(cf.success(f"Successfully inserted {len(result.inserted_ids)} records"))
        
        print(f"\n{cf.header('DATABASE STATUS')}")
        for collection in self.db.list_collection_names():
            count = self.db[collection].count_documents({})
            print(cf.info(f"Collection '{collection}': {count} documents"))

    def format_value(self, value, field_name):
        """Format value based on field type"""
        try:
            if field_name == 'ratings':
                # 处理评分
                return f"{float(value):.1f}"
            elif field_name == 'no_of_ratings':
                # 处理评论数，添加千位分隔符
                return f"{int(value.replace(',', '')):,}"
            elif field_name in ['discount_price', 'actual_price']:
                # 保持价格的货币符号和格式
                if not value.startswith('₹'):
                    return f"₹{value}"
                return value
            else:
                return str(value)
        except (ValueError, AttributeError):
            return str(value)

    def get_random_nosql_examples(self, collection_name):
        """Get random NoSQL query examples based on current query type"""
        examples = [
            # 基础查询示例
            {
                "query": f"show me {collection_name.replace('_', ' ')} limit 10 records",
                "pipeline": f"db.{collection_name}.find({{}}, {{ name: 1, ratings: 1, no_of_ratings: 1, discount_price: 1, actual_price: 1, _id: 0 }}).limit(10)",
                "explanation": "This pipeline retrieves documents from the collection and limits the output to 10 records."
            },
            # 评分查询示例
            {
                "query": f"show me {collection_name.replace('_', ' ')} with rating greater than 4.5 limit 10 records",
                "pipeline": f"db.{collection_name}.find({{ ratings: {{ $gt: '4.5' }} }}, {{ name: 1, ratings: 1, no_of_ratings: 1, discount_price: 1, actual_price: 1, _id: 0 }}).limit(10)",
                "explanation": "This pipeline filters documents with high ratings and returns up to 10 records."
            },
            # 评论数查询示例
            {
                "query": f"show me {collection_name.replace('_', ' ')} with comments greater than 5000 limit 10 records",
                "pipeline": f"db.{collection_name}.find({{ no_of_ratings: {{ $gt: '5000' }} }}, {{ name: 1, ratings: 1, no_of_ratings: 1, discount_price: 1, actual_price: 1, _id: 0 }}).limit(10)",
                "explanation": "This pipeline finds popular products with many reviews."
            },
            # 组合条件示例
            {
                "query": f"show me {collection_name.replace('_', ' ')} with rating greater than 4 and comments greater than 1000",
                "pipeline": f"db.{collection_name}.find({{ $and: [{{ ratings: {{ $gt: '4' }}, no_of_ratings: {{ $gt: '1000' }} }}] }}, {{ name: 1, ratings: 1, no_of_ratings: 1, discount_price: 1, actual_price: 1, _id: 0 }})",
                "explanation": "This pipeline combines rating and review count conditions."
            },
            # 基础分组统计示例
            {
                "query": f"show total number of {collection_name.replace('_', ' ')} group by category",
                "pipeline": f"db.{collection_name}.aggregate([{{ $group: {{ _id: '$sub_category', count: {{ $sum: 1 }} }} }}])",
                "explanation": "This pipeline groups documents by category and counts items in each group."
            },
            # 评分分组统计示例
            {
                "query": f"show average rating for {collection_name.replace('_', ' ')} group by category",
                "pipeline": f"db.{collection_name}.aggregate([{{ $group: {{ _id: '$sub_category', avg_rating: {{ $avg: {{ $toDouble: '$ratings' }} }} }} }}])",
                "explanation": "This pipeline calculates average rating for each category."
            },
            # 高评分商品分组统计
            {
                "query": f"show total number of {collection_name.replace('_', ' ')} with rating greater than 4 group by category",
                "pipeline": f"""db.{collection_name}.aggregate([
                    {{ $match: {{ ratings: {{ $gt: '4' }} }} }},
                    {{ $group: {{ _id: '$sub_category', count: {{ $sum: 1 }}, avg_rating: {{ $avg: {{ $toDouble: '$ratings' }} }} }} }}
                ])""",
                "explanation": "This pipeline groups high-rated products by category and shows their count and average rating."
            },
            # 热门商品分组统计
            {
                "query": f"show total number of {collection_name.replace('_', ' ')} with comments greater than 1000 group by category",
                "pipeline": f"""db.{collection_name}.aggregate([
                    {{ $match: {{ no_of_ratings: {{ $gt: '1000' }} }} }},
                    {{ $group: {{ _id: '$sub_category', count: {{ $sum: 1 }}, avg_comments: {{ $avg: {{ $toDouble: '$no_of_ratings' }} }} }} }}
                ])""",
                "explanation": "This pipeline groups popular products by category and shows their count and average reviews."
            },
            # 高评分且热门商品分组统计
            {
                "query": f"show total number of {collection_name.replace('_', ' ')} with rating greater than 4 and comments greater than 1000 group by category",
                "pipeline": f"""db.{collection_name}.aggregate([
                    {{ $match: {{ $and: [{{ ratings: {{ $gt: '4' }}, no_of_ratings: {{ $gt: '1000' }} }}] }} }},
                    {{ $group: {{ 
                        _id: '$sub_category', 
                        count: {{ $sum: 1 }},
                        avg_rating: {{ $avg: {{ $toDouble: '$ratings' }} }},
                        avg_comments: {{ $avg: {{ $toDouble: '$no_of_ratings' }} }}
                    }} }}
                ])""",
                "explanation": "This pipeline groups high-rated and popular products by category with detailed statistics."
            },
            # 主类别分组统计
            {
                "query": f"show total number of {collection_name.replace('_', ' ')} group by main category",
                "pipeline": f"db.{collection_name}.aggregate([{{ $group: {{ _id: '$main_category', count: {{ $sum: 1 }} }} }}])",
                "explanation": "This pipeline groups documents by main category and shows the distribution."
            },
            # 级联查询示例
            {
                "query": f"show me {collection_name.replace('_', ' ')} including air conditioners with rating greater than 4",
                "pipeline": f"""db.{collection_name}.aggregate([
                    {{ $lookup: {{ from: 'air_conditioners', localField: 'sub_category', foreignField: 'sub_category', as: 'related_products' }} }},
                    {{ $match: {{ ratings: {{ $gt: '4' }} }} }},
                    {{ $project: {{ name: 1, ratings: 1, no_of_ratings: 1, discount_price: 1, actual_price: 1, related_products: 1 }} }}
                ])""",
                "explanation": "This pipeline performs a lookup with air conditioners and filters by rating."
            },
            # 三表级联示例
            {
                "query": f"show me {collection_name.replace('_', ' ')} together with air conditioners connected to car and motorbike products",
                "pipeline": f"""db.{collection_name}.aggregate([
                    {{ $lookup: {{ from: 'air_conditioners', localField: 'sub_category', foreignField: 'sub_category', as: 'ac_products' }} }},
                    {{ $lookup: {{ from: 'all_car_and_motorbike_products', localField: 'main_category', foreignField: 'main_category', as: 'car_products' }} }},
                    {{ $project: {{ name: 1, ratings: 1, no_of_ratings: 1, discount_price: 1, actual_price: 1, ac_products: 1, car_products: 1 }} }}
                ])""",
                "explanation": "This pipeline performs a three-way lookup across all product categories."
            }
        ]
        
        # 根据当前查询类型选择相关示例
        relevant_examples = []
        current_query = collection_name.lower()
        
        if "rating" in current_query:
            relevant_examples.extend([ex for ex in examples if "rating" in ex["query"].lower()])
        if "comments" in current_query:
            relevant_examples.extend([ex for ex in examples if "comments" in ex["query"].lower()])
        if "group by" in current_query:
            relevant_examples.extend([ex for ex in examples if "group by" in ex["query"].lower()])
        if "including" in current_query or "together with" in current_query:
            relevant_examples.extend([ex for ex in examples if "lookup" in ex["pipeline"].lower()])
        
        # 如果没有找到相关示例，使用基础示例
        if not relevant_examples:
            relevant_examples = examples[:3]
        
        # 确保至少返回3个示例
        if len(relevant_examples) < 3:
            remaining = 3 - len(relevant_examples)
            relevant_examples.extend(random.sample([ex for ex in examples if ex not in relevant_examples], remaining))
        
        return random.sample(relevant_examples, 3)

    def get_mongo_query_string(self, collection_name, pipeline=None, condition=None):
        """Generate MongoDB query string"""
        if pipeline:
            # 聚合查询
            return f"db.{collection_name}.aggregate({str(pipeline)})"
        else:
            # 普通查询

            projection = "{ name: 1, ratings: 1, no_of_ratings: 1, discount_price: 1, actual_price: 1, _id: 0 }"
            if condition:
                return f"db.{collection_name}.find({condition}, {projection})"
            else:
                return f"db.{collection_name}.find({{}}, {projection})"

    def query(self, collection_name, condition=None, limit=5, group_by=None, aggregate=None, order_by=None):
        """
        Perform NoSQL query with optional filtering, grouping, and aggregation.
        """
        print(cf.header("QUERY EXECUTION"))

        # Get random examples
        examples = self.get_random_nosql_examples(collection_name)
        for i, example in enumerate(examples, 1):
            print(f"\n{cf.info(f'Example Query {i}:')}")
            print(example["query"])
            print(f"{cf.info('MongoDB Query:')}")
            print(cf.highlight(example["pipeline"]))
            print(f"{cf.info('Pipeline Explanation:')}")
            print(cf.highlight(example["explanation"]))

        # 当前查询
        print(f"\n{cf.info('Current Query:')}")
        
        # 构建查询条件
        query_dict = {}
        if condition:
            conditions = []
            
            # 解析评分条件
            if "'ratings'" in condition:
                rating_match = re.search(r"'ratings':\s*{\s*'\$gt':\s*'([\d.]+)'\s*}", condition)
                if rating_match:
                    conditions.append({"ratings": {"$gt": rating_match.group(1)}})
            
            # 解析评论数条件
            if "'no_of_ratings'" in condition:
                comments_match = re.search(r"'no_of_ratings':\s*{\s*'\$gt':\s*'(\d+)'\s*}", condition)
                if comments_match:
                    conditions.append({"no_of_ratings": {"$gt": comments_match.group(1)}})
            
            # 如果有多个条件，使用 $and
            if len(conditions) > 1:
                query_dict = {"$and": conditions}
            elif len(conditions) == 1:
                query_dict = conditions[0]
        
        # 构建查询字符串（用于显示）
        query_str = f"db.{collection_name}.find("
        if query_dict:
            # 格式化查询条件，使用更紧凑的格式
            if "$and" in query_dict:
                conditions = []
                for cond in query_dict["$and"]:
                    field = list(cond.keys())[0]
                    operator = list(cond[field].keys())[0]
                    value = cond[field][operator]
                    conditions.append(f"'{field}': {{'{operator}': '{value}'}}")
                formatted_query = "{\n    '$and': [{\n        " + "},\n        {".join(conditions) + "\n    }]"
                query_str += formatted_query + "}"
            else:
                field = list(query_dict.keys())[0]
                operator = list(query_dict[field].keys())[0]
                value = query_dict[field][operator]
                formatted_query = "{\n    " + f"'{field}': {{'{operator}': '{value}'}}" + "\n}"
                query_str += formatted_query
        else:
            query_str += "{}"
        
        # 添加投影，使用相同的格式化
        projection = {
            "name": 1,
            "ratings": 1,
            "no_of_ratings": 1,
            "discount_price": 1,
            "actual_price": 1,
            "_id": 0
        }
        formatted_projection = json.dumps(projection, indent=4).replace('"', "")
        query_str += ", " + formatted_projection
        
        if limit:
            query_str += f").limit({limit})"
        else:
            query_str += ")"

        print(f"\n{cf.info('MongoDB Query:')}")
        print(cf.highlight(query_str))

        # 构建管道或查询条件
        if group_by or aggregate:
            # 聚合查询
            pipeline = []
            
            # 添加匹配条件（如果有）
            if "rating greater than" in str(condition):
                match = re.search(r"ratings > ([\d.]+)", str(condition))
                if match:
                    rating_value = match.group(1)
                    pipeline.append({"$match": {"ratings": {"$gt": rating_value}}})
            
            # 添加分组阶段
            if group_by:
                group_stage = {
                    "_id": f"${group_by}",
                    "count": {"$sum": 1}
                }
                pipeline.append({"$group": group_stage})
            
            # 添加排序
            pipeline.append({"$sort": {"count": -1}})
            
            # 构建查询字符串
            query_str = f"db.{collection_name}.aggregate("
            formatted_pipeline = json.dumps(pipeline, indent=4).replace('"', '')
            query_str += formatted_pipeline + ")"
            
            print(f"\n{cf.info('MongoDB Query:')}")
            print(cf.highlight(query_str))
            
            print(f"{cf.info('Pipeline Explanation:')}")
            explanation = "This pipeline "
            if "rating greater than" in str(condition):
                explanation += "filters documents by rating, "
            explanation += f"groups them by {group_by} and counts documents in each group"
            print(cf.highlight(explanation + "."))

        else:
            # 普通查询
            # 显示完整的MongoDB find查询
            query_str = self.get_mongo_query_string(collection_name, condition=condition)
            if limit:
                query_str += f".limit({limit})"
            if order_by:
                # 将order_by转换为sort语法
                sort_field = list(order_by["$sort"].keys())[0]
                sort_order = list(order_by["$sort"].values())[0]
                query_str += f".sort({ {sort_field}: {sort_order} })"
            print(cf.highlight(query_str))
        
        print(f"{cf.info('Query Explanation:')}")
        explanation = "This query "
        if condition:
            explanation += "filters documents based on conditions"
        else:
            explanation += "retrieves all documents"
        if group_by:
            explanation += f", groups them by {group_by}"
        if aggregate:
            explanation += f" and performs {aggregate} aggregation"
        if order_by:
            explanation += ", applies sorting"
        if limit:
            explanation += f", and limits results to {limit} documents"
        print(cf.highlight(explanation + "."))

        # 添加执行确认
        execute = input(cf.info("\nDo you want to execute this query? (yes/no): ")).strip().lower()
        if execute != 'yes':
            print(cf.warning("Query execution cancelled."))
            return "cancelled"

        # 行查询并显示结果
        try:
            if group_by or aggregate:
                # 聚合查询
                results = list(self.db[collection_name].aggregate(pipeline))
                print(cf.success(f"\nFound {len(results)} groups"))
                print(cf.separator())
                for result in results:
                    if aggregate == "count":
                        print(cf.highlight(f"Category: {result['_id']}, Count: {result['count']}"))
                    elif aggregate == "AVG_RATING":
                        print(cf.highlight(f"Category: {result['_id']}, Average Rating: {result['average_rating']:.2f}"))
            else:
                # 普通查询
                try:
                    # 执行查询
                    projection = {
                        "name": 1,
                        "ratings": 1,
                        "no_of_ratings": 1,
                        "discount_price": 1,
                        "actual_price": 1,
                        "_id": 0
                    }
                    
                    # 解析查询条件
                    if condition and "$and" in condition:
                        # 处理多条件查询
                        conditions = []
                        if "'ratings'" in condition:
                            rating_match = re.search(r"'ratings':\s*{\s*'\$gt':\s*'([\d.]+)'\s*}", condition)
                            if rating_match:
                                conditions.append({"ratings": {"$gt": rating_match.group(1)}})
                        if "'no_of_ratings'" in condition:
                            comments_match = re.search(r"'no_of_ratings':\s*{\s*'\$gt':\s*'(\d+)'\s*}", condition)
                            if comments_match:
                                conditions.append({"no_of_ratings": {"$gt": comments_match.group(1)}})
                        query_dict = {"$and": conditions} if conditions else {}
                    else:
                        # 处理单条件查询
                        query_dict = eval(condition) if condition else {}
                    
                    # 执行查询
                    if limit:
                        results = list(self.db[collection_name].find(query_dict, projection).limit(limit))
                    else:
                        results = list(self.db[collection_name].find(query_dict, projection))


                    print(cf.success(f"\nFound {len(results)} documents"))
                    print(cf.separator())
                    for result in results:
                        formatted_result = {
                            "Name": result["name"][:50] + "..." if len(result["name"]) > 50 else result["name"],
                            "Rating": self.format_value(result["ratings"], "ratings"),
                            "Reviews": self.format_value(result["no_of_ratings"], "no_of_ratings"),
                            "Price": self.format_value(result["discount_price"], "discount_price"),
                            "Original": self.format_value(result["actual_price"], "actual_price")
                        }
                        print(cf.highlight(formatted_result))
                    print(cf.separator())

                except Exception as e:
                    print(cf.warning("\n抱歉，我的自然语言模型可能理解错了您的意思！您可以试试这些例子："))
                    print(cf.highlight("• show me appliances with rating greater than 4"))
                    print(cf.highlight("• show me air conditioners with comments greater than 1000"))
                    return "error"

        except Exception as e:
            print(cf.warning("\nSorry, my natural language model may have misunderstood you! You can try these examples"))
            if group_by:
                print(cf.highlight("• show total number of appliances group by category"))
                print(cf.highlight("• show average rating for air conditioners group by category"))
            else:
                print(cf.highlight("• show me appliances limit 10 records"))
                print(cf.highlight("• show me air conditioners with rating greater than 4"))
            return "error"

        # 修改交互选项
        print(f"\n{cf.info('What would you like to do next?')}")
        print(cf.highlight("1. Modify this query"))
        print(cf.highlight("2. Run a similar query"))
        print(cf.highlight("3. Show pipeline explanation again"))
        print(cf.highlight("4. Enter a new query"))
        print(cf.highlight("5. Return to main menu"))
        print(cf.highlight("6. Export query to JSON"))

        while True:
            choice = input(cf.info("\nEnter your choice (1-6): ")).strip()
            
            if choice == "1":
                print(cf.info("\nPlease enter your modified query:"))
                return "modify"
            elif choice == "2":
                template = f"show me {collection_name.replace('_', ' ')}"
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
                print(f"\n{cf.info('Pipeline Explanation:')}")
                print(cf.highlight(explanation + "."))
                continue
            elif choice == "4":
                print(cf.info("\nPlease enter your new query:"))
                return "new"
            elif choice == "5":
                return "exit"
            elif choice == "6":
                # 导出查询到JSON文件
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"query_{collection_name}_{timestamp}.json"
                
                # 创建导出数据
                export_data = {
                    "query_info": {
                        "collection": collection_name,
                        "condition": condition if condition else "None",
                        "group_by": group_by if group_by else "None",
                        "aggregate": aggregate if aggregate else "None",
                        "limit": limit
                    },
                    "mongodb_query": {
                        "pipeline": pipeline if 'pipeline' in locals() else [],
                        "explanation": explanation
                    }
                }
                
                # 写JSON文件
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                print(cf.success(f"\nQuery exported to {filename}"))
                continue
            else:
                print(cf.error("Invalid choice. Please enter a number between 1 and 6."))

        return "success"
