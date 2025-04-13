from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import logging
import sys
from datetime import datetime
import json

def get_datetime():
    now = datetime.now()
    return now.strftime("%m/%d/%Y, %H:%M:%S")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("output.log", mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

class StreamToLogger:
    def __init__(self, logger, log_level):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, message):
        message = message.strip()
        if message:
            self.logger.log(self.log_level, message)

    def flush(self):
        pass

sys.stdout = StreamToLogger(logging.getLogger("STDOUT"), logging.INFO)
sys.stderr = StreamToLogger(logging.getLogger("STDERR"), logging.ERROR)


load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

character_prompt_path = '../prompt/character_prompt'
crime_prompt_path = '../prompt/crime_prompt'
detail_prompt_path = '../prompt/detail_prompt'
alibi_prompt_path = '../prompt/alibi_prompt'

with open(character_prompt_path,'r', encoding="utf-8") as f:
    character_prompt = f.read()
with open(crime_prompt_path,'r', encoding="utf-8") as f:
    crime_prompt = f.read()
with open(detail_prompt_path,'r', encoding="utf-8") as f:
    detail_prompt = f.read()
with open(alibi_prompt_path,'r', encoding="utf-8") as f:
    alibi_prompt = f.read()

game_state = {
    "characters": [],
    "victim": None,
    "culprits": [],   # list of names
    "clues": [],
    "solution_explanation": ""
}

def character_generate(prompt, llm, n=4):
    section = {"이름":[], "특징":[], "성격":[]} #name, trait, personality in order
    for i in range(n):
        input = prompt.format(character_info={"이름":section["이름"], "특징":section["특징"]})
        output = llm.invoke(input)
        raw = output.content
        for part in raw.strip().split('\n\n'):
            if ':' in part:
                key, value = part.split(':', 1)
                section[key.strip()].append(value.strip())
    return section

def crime_generate(prompt, character_info, llm):
    section = {}
    input = prompt.format(character_info=character_info)
    output = llm.invoke(input)
    raw = output.content
    for part in raw.strip().split('\n\n'):
        if ':' in part:
            key, value = part.split(':', 1)
            section[key.strip()]=value.strip()
    return section

def detail_generate(prompt, character_info, crime, llm):
    section = {}
    input = prompt.format(character_info=character_info, crime=crime)
    output = llm.invoke(input)
    raw = output.content
    for part in raw.strip().split('\n\n'):
        if ':' in part:
            key, value = part.split(':', 1)
            section[key.strip()]=value.strip()
    return section

def alibi_generate(prompt, each_character_info, crime, llm):
    section = {}
    input = prompt.format(each_character_info=each_character_info, crime=crime) #each character_info
    output = llm.invoke(input)
    raw = output.content
    for part in raw.strip().split('\n\n'):
        if ':' in part:
            key, value = part.split(':', 1)
            section[key.strip()]=value.strip()
    return section

class Character:
    def __init__(self, name, trait, personality, detail, alibi):
        self.name = name
        self.trait = trait
        self.personality = personality
        self.detail = detail
        self.alibi = alibi
        # self.memory

game_state = {
    "characters": [],
    "victim": None,
    "culprits": [],   # list of names
    "clues": [],
    "solution_explanation": ""
}

people = int(4)
characters = [] #list of all characters

llm = ChatOpenAI(api_key = openai_api_key, model = "gpt-4o-mini", temperature=0.2)

characters_archive = [] #for saving token...
character_prompt = PromptTemplate.from_template(input_variable={"character_info"}, template=character_prompt)
character_info = character_generate(character_prompt, llm, n=people)
print(character_info)
crime_prompt = PromptTemplate.from_template(input_variable={"character_info"}, partial_variables={"date": get_datetime}, template=crime_prompt)
crime = crime_generate(crime_prompt, character_info, llm)
print(crime)
detail_prompt = PromptTemplate.from_template(input_variable={"character_info", "crime"}, template=detail_prompt)
detail = detail_generate(detail_prompt, character_info, crime, llm)
print(detail)
alibi_prompt = PromptTemplate.from_template(input_variable={"each_character_info", "crime"}, template=alibi_prompt)
for i in range(people):
    each_character_info = {}
    each_character_info["name"] = character_info["이름"][i]
    each_character_info["trait"] = character_info["특징"][i]
    each_character_info["personality"] = character_info["성격"][i]
    each_character_info["detail"] = detail[character_info["이름"][i]]
    each_character_info["alibi"] = alibi_generate(alibi_prompt, each_character_info, crime, llm)
    each_character = Character(**each_character_info)
    characters.append(each_character)
    characters_archive.append(each_character.__dict__)
characters_archive.append(crime)
with open("info.json",'w', encoding="utf-8") as f:
    json.dump(characters_archive, f, ensure_ascii=False, indent=2)



# class event():
#     def __init__(self):


# class game_env():