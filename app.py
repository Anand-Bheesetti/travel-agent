import streamlit as st
import uuid
from workflow import TravelWorkflow

# from services import QueryAnalyzer # etc.
# from models import TripPlan
# from langgraph.graph import StateGraph, END

st.title("AI Travel Agent")

# Initialize workflow and session state
if "workflow" not in st.session_state:
  st.session_state.workflow = TravelWorkflow()
if "messages" not in st.session_state:
  st.session_state.messages = []
if "thread_id" not in st.session_state:
  st.session_state.thread_id = str(uuid.uuid4())

# Display chat history
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

# Handle user input
if prompt := st.chat_input("Where do you want to go?"):
  st.session_state.messages.append({"role": "user", "content": prompt})
  with st.chat_message("user"):
    st.markdown(prompt)

  with st.chat_message("assistant"):
    message_placeholder = st.empty()
    full_response = ""

    # Run the workflow and stream the response
    workflow = st.session_state.workflow
    thread_id = st.session_state.thread_id
    events = workflow.run(prompt, thread_id)

    for event in events:
      # The event stream contains different types of data
      # We're interested in the messages from the 'query_analyzer' node
      if "messages" in event.get("query_analyzer", {}):
        response_messages = event["query_analyzer"]["messages"]
        for message in response_messages:
          full_response += message.content
          message_placeholder.markdown(full_response + "▌")

    message_placeholder.markdown(full_response)
  st.session_state.messages.append({"role": "assistant", "content": full_response})
