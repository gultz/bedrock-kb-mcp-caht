import logging
import datetime
import sys
import os

from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import file_write
from botocore.config import Config
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


# chembl_mcp_client = MCPClient(lambda: stdio_client(
#     StdioServerParameters(command="node", args=["ChEMBL-MCP-Server/build/index.js"])
# ))


chembl_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="docker", args=["run", "-i", "chembl-mcp-server"])
))

uniprot_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="docker", args=["run", "-i", "uniprot-mcp-server"])
))


def run_chembl_agent(query: str) -> str:
    """
    chembl_agent를 실행하고 결과를 반환합니다.
    """
    try:
        with chembl_mcp_client as client:
            tools = client.list_tools_sync()
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


def run_uniprot_agent(query: str) -> str:
    """
    chembl_agent를 실행하고 결과를 반환합니다.
    """
    try:
        with uniprot_mcp_client as client:
            tools = client.list_tools_sync()
            system_prompt = """
            You are a specialized UniProt research agent. Your role is to:

            1. Understand and extract key biological entities or research intents from the input query.
            2. Use the appropriate UniProt tool to perform protein-level search, functional annotation, or structural data retrieval.
            3. Query the UniProt REST API using the correct endpoint based on the tool and context.
            4. Return well-structured and informative results, including protein names, UniProt IDs, gene symbols, functions, and associated annotations.
            5. If applicable, include links to UniProt entries and summary insights from comparative genomics or systems biology perspectives.

            You support 26 advanced bioinformatics tools designed for AI assistants and MCP clients. These tools allow deep protein analysis, sequence comparison, domain prediction, and pathway exploration directly through the UniProt knowledgebase.

            Always format results clearly and concisely for downstream consumption by LLMs or human users.
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
        logger.error(f"Error in uniprot_agent: {e}")
        return f"Error: {str(e)}"