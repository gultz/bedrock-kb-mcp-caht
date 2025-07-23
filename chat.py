#import traceback
#import uuid
import logging
import datetime
import sys
#import asyncio
import os

#from botocore.config import Config
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import file_write
from botocore.config import Config
# from strands.agent.conversationmanager import SlidingWindowConversationManager
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
from strands.agent.conversation_manager import SlidingWindowConversationManager

logging.basicConfig(
    level=logging.INFO,  # Defaulx t to INFO level
    format='%(filename)s:%(lineno)d | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("chat")

# model_name = "Claude 3.7 Sonnet"
# model_type = "claude"
# debug_mode = "Enable"
# model_id = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
# models = info.get_model_info(model_name)
# reasoning_mode = 'Disable'


model = BedrockModel(
    boto_client_config=Config(
        read_timeout=900,
        connect_timeout=900,
        retries=dict(max_attempts=3, mode="adaptive"),
    ),
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    max_tokens=64000,
    stop_sequences=["\n\nHuman:"],
    temperature=0.1,
    top_p=0.9,
    additional_request_fields={
        "thinking": {
            "type": "disabled"
        }
    }
)

conversation_manager = SlidingWindowConversationManager(
    window_size=10,  
)


chembl_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="node", args=["ChEMBL-MCP-Server/build/index.js"])
))


def run_chembl_agent(query: str) -> str:
    """
    chembl_agent를 실행하고 결과를 반환합니다.
    """
    try:
        with chembl_mcp_client as client:
            all_tools = client.list_tools_sync()
            tools = [all_tools[0], all_tools[1]]
            system_prompt = """
        You are a specialized ChEMBL research agent. Your role is to:
        1. Extract either the compound name or target name from the query
        2. Search ChEMBL with the name
        3. Return structured, well-formatted compound information with SMILES and activity information for the name
        """
            agent = Agent(
                tools=tools,
                system_prompt=system_prompt,
                conversation_manager=conversation_manager,
                model=model
            )
            response = agent(query)
            return str(response)
    except Exception as e:
        logger.error(f"Error in chembl_agent: {e}")
        return f"Error: {str(e)}"