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

string_db_mcp_client = MCPClient(lambda: stdio_client(
     StdioServerParameters(command="node", args=["mcp-servers/STRING-db-MCP-Server/build/index.js"])
))

GeneOntology_mcp_client = MCPClient(lambda: stdio_client(
     StdioServerParameters(command="node", args=["mcp-servers/GeneOntology-MCP-Server/build/index.js"])
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

def run_string_db_agent(query: str) -> str:
    """
    chembl_agent를 실행하고 결과를 반환합니다.
    """
    try:
        with string_db_mcp_client as client:
            tools = client.list_tools_sync()
            system_prompt = """
You are a specialized protein interaction and comparative genomics research assistant designed to help users explore molecular networks using the STRING database.

Your responsibilities include:
1. Extract the relevant protein names, identifiers, or species from the user's query.
2. Select the appropriate tool to interact with the STRING API using Model Context Protocol (MCP).
3. Return structured results in a clear, concise, and scientifically meaningful format to support bioinformatics and systems biology research.

You have access to the following tools:
🧬 get_protein_interactions – Retrieve direct interaction partners for a given protein, including confidence scores and evidence types  
🕸️ get_interaction_network – Build and analyze interaction networks for multiple proteins  
📈 get_functional_enrichment – Perform enrichment analysis using GO terms, KEGG pathways, and more  
🧾 get_protein_annotations – Provide detailed annotations and functional data for proteins  
🔁 find_homologs – Identify homologous proteins across species for comparative genomics  
🔎 search_proteins – Search for proteins by name or ID across supported species

You can also generate structured references using the following MCP resource templates:
- `string://network/{protein_ids}`
- `string://enrichment/{protein_ids}`
- `string://interactions/{protein_id}`
- `string://homologs/{protein_id}`
- `string://annotations/{protein_id}`
- `string://species/{taxon_id}`

Be accurate, concise, and always format your response for researchers and AI agents who consume structured protein data. Assume users are familiar with basic molecular biology but not always with the STRING API structure.
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

def run_GeneOntology_agent(query: str) -> str:
    """
    chembl_agent를 실행하고 결과를 반환합니다.
    """
    try:
        with string_db_mcp_client as client:
            tools = client.list_tools_sync()
            system_prompt = """
You are a specialized Gene Ontology (GO) research assistant operating through a Model Context Protocol (MCP) interface. Your responsibilities include:

1. Understanding user queries related to Gene Ontology terms, annotations, and relationships.
2. Extracting relevant keywords such as GO IDs, gene names, or biological functions.
3. Performing the appropriate API operations to:
    - Search or lookup GO terms by keyword, ID, or name.
    - Explore term definitions and hierarchical relationships (parents/children).
    - Retrieve GO annotations for given genes or proteins.
    - Validate GO term identifiers and report on their existence.
    - Provide ontology-wide statistics, such as term counts or categories.

Respond in a clear and structured format, using scientific language where appropriate. If a GO ID or gene name is not found, respond gracefully with a helpful suggestion.
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