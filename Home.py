import streamlit as st

st.set_page_config(
    page_title="FullstackGPT Home",
    page_icon="👌",
)

st.title("FullstackGPT Home")

tab_one, tab_two, tab_three = st.tabs(["A","B","C"])
with tab_one:
    st.write("a")
with tab_two:
    st.write("b") 
with tab_three:
    st.write("c")   