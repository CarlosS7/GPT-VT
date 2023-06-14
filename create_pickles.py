from langchain.memory import ConversationSummaryBufferMemory
from langchain.chat_models import ChatOpenAI 
import pickle

llm = ChatOpenAI()

conversation = ConversationSummaryBufferMemory(llm=llm, max_token_limit=10)
conversation.save_context({"input": "hi"}, {"output": "whats up"})
conversation.save_context({"input": "not much you"}, {"output": "not much"})

with open('memories/thought.pkl', 'wb') as file:
    pickle.dump(conversation.load_memory_variables({}), file)

with open('memories/response.pkl', 'wb') as file:
    pickle.dump(conversation.load_memory_variables({}), file)