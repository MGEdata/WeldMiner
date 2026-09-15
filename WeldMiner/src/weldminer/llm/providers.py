"""Create provider clients only when an extraction is requested."""
import os
from ..config import ExtractionConfig, ModelConfig, NODES

def create_llm(config: ModelConfig):
    key = config.api_key.get_secret_value() if config.api_key else None
    if config.provider == 'qwen':
        if config.base_url:
            raise ValueError('Qwen uses ChatTongyi/DashScope; omit base_url (not an OpenAI-compatible endpoint)')
        from langchain_community.chat_models import ChatTongyi
        return ChatTongyi(model_name=config.model, api_key=key or os.getenv('QWEN_API_KEY'),
            model_kwargs={'temperature': config.temperature, 'max_tokens': config.max_tokens,
                          'enable_thinking': config.enable_reasoning})
    if config.provider == 'deepseek':
        from langchain_deepseek import ChatDeepSeek
        return ChatDeepSeek(model_name=config.model, api_key=key or os.getenv('DEEPSEEK_API_KEY'),
            base_url=config.base_url or os.getenv('DEEPSEEK_API_BASE_URL') or 'https://api.deepseek.com', temperature=config.temperature,
            max_tokens=config.max_tokens,
            extra_body={'thinking': {'type': 'enabled' if config.enable_reasoning else 'disabled'}})
    from langchain_google_genai import ChatGoogleGenerativeAI
    base_url = config.base_url or os.getenv('GOOGLE_API_BASE_URL')
    endpoint_options = {}
    if base_url:
        if 'base_url' in ChatGoogleGenerativeAI.model_fields:
            endpoint_options['base_url'] = base_url
        else:
            # Older Google clients use a host-only API endpoint.
            from urllib.parse import urlsplit
            endpoint = urlsplit(base_url if '://' in base_url else 'https://' + base_url)
            if endpoint.path not in ('', '/') or endpoint.query or endpoint.fragment:
                raise ValueError('This Google client requires a host-only endpoint; upgrade langchain-google-genai for custom URL paths')
            endpoint_options['client_options'] = {'api_endpoint': endpoint.netloc}
    # Preserve the original adapter behavior: no explicit Google thinking settings.
    return ChatGoogleGenerativeAI(model=config.model, api_key=key or os.getenv('GOOGLE_API_KEY'),
                                 temperature=config.temperature, max_tokens=config.max_tokens,
                                 **endpoint_options)

def create_node_llms(config: ExtractionConfig):
    unknown = set(config.node_llms) - set(NODES)
    if unknown:
        raise ValueError(f'Unknown workflow nodes: {sorted(unknown)}')
    return {node: create_llm(config.node_llms.get(node, config.llm)) for node in NODES}
