from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_teddynote import logging
logging.langsmith("VirtualGameEnv")
import os

openai_api_key = os.environ('OPENAI_API_KEY')

generate_prompt_path = '../prompt/generate_prompt'

with open(generate_prompt_path,'r') as f:
    generate_prompt = f.read()

prompt = PromptTemplate(
    template=generate_prompt
)

game_state = {
    "characters": [],
    "victim": None,
    "culprits": [],   # list of names
    "clues": [],
    "solution_explanation": ""
}


def character_generate(prompt):
    input = prompt
    llm = ChatOpenAI(api_key = openai_api_key, model = "gpt-4o-mini")
    llm.invoke(input)

class Character:
    def __init__(self, name, traits, personality, alibi, secret):
        self.name = name
        self.traits = traits        # superficial description
        self.personality = personality  # deeper details or motive
        self.alibi = alibi          # what they'll claim
        self.secret = secret        # e.g. "Culprit" or other hidden info

game_state = {
    "characters": [],
    "victim": None,
    "culprits": [],   # list of names
    "clues": [],
    "solution_explanation": ""
}

# class event():
#     def __init__(self):


# class game_env():
