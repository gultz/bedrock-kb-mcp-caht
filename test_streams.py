import asyncio
from strands import Agent
from strands_tools import calculator
import mcp_agent

# Initialize our agent without a import logging
import datetime
import sys
import os

from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import file_write
from botocore.config import Config
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters

# MCP 클라이언트 정의
chembl_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="docker", args=["run", "-i", "chembl-mcp-server"])
))

# Bedrock 모델 설정
model = BedrockModel(
    boto_client_config=Config(
        read_timeout=900,
        connect_timeout=900,
        retries=dict(max_attempts=3, mode="adaptive"),
    ),
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    max_tokens=5000,
    temperature=0.1,
    top_p=0.9,
)

# Async function that iterators over streamed agent events
async def process_streaming_response():
    # MCP 클라이언트를 with 문 안에서 사용
    with chembl_mcp_client as client:
        tools = client.list_tools_sync()
        
        agent = Agent(
            tools=tools,
            model=model,
            callback_handler=None
        )
        
        agent_stream = agent.stream_async("What is the mechanism of action of imatinib?")
        async for event in agent_stream:
            print(event)

# Run the agent
asyncio.run(process_streaming_response())