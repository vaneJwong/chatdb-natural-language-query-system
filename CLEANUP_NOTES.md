# 整理记录

## 目录判断

- `no_sql_chat/`：代码更新时间最晚，结构完整，并已有 README；选为公开仓库主版本。
- `Project1.1/`：更早的 ChatDB 原型，包含三套 MySQL 示例数据、MongoDB 示例、旧代码和课程说明；不与主版本混合。
- `demo01/`：单独的 JSON/MapReduce 实验，包含大量临时运行结果；与 ChatDB 主项目无直接代码关系。

## 已保留

- 程序入口与 SQL、NoSQL 查询逻辑
- 自然语言解析逻辑
- 控制台格式化代码
- 查询示例

## 已排除

- `.DS_Store`、`.idea/`、`__pycache__/` 和 `*.pyc`
- `out_put_data/` 等生成结果
- `Project1.1/old_code/` 和空的 `import.py`
- 课程作业 PDF
- 许可状态尚未确认的第三方 CSV 数据

## 安全处理

原代码中的 MySQL 密码已经从公开副本中移除。数据库地址、用户名、密码和数据库名现在通过环境变量配置；`.env` 已加入 `.gitignore`。

## 原目录中的重复项

`Project1.1/reviews.json` 与
`Project1.1/mongodb datasets/mongodb_dataset1/Orders/reviews.json` 内容完全相同。其余主要目录之间没有发现相同的项目代码文件。
