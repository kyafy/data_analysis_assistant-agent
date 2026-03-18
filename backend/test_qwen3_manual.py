import os
import json
import dashscope
from http import HTTPStatus
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    print("Error: DASHSCOPE_API_KEY not found in environment.")
    exit(1)

dashscope.api_key = api_key

def test_qwen3_streaming_with_tools():
    print("\n=== Testing Qwen3-Max with Streaming & Tools ===")
    
    # Define a simple tool
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location"],
                },
            },
        }
    ]

    messages = [
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': 'What is the weather like in Beijing?'}
    ]

    print(f"User Query: {messages[-1]['content']}")
    print("-" * 50)

    try:
        # Use 'qwen-max' as user's 'qwen3-max' is likely mapped to the latest max model in DashScope
        # If user explicitly wants to test 'qwen-max-latest' or specific version, change here.
        # But for now let's stick to 'qwen-max' which is the standard identifier.
        model_name = 'qwen-max' 
        print(f"Testing Model: {model_name}")

        responses = dashscope.Generation.call(
            model=model_name,
            messages=messages,
            result_format='message',
            stream=True,
            incremental_output=True,
            tools=tools
        )
        
        full_content = ""
        tool_calls_chunks = []

        print("\nStreaming Response Chunks:")
        for response in responses:
            if response.status_code == HTTPStatus.OK:
                # Print the raw chunk for analysis
                # print(f"Raw Chunk: {json.dumps(response.output, ensure_ascii=False)}")
                
                output = response.output
                choices = output.choices
                if choices:
                    choice = choices[0]
                    delta = choice.message
                    
                    # Handle content
                    if 'content' in delta and delta.content:
                        print(f"[Content Delta]: {delta.content}")
                        full_content += delta.content
                    
                    # Handle tool calls
                    if 'tool_calls' in delta and delta.tool_calls:
                        print(f"[Tool Call Delta]: {delta.tool_calls}")
                        tool_calls_chunks.append(delta.tool_calls)
                        
                    if choice.finish_reason:
                         print(f"[Finish Reason]: {choice.finish_reason}")

            else:
                print('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
                    response.request_id, response.status_code,
                    response.code, response.message
                ))

        print("-" * 50)
        print(f"Full Content Reconstructed: {full_content}")
        print(f"Tool Calls Chunks: {tool_calls_chunks}")

    except Exception as e:
        print(f"Error calling DashScope: {e}")

if __name__ == '__main__':
    test_qwen3_streaming_with_tools()
