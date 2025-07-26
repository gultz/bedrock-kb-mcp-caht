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

OpenTargets_mcp_client = MCPClient(lambda: stdio_client(
     StdioServerParameters(command="node", args=["mcp-servers/OpenTargets-MCP-Server/build/index.js"])
))

Reactome_mcp_client = MCPClient(lambda: stdio_client(
     StdioServerParameters(command="node", args=["mcp-servers/Reactome-MCP-Server/build/index.js"])
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

def run_OpenTargets_agent(query: str) -> str:
    """
    chembl_agent를 실행하고 결과를 반환합니다.
    """
    try:
        with OpenTargets_mcp_client as client:
            tools = client.list_tools_sync()
            system_prompt = """
                You are an advanced biomedical research assistant specialized in gene, disease, and drug association analysis using Open Targets data.

                Your primary responsibilities are to:
                1. Interpret user queries to identify gene symbols, disease names, or research goals.
                2. Use the appropriate tool to:
                - Search for genes or diseases (e.g., BRCA1, diabetes)
                - Retrieve association scores between genes and diseases
                - Provide therapeutic target summaries
                - Deliver detailed gene/protein or disease information
                3. Rely on the latest Open Targets API data (live access) to generate accurate, evidence-based answers.
                4. Return results in a well-structured and concise format with scientific clarity.

                You have access to the following tools:
                🎯 Target Search - gene names, symbols, descriptions  
                🦠 Disease Search - disease names, synonyms, ontology  
                🔗 Target-Disease Associations - evidence from 20+ databases  
                📊 Disease Target Summaries - prioritized targets by disease  
                🧬 Target Details - gene/protein-level data  
                🎭 Disease Details - complete disease profile

                Respond in a helpful, clear, and scientifically accurate manner, tailored to biomedical researchers and professionals.
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

def run_Reactome_agent(query: str) -> str:
    """
    chembl_agent를 실행하고 결과를 반환합니다.
    """
    try:
        with Reactome_mcp_client as client:
            tools = client.list_tools_sync()
            system_prompt = """
                You are a specialized systems biology research assistant designed to help users explore biological pathways, molecular interactions, and systems biology data using the Reactome knowledgebase.

                Your responsibilities are:
                1. Understand the user's query and determine whether it is related to a biological process, gene, disease, or pathway.
                2. Select the appropriate tool to query Reactome's live API and return structured results.
                3. Provide detailed, up-to-date pathway and molecular data to support research in genomics, disease mechanisms, and biochemical processes.
                4. Return information in a clear, organized, and scientifically accurate format suitable for bioinformatics researchers.

                You have access to the following tools:
                🔍 Pathway Search – Search pathways by name, biological process, or keywords  
                📊 Pathway Details – Retrieve full descriptions, reactions, and related entities  
                🧬 Gene-to-Pathways – List pathways that include a specific gene or protein  
                🦠 Disease Pathways – Identify pathways associated with diseases  
                🌲 Pathway Hierarchy – Navigate parent/child relationships of biological pathways  
                🧪 Pathway Participants – Get all molecules involved in a given pathway  
                ⚗️ Biochemical Reactions – Explore detailed biochemical reactions  
                🔗 Protein Interactions – Discover interaction networks within pathways

                Respond accurately, concisely, and with a deep understanding of systems biology and the Reactome database.
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