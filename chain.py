import os
import validators
import pickle

from langchain.chat_models import ChatOpenAI
from langchain import LLMChain
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.prompts import load_prompt

from dotenv import load_dotenv

load_dotenv()

# with open('data/prompts/discuss/starter_prompt.yaml', encoding='utf-8') as file:
#     starter_prompt = file.read()

# with open('data/prompts/discuss/thought_prompt.yaml', 'r', encoding='latin-1') as file:
#     thought_prompt = file.read()

# with open('data/prompts/discuss/thought_prompt2.yaml', 'w', encoding='utf-8') as file:
#     file.write(thought_prompt)

# with open('data/prompts/discuss/response_prompt.yaml', encoding='utf-8') as file:
#     response_prompt = file.read()

# with open('data/prompts/discuss/thought_summary_prompt.yaml', encoding='utf-8') as file:
#     thought_summary_prompt = file.read()

# with open('data/prompts/discuss/response_summary_prompt.yaml', encoding='utf-8') as file:
#     response_summary_prompt = file.read()

DISCUSS_STARTER_PROMPT_TEMPLATE = load_prompt('data/prompts/discuss/starter_prompt.yaml')
DISCUSS_THOUGHT_PROMPT_TEMPLATE = load_prompt('data/prompts/discuss/thought_prompt.yaml')
DISCUSS_RESPONSE_PROMPT_TEMPLATE = load_prompt('data/prompts/discuss/response_prompt.yaml')
DISCUSS_THOUGHT_SUMMARY_TEMPLATE = load_prompt('data/prompts/discuss/thought_summary_prompt.yaml')
DISCUSS_RESPONSE_SUMMARY_TEMPLATE = load_prompt('data/prompts/discuss/response_summary_prompt.yaml')


def load_memories(conversation_type: str = "discuss"):
    """Load the memory objects"""
    llm = ChatOpenAI() # type: ignore
    thought_defaults = {
        "llm":llm,
        "memory_key":"history",
        "input_key":"input",
        "ai_prefix":"Thought",
        "human_prefix":"Student",
        "max_token_limit":900
    }
    response_defaults = {
        "llm":llm,
        "memory_key":"history",
        "input_key":"input",
        "ai_prefix":"Tutor",
        "human_prefix":"Student",
        "max_token_limit":900
    }
    thought_memory: ConversationSummaryBufferMemory
    response_memory: ConversationSummaryBufferMemory
    # memory definitions
    if conversation_type == "discuss":
        thought_memory = ConversationSummaryBufferMemory(
            prompt=DISCUSS_THOUGHT_SUMMARY_TEMPLATE,
            **thought_defaults
        )

        response_memory = ConversationSummaryBufferMemory(
            prompt=DISCUSS_RESPONSE_SUMMARY_TEMPLATE,
            **response_defaults
        )

    return (thought_memory, response_memory)


def load_chains():
    """Logic for loading the chain you want to use should go here."""
    llm = ChatOpenAI(max_tokens=170)

    # chatGPT prompt formatting
    discuss_starter_message_prompt = HumanMessagePromptTemplate(prompt=DISCUSS_STARTER_PROMPT_TEMPLATE)
    discuss_thought_message_prompt = HumanMessagePromptTemplate(prompt=DISCUSS_THOUGHT_PROMPT_TEMPLATE)
    discuss_response_message_prompt = HumanMessagePromptTemplate(prompt=DISCUSS_RESPONSE_PROMPT_TEMPLATE)
    discuss_response_summary_message_prompt = HumanMessagePromptTemplate(prompt=DISCUSS_RESPONSE_SUMMARY_TEMPLATE)
    discuss_thought_summary_message_prompt = HumanMessagePromptTemplate(prompt=DISCUSS_THOUGHT_SUMMARY_TEMPLATE)

    discuss_starter_chat_prompt = ChatPromptTemplate.from_messages([discuss_starter_message_prompt])
    discuss_thought_chat_prompt = ChatPromptTemplate.from_messages([discuss_thought_message_prompt])
    discuss_response_chat_prompt = ChatPromptTemplate.from_messages([discuss_response_message_prompt])
    discuss_response_summary_chat_prompt = ChatPromptTemplate.from_messages([discuss_response_summary_message_prompt])
    discuss_thought_summary_chat_prompt = ChatPromptTemplate.from_messages([discuss_thought_summary_message_prompt])


    # define chains
    discuss_starter_chain = LLMChain(
        llm=llm,
        prompt=discuss_starter_chat_prompt,
        verbose=False
    )

    discuss_thought_chain = LLMChain(
        llm=llm,
        prompt=discuss_thought_chat_prompt,
        verbose=False
    )

    discuss_response_chain = LLMChain(
        llm=llm,
        prompt=discuss_response_chat_prompt,
        verbose=False
    )

    discuss_response_summary_chain = LLMChain(
        llm=llm,
        prompt=discuss_response_summary_chat_prompt,
        verbose=True
    )

    discuss_thought_summary_chain = LLMChain(
        llm=llm,
        prompt=discuss_thought_summary_chat_prompt,
        verbose=True
    )

    return (
        discuss_starter_chain, 
        discuss_thought_chain, 
        discuss_response_chain,
        discuss_response_summary_chain,
        discuss_thought_summary_chain
    )


async def chat(**kwargs):
    # if there's no input, generate a starter
    if kwargs.get('inp') is None:
        assert kwargs.get('starter_chain'), "Please pass the starter chain."
        starter_chain = kwargs.get('starter_chain')
        context = kwargs.get('context')

        # get number of tokens contained in given context
        starter_tokens = starter_chain.llm.get_num_tokens(context)

        # provided context can't take up more than 386 tokens (see notes on 2023-03-22)
        if starter_tokens > 386:
            return "Sorry, I can't handle a context of that length yet, but I can work through it with you if you break it into smaller pieces!\n\n If you feel ready to move on at any time, just give me the next piece by using the `/context` command."
        # check it's not a URL either
        # if validators.url(context):
        #     return "Sorry, I can't scrape content from URLs yet. Please copy + paste a few paragraphs of text after the `/context` command!"
            

        response = starter_chain.predict(
            context=context
        )

        return response

    # if we sent a thought across, generate a response
    if kwargs.get('thought'):
        assert kwargs.get('response_chain'), "Please pass the response chain."
        response_chain = kwargs.get('response_chain')
        response_memory = kwargs.get('response_memory')
        context = kwargs.get('context')
        inp = kwargs.get('inp')
        thought = kwargs.get('thought')

        # # get the history into a string
        # with open('memories/response.pkl', 'rb') as file:
        #     unpickler = pickle.Unpickler(file)
        #     response_pickle = unpickler.load()
        # history = response_pickle
        history = response_memory.memory.moving_summary_buffer

        response = await response_chain.apredict(
            context=context,
            input=inp,
            thought=thought,
            history=history
        )
        if 'Student:' in response:
            response = response.split('Student:')[0].strip()
        if 'Studen:' in response:
            response = response.split('Studen:')[0].strip()

        return response

    # otherwise, we're generating a thought
    else:
        assert kwargs.get('thought_chain'), "Please pass the thought chain."
        inp = kwargs.get('inp')
        thought_chain = kwargs.get('thought_chain')
        thought_memory = kwargs.get('thought_memory')
        context = kwargs.get('context')

        # # get the history into a string
        history = thought_memory.memory.moving_summary_buffer
        # with open('memories/thought.pkl', 'rb') as file:
        #     unpickler = pickle.Unpickler(file)
        #     thought_pickle = unpickler.load()
        # history = thought_pickle
        response = await thought_chain.apredict(
            context=context,
            input=inp,
            history=history
        )

        if 'Tutor:' in response:
            response = response.split('Tutor:')[0].strip()

        return response


class ConversationCache:
    "Wrapper Class for storing contexts between channels. Using an object to pass by reference avoid additional cache hits"
    def __init__(self, context=None, conversation_type="discuss"):
        
        self.thought_memory, self.response_memory = load_memories(conversation_type)
        self.context = context
        self.conversation_type = conversation_type


    # def restart(self):
    #    self.thought_memory.clear()
    #    self.response_memory.clear()
    #    self.context = None
    #    self.convo_type = None
