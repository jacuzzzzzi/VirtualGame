from langchain_core.prompts import PromptTemplate
from langchain.chains.llm import LLMChain 
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from pathlib import Path
import logging
import sys
from datetime import datetime
import json
import argparse
import ast

def parse_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument('--info_path',    type=str,   default='info.json')
    parser.add_argument('--refine_info_path',     type=str,   default='refine_info.json')
    parser.add_argument('--people',     type=int,   default=5)
    parser.add_argument('--max_ver',     type=int,   default=3)
    parser.add_argument('--recycle',    type=bool,    help="about whether to use the info already made")
    parser.add_argument('--refine',    type=bool,   help="about whether to refine the info")
    parser.add_argument('--remake',    type=bool,   help="about whether to remake the entire crime")
    parser.add_argument('--fake',    type=bool,   help="about whether to make the fake alibi of the crimer")
    return parser.parse_args()


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

def relation_generate(prompt, character_info, crime, llm):
    section = {}
    input = prompt.format(character_info=character_info, crime=crime)
    output = llm.invoke(input)
    raw = output.content
    for part in raw.strip().split('\n\n'):
        if ':' in part:
            key, value = part.split(':', 1)
            section[key.strip()]=value.strip()
    relation = [section[k] for k in character_info["이름"] if k in section]
    return relation

def secret_generate(prompt, character_info, crime, llm):
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

def fake_alibi_generate(prompt, each_character_info, crime, llm):
    section = {}
    input = prompt.format(each_character_info=each_character_info, crime=crime) #each character_info
    output = llm.invoke(input)
    raw = output.content
    for part in raw.strip().split('\n\n'):
        if ':' in part:
            key, value = part.split(':', 1)
            section[key.strip()]=value.strip()
    return section

def refine_generate(refine_info_path, refine_prompt, remake_prompt, adapt_prompt, info, llm, max_ver, remake):
    ver = 1
    while ver <= max_ver:
        if remake and ver==1:
            input = remake_prompt.format(info=info)
            feedback = llm.invoke(input)
        else:
            input = refine_prompt.format(info=info)
            feedback = llm.invoke(input)
        print(feedback.content)
        print(f"{ver}번째 수정")
        input = adapt_prompt.format(info=info, feedback=feedback)
        output = llm.invoke(input)
        print(output.content)
        raw = output.content.split("info:")[-1]
        try:
            info = ast.literal_eval(raw)
        except:
            info = ast.literal_eval(raw[:-1])
        ver += 1
        with open(refine_info_path,'w', encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
    return info

class Character:
    def __init__(self, name, trait, personality, relation, secret, alibi):
        self.name = name
        self.trait = trait
        self.personality = personality
        self.relation = relation
        self.secret = secret
        self.alibi = alibi
        self.fake_alibi = None
        self.prompt = None
        self.em_prompt = None
        self.memory = ConversationBufferMemory(memory_key="history", input_key="input", return_messages=True)
        self.chain = None

    def get_info(self):
        return {"name":self.name, "trait":self.trait, "personality":self.personality, "relation":self.relation, "secret":self.secret, "alibi":self.alibi, "fake_alibi":self.fake_alibi}

def begin(info_path, character_prompt, crime_prompt, relation_prompt, secret_prompt, alibi_prompt, llm, people=4) -> list:
    characters_archive = [] #for saving token...
    character_prompt = PromptTemplate.from_template(input_variable={"character_info"}, template=character_prompt)
    character_info = character_generate(character_prompt, llm, n=people)
    print(character_info)

    crime_prompt = PromptTemplate.from_template(input_variable={"character_info"}, partial_variables={"date": get_datetime}, template=crime_prompt)
    crime = crime_generate(crime_prompt, character_info, llm)
    print(crime)

    relation_prompt = PromptTemplate.from_template(input_variable={"character_info", "crime"}, template=relation_prompt)
    relation = relation_generate(relation_prompt, character_info, crime, llm)
    print(relation)
    character_info["관계"] = relation

    secret_prompt = PromptTemplate.from_template(input_variable={"character_info", "crime"}, template=secret_prompt)
    secret = secret_generate(secret_prompt, character_info, crime, llm)
    print(secret)

    alibi_prompt = PromptTemplate.from_template(input_variable={"each_character_info", "crime"}, template=alibi_prompt)

    for i in range(people):
        each_character_info = {}
        each_character_info["name"] = character_info["이름"][i]
        each_character_info["trait"] = character_info["특징"][i]
        each_character_info["personality"] = character_info["성격"][i]
        each_character_info["relation"] = character_info["관계"][i]
        each_character_info["secret"] = secret[character_info["이름"][i]]
        each_character_info["alibi"] = alibi_generate(alibi_prompt, each_character_info, crime, llm)
        characters_archive.append(each_character_info)
    characters_archive.append(crime)
    with open(info_path,'w', encoding="utf-8") as f:
        json.dump(characters_archive, f, ensure_ascii=False, indent=2)
    return characters_archive

def refine(info, refine_info_path, refine_prompt, remake_prompt, adapt_prompt, llm, max_ver, remake) -> list:
    refine_prompt = PromptTemplate.from_template(input_variable={"info"}, template=refine_prompt)
    remake_prompt = PromptTemplate.from_template(input_variable={"info"}, template=remake_prompt)
    adapt_prompt = PromptTemplate.from_template(input_variable={"info", "feedback"}, template=adapt_prompt)
    refine_info = refine_generate(refine_info_path, refine_prompt, remake_prompt, adapt_prompt, info, llm, max_ver, remake)
    return refine_info

def each_character_generate(info):
    for i in range(len(info)-1):
        each_character = Character(**info[i])
        each_character.prompt = PromptTemplate.from_template(input_variable={"each_character_info", "crime", "history", "input"}, template=each_character_prompt)
        each_character.em_prompt = PromptTemplate.from_template(input_variable={"each_character_info", "crime", "history", "input", "response"}, template=em_prompt)
        each_character.chain = LLMChain(
            llm=character_llm,
            memory=each_character.memory,
            prompt=each_character.prompt)
        characters[each_character.name]=each_character

class Chatting():
    def __init__(self, crime, suspects, criminal):
        self.log = []
        self.crime = crime
        self.suspects = suspects
        self.criminal = criminal
    
    def talk(self, *args):
        name, input = args
        try:
            if name == "범인":
                if input == self.criminal:
                    "정답입니다."
            if name in self.suspects:
                self.log.append({
                "speaker": "나",
                "target": name,
                "message": input
                })
                response = characters[name].chain.invoke({"each_character_info": characters[name].get_info(), "crime":self.crime, "input":input})["text"]
                if "<EM>" in response: #Emergency
                    characters[name].chain.memory.chat_memory.messages.pop()
                    characters[name].chain.prompt = characters[name].em_prompt
                    em_response = characters[name].chain.invoke({"each_character_info": characters[name].get_info(), "crime":self.crime, "input":input, "response":response})["text"] 
                    characters[name].chain.prompt = characters[name].prompt
                    response = em_response.split(":")[-1]
                self.log.append({
                "speaker": name,
                "target": "나",
                "message": response
                })
                return response
        except:
            pass
        return False

BASE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = BASE_DIR.parent / 'prompt'

#prompt path and load
character_prompt_path = PROMPT_DIR / 'character_prompt'
crime_prompt_path = PROMPT_DIR / 'crime_prompt'
secret_prompt_path = PROMPT_DIR / 'secret_prompt'
relation_prompt_path = PROMPT_DIR / 'relation_prompt'
alibi_prompt_path = PROMPT_DIR / 'alibi_prompt'
fake_alibi_prompt_path = PROMPT_DIR / 'fake_alibi_prompt'
refine_prompt_path = PROMPT_DIR / 'refine_prompt'
remake_prompt_path = PROMPT_DIR / 'remake_prompt'
adapt_prompt_path = PROMPT_DIR / 'adapt_prompt'
each_character_prompt_path = PROMPT_DIR / 'each_character_prompt'
em_prompt_path = PROMPT_DIR / 'em_prompt'

with open(character_prompt_path,'r', encoding="utf-8") as f:
    character_prompt = f.read()
with open(crime_prompt_path,'r', encoding="utf-8") as f:
    crime_prompt = f.read()
with open(relation_prompt_path,'r', encoding="utf-8") as f:
    relation_prompt = f.read()
with open(secret_prompt_path,'r', encoding="utf-8") as f:
    secret_prompt = f.read()
with open(alibi_prompt_path,'r', encoding="utf-8") as f:
    alibi_prompt = f.read()
with open(fake_alibi_prompt_path,'r', encoding="utf-8") as f:
    fake_alibi_prompt = f.read()
with open(refine_prompt_path,'r', encoding="utf-8") as f:
    refine_prompt = f.read()
with open(remake_prompt_path,'r', encoding="utf-8") as f:
    remake_prompt = f.read()
with open(adapt_prompt_path,'r', encoding="utf-8") as f:
    adapt_prompt = f.read()
with open(each_character_prompt_path,'r', encoding="utf-8") as f:
    each_character_prompt = f.read()
with open(em_prompt_path,'r', encoding="utf-8") as f:
    em_prompt = f.read()

characters = {} #dict of all characters

llm = ChatOpenAI(api_key = openai_api_key, model = "gpt-4o-mini", temperature=0.2)
character_llm = ChatOpenAI(api_key = openai_api_key, model = "gpt-4o-mini", temperature=1.0)


if __name__ == "__main__":
    args = parse_arg()
    info_path = BASE_DIR / args.info_path
    refine_info_path = BASE_DIR / args.refine_info_path
    if args.recycle:
        with open(info_path, "r", encoding="utf-8") as f:
            info = json.load(f)
    else:
        info = begin(info_path, character_prompt, crime_prompt, relation_prompt, secret_prompt, alibi_prompt, llm, args.people)  

    if args.refine:
        refine_info = refine(info, refine_info_path, refine_prompt, remake_prompt, adapt_prompt, llm, args.max_ver, args.remake)
        with open(refine_info_path,'w', encoding="utf-8") as f:
            json.dump(refine_info, f, ensure_ascii=False, indent=2)