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


chembl_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="docker", args=["run", "-i", "chembl-mcp-server"])
))
chembl_agent_tools = chembl_mcp_client.list_tools_sync()

agent = Agent(
    tools=chembl_agent_tools,
    callback_handler=None
)

# Async function that iterators over streamed agent events
async def process_streaming_response():
    agent_stream = agent.stream_async("What is the mechanism of action of imatinib?")
    async for event in agent_stream:
        print(event)

# Run the agent
asyncio.run(process_streaming_response())