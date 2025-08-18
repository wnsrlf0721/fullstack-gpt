import streamlit as st
import json
from pathlib import Path
from langchain.retrievers import WikipediaRetriever 
from langchain.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.callbacks import StreamingStdOutCallbackHandler

st.set_page_config(
    page_title="QuizGPT",
    page_icon = "❓"
)

st.title("Quiz GPT")

function = {
    "name": "create_quiz",
    "description": "function that takes a list of questions and answers and returns a quiz",
    "parameters": {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                        },
                        "answers": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "answer": {
                                        "type": "string",
                                    },
                                    "correct": {
                                        "type": "boolean",
                                    },
                                },
                                "required": ["answer", "correct"],
                            },
                        },
                    },
                    "required": ["question", "answers"],
                },
            }
        },
        "required": ["questions"],
    },
}

llm = ChatOpenAI(
    temperature = 1,
    model="gpt-5-nano-2025-08-07",
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()],
).bind(
    function_call={"name": "create_quiz"},
    functions=[function],
)

prompt = PromptTemplate.from_template("""
    You are a helpful assistant that is role playing as a teacher.
                    
    Based ONLY on the following context make 4 questions to test the user's knowledge about the text.
    
    Each question should have 3 answers, two of them must be incorrect and one should be correct.

    Context: {context}
""")

def format_docs(docs):
    return "\n\n".join(document.page_content for document in docs)

@st.cache_data(show_spinner = "Loading file...")
def split_file(file):
    file_content = file.read()
    file_path = f"./.cache/quiz_files/{file.name}"
    Path("./.cache/quiz_files").mkdir(parents=True, exist_ok=True)
    with open(file_path, "wb+") as f:
        f.write(file_content)
    splitter =CharacterTextSplitter.from_tiktoken_encoder(
        separator="\n",
        chunk_size= 600,
        chunk_overlap= 100,
    )
    loader = UnstructuredFileLoader(file_path)
    docs = loader.load_and_split(text_splitter= splitter)
    return docs

@st.cache_data(show_spinner="Making quiz...")
def run_quiz_chain(_docs, topic):
    chain = {"context": format_docs} | prompt | llm
    response = chain.invoke(_docs)
    r = response.additional_kwargs["function_call"]["arguments"]
    return json.loads(r)

# Return docs about Wiki
@st.cache_data(show_spinner="Searching Wikipedia...")
def wiki_search(term):
    retriever = WikipediaRetriever(top_k_results=1)
    docs = retriever.get_relevant_documents(term)
    return docs

with st.sidebar:
    docs= None
    choice = st.selectbox("Choose what you want to use.", (
        "File","Wikipedia Article",
    ),)

    if choice =="File":
        file = st.file_uploader("Upload a .docx, .txt or .pdf file", 
        type=["pdf", "txt", "docx"],
        )
        if file:
            docs = split_file(file)
    else :
        topic = st.text_input("Search Wikipedia...")
        if topic:
            docs = wiki_search(topic)

if not docs:
    st.markdown("""
    Welcome to QuizGPT.

    I will make a quiz from Wikipedia articles or files you upload to test your knowledge and help you study.

    Get started by uploading a file or searching on Wikipedia in the sidebar.
    """)

else:
    response = run_quiz_chain(docs, topic if topic else file.name)
    with st.form("questions_form"):
        for question in response["questions"]:
            st.write(question["question"])
            value = st.radio("Select an option", [answer["answer"] for answer in question["answers"]],index=None)
            if {"answer": value, "correct": True} in question["answers"]:
                st.success("Correct!")
            elif value is not None:
                st.error("Wrong")
            
        button = st.form_submit_button()