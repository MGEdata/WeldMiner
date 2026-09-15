"""Validated public configuration; goals retain their original workflow meanings."""
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, SecretStr

NODES = ('extract_skeleton', 'check_skeleton', 'extract_global_dim', 'extract_fact_table')

class ModelConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    provider: Literal['qwen', 'deepseek', 'google'] = 'qwen'
    model: str = 'qwen3.7-max'
    api_key: SecretStr | None = Field(default=None, exclude=True, repr=False)
    base_url: str | None = None
    temperature: float = 0.0
    enable_reasoning: bool = True
    max_tokens: int = Field(default=65536, gt=0)

class ExtractionConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    material_user_goal: list[str] = Field(default_factory=lambda: [
        'hardness', 'tensile strength', 'yield strength', 'elongation',
        'Charpy impact test temperature', 'impact energy'])
    material_direct_goal: list[str] = Field(default_factory=list)
    sample_user_goal: list[str] = Field(default_factory=lambda: [
        'hardness', 'stretching rate', 'tensile strength', 'yield strength',
        'elongation', 'Charpy impact test temperature', 'impact energy'])
    sample_direct_goal: list[str] = Field(default_factory=list)
    llm: ModelConfig = Field(default_factory=ModelConfig)
    node_llms: dict[str, ModelConfig] = Field(default_factory=dict)
    export_csv: bool = True
    export_excel: bool = True

    @classmethod
    def from_file(cls, path: str | Path):
        return cls.model_validate_json(Path(path).read_text(encoding='utf-8-sig'))

