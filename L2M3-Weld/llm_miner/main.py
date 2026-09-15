"""Optional single-document helper; batch experiments use batch_l2m3.py."""
from llm_miner.agent import LLMMiner
from llm_miner.reader import JournalReader


def main(file_path: str, journal=None, *, llm):
    """Use an explicitly supplied LangChain model on the complete document."""
    reader = JournalReader.from_file(file_path, journal)
    if not reader.elements:
        raise ValueError('Parser found no elements')
    agent = LLMMiner.from_llm(llm, llm)
    agent.invoke({'paragraph': reader, 'token_checker': None})
    return reader
