import re
from console_utils import ConsoleFormatter as cf

# 添加同义词映射
SHOW_SYNONYMS = {
    "show": "show",
    "display": "show",
    "list": "show",
    "find": "show",
    "get": "show",
    "search": "show",
    "give": "show",
    "tell": "show",
    "fetch": "show",
    "retrieve": "show"
}

def normalize_command(question):
    """Normalize command by replacing synonyms"""
    words = question.lower().split()
    if words and words[0] in SHOW_SYNONYMS:
        words[0] = SHOW_SYNONYMS[words[0]]
    return " ".join(words)

def get_similar_queries(table_name, error_type):
    """Get similar query suggestions based on error type"""
    suggestions = {
        "rating": [
            f"show me {table_name.replace('_', ' ')} with rating greater than 4",
            f"show me {table_name.replace('_', ' ')} with rating greater than 4.5 limit 10 records",
            f"show total number of {table_name.replace('_', ' ')} with rating greater than 4 group by category"
        ],
        "price": [
            f"show me {table_name.replace('_', ' ')} with price greater than 5000",
            f"show me {table_name.replace('_', ' ')} with price between 1000 and 5000",
            f"show me {table_name.replace('_', ' ')} in ascending price"
        ],
        "comments": [
            f"show me {table_name.replace('_', ' ')} with comments greater than 1000",
            f"show me {table_name.replace('_', ' ')} with comments greater than 5000 limit 10 records",
            f"show total number of {table_name.replace('_', ' ')} with comments greater than 1000 group by category"
        ],
        "discount": [
            f"show me {table_name.replace('_', ' ')} with discount greater than 30",
            f"show me {table_name.replace('_', ' ')} with discount greater than 25 in descending price",
            f"show average discount for {table_name.replace('_', ' ')}"
        ],
        "join": [
            f"show me {table_name.replace('_', ' ')} related to appliances",
            f"show me {table_name.replace('_', ' ')} including air conditioners",
            f"show me {table_name.replace('_', ' ')} together with appliances connected to car and motorbike products"
        ],
        "group": [
            f"show total number of {table_name.replace('_', ' ')} group by category",
            f"show average rating for {table_name.replace('_', ' ')} group by category",
            f"show total number of {table_name.replace('_', ' ')} with rating greater than 4 group by category"
        ]
    }
    return suggestions.get(error_type, [])

def parse_natural_language(question, db_type):
    """Parse a natural language question into query parameters"""
    try:

        normalized_question = normalize_command(question)
        
        table_map = {
            "air conditioners": "air_conditioners",
            "appliances": "all_appliances",
            "car and motorbike products": "all_car_and_motorbike_products",
        }

        table_name = None
        condition = None
        order_by = None
        limit = None
        group_by = None
        aggregate = None
        join_table = None
        join_type = None
        join_condition = None

        # Table detection
        for key, value in table_map.items():
            if key in normalized_question.lower():
                table_name = value
                break

        if not table_name:
            raise ValueError("Could not identify the table from the question")

        # Condition detection
        conditions = []

        # Rating condition

        if "rating greater than" in normalized_question.lower():
            match = re.search(r"rating greater than (\d+\.?\d*)", normalized_question.lower())
            if match:
                rating_value = match.group(1)
                if db_type == "sql":
                    conditions.append(f"ratings > {rating_value}")
                else:
                    conditions.append(f"{{'ratings': {{'$gt': '{rating_value}'}}}}")

        # Comments condition
        if "comments greater than" in normalized_question.lower():
            match = re.search(r"comments greater than (\d+)", normalized_question.lower())
            if match:
                comments_value = match.group(1)
                if db_type == "sql":
                    conditions.append(f"no_of_ratings > {comments_value}")
                else:
                    conditions.append(f"{{'no_of_ratings': {{'$gt': '{comments_value}'}}}}")

        # Price condition。
        if "price greater than" in normalized_question.lower():
            match = re.search(r"price greater than (\d+)", normalized_question.lower())
            if match:
                price_value = match.group(1)
                if db_type == "sql":
                    conditions.append(f"CAST(REPLACE(REPLACE(discount_price, '₹', ''), ',', '') AS DECIMAL) > {price_value}")
                else:
                    conditions.append(f"{{'$expr': {{'$gt': [{{'$toDouble': {{'$replaceAll': {{'input': {{'$replaceAll': {{'input': '$discount_price', 'find': '₹', 'replacement': ''}}, 'find': ',', 'replacement': ''}}}}}}, {price_value}]}}}}")

        # Price range condition
        if "price between" in normalized_question.lower():
            match = re.search(r"price between (\d+) and (\d+)", normalized_question.lower())
            if match:
                min_price, max_price = match.group(1), match.group(2)
                if db_type == "sql":
                    price_field = "CAST(REPLACE(REPLACE(discount_price, '₹', ''), ',', '') AS DECIMAL)"
                    conditions.append(f"{price_field} BETWEEN {min_price} AND {max_price}")
                else:
                    conditions.append(f"{{'$expr': {{'$and': [{{'$gte': [{{'$toDouble': {{'$replaceAll': {{'input': {{'$replaceAll': {{'input': '$discount_price', 'find': '₹', 'replacement': ''}}, 'find': ',', 'replacement': ''}}}}}}, {min_price}]}}, {{'$lte': [{{'$toDouble': {{'$replaceAll': {{'input': {{'$replaceAll': {{'input': '$discount_price', 'find': '₹', 'replacement': ''}}, 'find': ',', 'replacement': ''}}}}}}, {max_price}]}}]}}}}")

        # Combine conditions
        if conditions:
            if db_type == "sql":
                condition = " AND ".join(conditions)
            else:
                condition = f"{{'$and': [" + ", ".join(conditions) + "]}"

        # Sorting
        if "ascending price" in normalized_question.lower():
            if db_type == "sql":
                order_by = "CAST(REPLACE(REPLACE(discount_price, '₹', ''), ',', '') AS DECIMAL) ASC"
            else:
                order_by = {"$sort": {"numeric_price": 1}}
        elif "descending price" in normalized_question.lower():
            if db_type == "sql":
                order_by = "CAST(REPLACE(REPLACE(discount_price, '₹', ''), ',', '') AS DECIMAL) DESC"
            else:
                order_by = {"$sort": {"numeric_price": -1}}

        # Grouping
        if "group by category" in normalized_question.lower():
            group_by = "sub_category"
            
            # 检测平均评分
            if "average rating" in normalized_question.lower():
                aggregate = "AVG(CAST(ratings AS DECIMAL(10,2)))"
                # 移除默认的 limit
                limit = None
            elif "total number" in normalized_question.lower():
                aggregate = "COUNT(*)"
                # 移除默认的 limit
                limit = None
            
            # 检测是否有条件
            if "with rating greater than" in normalized_question.lower():
                match = re.search(r"rating greater than (\d+\.?\d*)", normalized_question.lower())
                if match:
                    rating_value = match.group(1)
                    condition = f"ratings > {rating_value}"

        # Join detection
        join_keywords = {
            "related to": "INNER JOIN",
            "matching": "INNER JOIN",
            "combined with": "INNER JOIN",
            "including": "LEFT JOIN",
            "along with": "LEFT JOIN",
            "with all": "LEFT JOIN"
        }

        # Three-table join keywords
        three_table_keywords = {
            "together with": "INNER JOIN",
            "connected to": "INNER JOIN"
        }

        # 检测三表连接
        if "together with" in normalized_question.lower() and "connected to" in normalized_question.lower():
            join_tables = []
            for key, value in table_map.items():
                if key in normalized_question.lower() and value != table_name:
                    join_tables.append(value)
            
            if len(join_tables) == 2:  # 确保找到了两个要连接的表
                join_table = ",".join(join_tables)
                join_type = "INNER JOIN"
                join_condition = f"""ON t1.sub_category = t2.sub_category 
                    INNER JOIN {join_tables[1]} t3 
                    ON t1.main_category = t3.main_category"""
            else:
                print(cf.warning("\nThree-table join requires exactly two additional tables."))
                print(cf.info("Example: show me appliances together with air conditioners connected to car and motorbike products"))
                raise ValueError("Invalid three-table join syntax")
        else:
            # 检测两表连接
            for keyword, join_operation in join_keywords.items():
                if keyword in normalized_question.lower():
                    for key, value in table_map.items():
                        if key in normalized_question.lower() and value != table_name:
                            join_table = value
                            join_type = join_operation
                            if "sub_category" in str(table_name):
                                join_condition = f"ON {table_name}.sub_category = {join_table}.sub_category"
                            else:
                                join_condition = f"ON {table_name}.main_category = {join_table}.main_category"
                            break
                    break

        # 只有在明确指定时才设置 limit
        match = re.search(r"limit (\d+) records", normalized_question.lower())
        if match:
            limit = int(match.group(1))

        return table_name, condition, order_by, limit, group_by, aggregate, join_table, join_type, join_condition

    except Exception as e:
        if "table" in str(e).lower():
            print(cf.warning("\nAvailable categories:"))
            print(cf.highlight("• air conditioners"))
            print(cf.highlight("• appliances"))
            print(cf.highlight("• car and motorbike products"))
        raise e
