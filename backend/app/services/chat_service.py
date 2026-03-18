from langchain_community.agent_toolkits import SQLDatabaseToolkit, create_sql_agent
from langchain_core.tools import tool
from app.core.llm.qwen import ChatQwen
from app.core.db.database import get_sql_database
from typing import Any, AsyncGenerator
import json

@tool
def render_echarts_chart(echarts_option_json: str) -> str:
    """
    Use this tool to render an ECharts chart.
    Pass a valid ECharts option JSON string as the argument.
    The JSON must be a valid ECharts option object, for example:
    {"title": {"text": "Sales"}, "xAxis": {"type": "category", "data": ["A", "B"]}, "yAxis": {"type": "value"}, "series": [{"data": [10, 20], "type": "bar"}]}
    Call this tool when the user asks for a chart, graph, or visual representation of the data.
    """
    return "Chart configuration successfully sent to the frontend for rendering."

class NL2SQLService:
    def __init__(self):
        self.db = get_sql_database()
        self.llm = ChatQwen(temperature=0) # temperature=0 for deterministic SQL
        self.init_agent()

    def init_agent(self):
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.tools = self.toolkit.get_tools()
        
        # custom instructions for charting
        custom_prefix = """You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct MySQL query to run, then look at the results of the query and return the answer.
Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 10 results.
You can order the results by a relevant column to return the most interesting examples in the database.
Never query for all the columns from a specific table, only ask for the relevant columns given the question.
You have access to tools for interacting with the database.
Only use the below tools. Only use the information returned by the below tools to construct your final answer.
You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

IMPORTANT: You must always respond in the exact same language as the user's input. For example, if the user asks a question in Chinese, your response must be entirely in Chinese."""

        custom_suffix = """If the user requests a visualization, chart, or graph, you MUST use the render_echarts_chart tool to generate a valid ECharts option JSON based on the data you queried. 
Do not write the JSON in your final answer, just use the tool.
DO NOT output any image URLs or markdown image links.
DO NOT try to draw the chart using text or base64 strings.
After calling the tool, simply tell the user that the chart has been generated and displayed on the right panel.

Remember: ALWAYS respond in the SAME LANGUAGE as the user's original input."""

        # create_sql_agent handles prompt and tools automatically.
        self.agent_executor = create_sql_agent(
            llm=self.llm,
            toolkit=self.toolkit,
            verbose=True,
            agent_type="tool-calling", # or "openai-tools" or "zero-shot-react-description"
            handle_parsing_errors=True,
            extra_tools=[render_echarts_chart],
            prefix=custom_prefix,
            suffix=custom_suffix
        )

    def reload_db(self):
        """Reload database connection and re-initialize agent."""
        self.db = get_sql_database()
        self.init_agent()

    async def chat_stream(self, question: str, session_id: str) -> AsyncGenerator[str, None]:
        """
        Stream the agent execution.
        This will yield tokens/events.
        We need to adapt this to the SSE format defined in the plan:
        status, delta, sql, chart_spec, final
        """
        try:
            # We use astream_events to get granular updates
            async for event in self.agent_executor.astream_events(
                {"input": question},
                version="v2"
            ):
                kind = event["event"]
                
                # Yield thinking status when LLM starts
                if kind == "on_chat_model_start":
                    yield f"data: {json.dumps({'status': 'thinking'})}\n\n"
                    
                # Stream the text response chunks
                elif kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        yield f"data: {json.dumps({'status': 'answer', 'delta': content})}\n\n"
                
                # Yield sql/query status when a tool is called
                elif kind == "on_tool_start":
                    tool_name = event["name"]
                    if tool_name == "sql_db_query":
                        sql_query = event["data"].get("input", {}).get("query", "")
                        yield f"data: {json.dumps({'status': 'sql', 'sql': sql_query})}\n\n"
                        yield f"data: {json.dumps({'status': 'query'})}\n\n"
                    elif tool_name in ["sql_db_list_tables", "sql_db_schema"]:
                        yield f"data: {json.dumps({'status': 'thinking'})}\n\n"
                    elif tool_name == "render_echarts_chart":
                        try:
                            # Extract the JSON string from tool args
                            option_str = event["data"].get("input", {}).get("echarts_option_json", "{}")
                            # It might be passed as a direct dict or a JSON string
                            if isinstance(option_str, str):
                                chart_spec = json.loads(option_str)
                            else:
                                chart_spec = option_str
                            yield f"data: {json.dumps({'status': 'chart', 'chart_spec': chart_spec})}\n\n"
                        except Exception as e:
                            import logging
                            logging.getLogger(__name__).error(f"Error parsing chart spec: {e}, input was: {event['data']}")
                            pass
                
                # Catch tool output for raw data display
                elif kind == "on_tool_end":
                    tool_name = event["name"]
                    if tool_name == "sql_db_query":
                        # Output is usually a string representation of a list of tuples or list of dicts
                        tool_output = event["data"].get("output", "")
                        try:
                            # Safely eval the string if it looks like a list
                            import ast
                            if isinstance(tool_output, str) and tool_output.strip().startswith("["):
                                raw_data = ast.literal_eval(tool_output)
                                # Send raw data to frontend for visualization window
                                yield f"data: {json.dumps({'status': 'data', 'data': raw_data})}\n\n"
                        except Exception as e:
                            import logging
                            logging.getLogger(__name__).warning(f"Could not parse sql_db_query output for data table: {e}")
                            pass
                
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'delta': str(e)})}\n\n"
        
import json
