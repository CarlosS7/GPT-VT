import os
import asyncio
import globals
import markdown
import streamlit as st
from streamlit_chat import message as st_message
from typing import Tuple
from dotenv import load_dotenv
from streamlit_app_utils import process_summarize_button, load_db_from_file_and_create_if_not_exists, validate_api_key
from chat_utils import qa_from_db
from langchain.chat_models import ChatOpenAI

from summary_utils import transcript_loader
from langchain.prompts import load_prompt
from langchain.memory import ConversationSummaryBufferMemory
from chain import ConversationCache

import pandas as pd
import pickle



globals.init()


load_dotenv('.env')





st.set_page_config(page_title='VirtualTutor')

def documents():
    st.title('Training Subject Selection')
    #st.markdown('Documents are stored in the documents folder in the project directory.')
    directory = 'documents'
    files = os.listdir(directory)
    file_names = [file.split('.')[0] for file in files if file.endswith('.pdf')]
    material = st.radio(
        "Please choose your subject",
        file_names
    )

    if st.button('Select'):

        st.write('You selected: ' + material)
        selected_file_path = os.path.join(directory, material+'.pdf')
        st.spinner('Preparing the material for the tutoring session...')

        st.write("Summary of the Material:")

        if not os.path.exists(f'summaries/{material}_summary.txt'):
            process_summarize_button(selected_file_path, use_gpt_4=False, find_clusters=True)
        else:
            f = open(f'summaries/{material}_summary.txt')
            htmlmarkdown = markdown.markdown(f.read())
            st.markdown(htmlmarkdown, unsafe_allow_html=True)

        @st.cache_data
        def run_first_comment(material_name: str):
            with open(f'summaries/{material_name}_summary.txt') as f:
                lines = f.readlines()
                    
                starter_chain = globals.DISCUSS_STARTER_CHAIN
                starter_response = starter_chain.predict(
                        context=lines
                    )
            
            
            return starter_response
        
        initial_message = run_first_comment(material_name=material)

        if 'initial_message' not in st.session_state:
                st.session_state['initial_message'] = initial_message

        db = load_db_from_file_and_create_if_not_exists(selected_file_path)
        st.session_state.db = db
        st.session_state.message_history = []

        st.success('Done! You can now navigate to the Tutor Session page')

def tutor() -> Tuple[str, str]:
    st.title('Tutor Session')

    async def chat_and_save(local_chain: ConversationCache):

        
        # thought_memory.save_context({"input":'Initial input message'}, {"output": 'Initial thought'})
        # response_memory.save_context({"input": 'Inittial input message'}, {"output": 'Initial response'})

        if 'text_input' not in st.session_state:
            st.session_state.text_input = ''

        if 'initial_message' not in st.session_state:
            st.session_state.initial_message = ''
        else:
            st.write(st.session_state.initial_message)

        input = st.text_input('Write your input', key='text_input')

        #thought_memory, response_memory = load_memories('discuss')
        thought_chain =  globals.DISCUSS_THOUGHT_CHAIN
        response_chain = globals.DISCUSS_RESPONSE_CHAIN
        thought_memory_chain = globals.DISCUSS_THOUGHT_SUMMARY_TEMPLATE
        response_memory_chain = globals.DISCUSS_RESPONSE_SUMMARY_TEMPLATE
        
        @st.cache_data
        def predict_initial_thought_and_response():
            global thought_history, response_history
            thought_history = thought_memory_chain.predict(new_lines="Hi!", summary="Hello!")
            response_history = response_memory_chain.predict(new_lines="Hi!", summary="Hello!")
            return thought_history, response_history
        
        thought_history, response_history = predict_initial_thought_and_response()



        if st.button('Send') and 'db' in st.session_state:
            

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
                    history = response_memory

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
                    history = thought_memory
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

            db = st.session_state.db
            context = qa_from_db(input, db)
            # get the history into a string
            # history = thought_memory.load_memory_variables({})['history']
            thought = await chat(
                    context=context,
                    inp=input,
                    thought_chain=thought_chain,
                    thought_memory=thought_history
                )
            # global response
            # get the history into a string
            #history = response_memory.load_memory_variables({})['history']
            response = await chat(
                    context=context,
                    inp=input,
                    thought=thought,
                    response_chain=response_chain,
                    response_memory=response_history
                )
            
            if 'thought_list' not in st.session_state:
                st.session_state.thought_list = []

            if 'response_list' not in st.session_state:
                st.session_state.response_list = []

            st.session_state.thought_list += " Student: "+input + " Thought: "+thought
            st.session_state.response_list += " Student: "+input + " Tutor: "+response
            

            
            #local_chain.thought_memory.save_context({"input":"Starter"}, {"output": st.session_state.initial_message})
            thought_history = thought_memory_chain.predict(new_lines=input, summary=('').join(st.session_state.thought_list))
            response_history = response_memory_chain.predict(new_lines=input, summary=('').join(st.session_state.response_list))
            #st_message(response)
            # with open('memories/thought.pkl', 'wb') as file:
            #     pickle.dump(local_chain.thought_memory.load_memory_variables({})['history'], file)

            # with open('memories/response.pkl', 'wb') as file:
            #     pickle.dump(local_chain.response_memory.load_memory_variables({})['history'], file)

            
            st.session_state.message_history.append({'message': input, 'is_user': True})
            st.session_state.message_history.append({'message': response, 'is_user': False})

            if 'message_history' not in st.session_state:
                st.session_state.message_history = []
            for i, message_ in enumerate(st.session_state.message_history):
                st_message(**message_, key=str(i))
            # print(thought)
            # print(response)
        #return thought, response
    def main():
        asyncio.run(chat_and_save(ConversationCache()))

    if __name__ == '__main__':
        main()
    




PAGES = {
    "Material Selection": documents,
    "Tutor Session": tutor
}

st.sidebar.title("Navigation")
selection = st.sidebar.radio("-", list(PAGES.keys()))
page = PAGES[selection]
page()
