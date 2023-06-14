#encoding: utf-8

from langchain.prompts import load_prompt
import yaml
import json


# with open('data/prompts/discuss/starter_prompt.yaml', encoding='utf-8') as file:
#     starter_prompt = file.read()

# with open('data/prompts/discuss/thought_prompt.yaml', 'r', encoding='utf-8') as f:
#     thought_prompt = yaml.load(f, Loader=yaml.FullLoader)

# with open('data/prompts/discuss/thought_prompt.json', 'w', encoding='latin-1') as f:
#     f.write(json.dumps(thought_prompt))

# with open('data/prompts/discuss/thought_prompt2.yaml', 'w', encoding='utf-8') as file:
#     file.write(thought_prompt)

# with open('data/prompts/discuss/response_prompt.yaml', encoding='utf-8') as file:
#     response_prompt = file.read()

# with open('data/prompts/discuss/thought_summary_prompt.yaml', encoding='utf-8') as file:
#     thought_summary_prompt = file.read()

# with open('data/prompts/discuss/response_summary_prompt.yaml', encoding='utf-8') as file:
#     response_summary_prompt = file.read()

DISCUSS_STARTER_PROMPT_TEMPLATE = load_prompt('data/prompts/discuss/starter_prompt.yaml')
DISCUSS_THOUGHT_PROMPT_TEMPLATE = load_prompt('data/prompts/discuss/thought_prompt3.yaml')
DISCUSS_RESPONSE_PROMPT_TEMPLATE = load_prompt('data/prompts/discuss/response_prompt2.yaml')
DISCUSS_THOUGHT_SUMMARY_TEMPLATE = load_prompt('data/prompts/discuss/thought_summary_prompt.yaml')
DISCUSS_RESPONSE_SUMMARY_TEMPLATE = load_prompt('data/prompts/discuss/response_summary_prompt.yaml')

print(DISCUSS_STARTER_PROMPT_TEMPLATE)
print(DISCUSS_THOUGHT_PROMPT_TEMPLATE)
print(DISCUSS_RESPONSE_PROMPT_TEMPLATE)
print(DISCUSS_THOUGHT_SUMMARY_TEMPLATE)
print(DISCUSS_RESPONSE_SUMMARY_TEMPLATE)