import sqlite3
import os
import json
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit

# 1. Create a dummy SQLite DB for testing
DB_PATH = "test_data.db"
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER,
        department TEXT
    )
''')
cursor.execute('''
    CREATE TABLE sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        sale_date DATE,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')

# Insert some dummy data
cursor.executemany('INSERT INTO users (name, age, department) VALUES (?, ?, ?)', [
    ('Alice', 28, 'Sales'),
    ('Bob', 35, 'Engineering'),
    ('Charlie', 32, 'Sales')
])
cursor.executemany('INSERT INTO sales (user_id, amount, sale_date) VALUES (?, ?, ?)', [
    (1, 1500.50, '2023-10-01'),
    (1, 2000.00, '2023-10-15'),
    (3, 800.75, '2023-10-05')
])
conn.commit()
conn.close()

# 2. Initialize SQLDatabase and Toolkit
db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")

# Note: We pass a mock LLM or None just to inspect the tools.
# The tools themselves don't always need the LLM unless it's the QueryChecker.
# For schema and query execution, the LLM is not strictly necessary for instantiation if we only want to test the tool's run function.
# However, SQLDatabaseToolkit requires an LLM for QuerySQLCheckerTool.
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from typing import Any, List, Optional
class MockLLM(BaseChatModel):
    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs: Any) -> Any:
        pass
    @property
    def _llm_type(self) -> str:
        return "mock"

mock_llm = MockLLM()
toolkit = SQLDatabaseToolkit(db=db, llm=mock_llm)
tools = toolkit.get_tools()

print("=== Available Tools in SQLDatabaseToolkit ===")
tool_map = {t.name: t for t in tools}
for t in tools:
    print(f"- Name: {t.name}")
    print(f"  Description: {t.description}")
    print(f"  Args Schema: {t.args_schema.schema() if t.args_schema else 'None'}\n")

# 3. Test Tool Invocations to observe Input/Output formats
print("\n=== Testing sql_db_list_tables ===")
list_tool = tool_map['sql_db_list_tables']
# Input is usually empty string or dict
res_list = list_tool.invoke("")
print(f"Input: ''")
print(f"Output type: {type(res_list)}")
print(f"Output content:\n{res_list}\n")

print("\n=== Testing sql_db_schema ===")
schema_tool = tool_map['sql_db_schema']
# The schema says it expects a comma-separated list of tables as a string in `table_names`
schema_input = {"table_names": "users, sales"}
res_schema = schema_tool.invoke(schema_input)
print(f"Input: {schema_input}")
print(f"Output type: {type(res_schema)}")
print(f"Output content:\n{res_schema}\n")

print("\n=== Testing sql_db_query ===")
query_tool = tool_map['sql_db_query']
# Input expects a detailed and correct SQL query in `query`
query_input = {"query": "SELECT name, amount FROM users JOIN sales ON users.id = sales.user_id WHERE users.department = 'Sales'"}
res_query = query_tool.invoke(query_input)
print(f"Input: {query_input}")
print(f"Output type: {type(res_query)}")
print(f"Output content:\n{res_query}\n")

# Test query tool with intentional error
print("\n=== Testing sql_db_query (Error Case) ===")
bad_query_input = {"query": "SELECT name, amount FROM non_existent_table"}
res_bad_query = query_tool.invoke(bad_query_input)
print(f"Input: {bad_query_input}")
print(f"Output type: {type(res_bad_query)}")
print(f"Output content:\n{res_bad_query}\n")

# Clean up
os.remove(DB_PATH)
