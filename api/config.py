import yaml
from typing import TypedDict
from langchain.chat_models import init_chat_model
from pathlib import Path

class ConfigSchema(TypedDict):
    model: str

MODELS = {
    "low": init_chat_model("openai:gpt-4.1-mini", temperature=0.0),
    "high": init_chat_model("openai:o3"),
}

# Load prompts from YAML
_PROMPTS_FILE = Path(__file__).parent.parent / "agents" / "prompts.yaml"
with open(_PROMPTS_FILE, 'r') as f:
    _prompts_data = yaml.safe_load(f)

def get_prompt(prompt_name: str) -> str:
    if prompt_name not in _prompts_data:
        raise ValueError(f"Prompt {prompt_name} not found in {_PROMPTS_FILE}")
    return _prompts_data[prompt_name]