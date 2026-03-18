from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit
from langchain_core.tools import tool

@tool
def render_echarts_chart(echarts_option_json: str) -> str:
    """Use this tool to render an ECharts chart."""
    return "Chart rendered successfully."

# print the signature of create_sql_agent
import inspect
print(inspect.signature(create_sql_agent))
