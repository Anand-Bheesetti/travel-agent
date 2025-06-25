import streamlit as st
from workflow import app
from langchain_core.messages import HumanMessage
from services.markdown_exporter import MarkdownExporter
import datetime

st.set_page_config(page_title="AI Travel Agent", page_icon="✈️")
st.title("AI Travel Agent ✈️")

if "chat_history" not in st.session_state:
  st.session_state.chat_history = []

# Chat display
for msg in st.session_state.chat_history:
  if msg["role"] == "user":
    st.chat_message("user").write(msg["content"])
  else:
    st.chat_message("assistant").write(msg["content"])

# User input
user_input = st.chat_input("Where do you want to travel?")
if user_input:
  st.session_state.chat_history.append({"role": "user", "content": user_input})
  messages = [
    HumanMessage(content=m["content"]) if m["role"] == "user" else None
    for m in st.session_state.chat_history
  ]
  messages = [m for m in messages if m is not None]

  # Run the workflow
  with st.status("Agent reasoning (all steps shown below):", expanded=True) as status:
    final = None
    for event in app.stream({"messages": messages}):
      if "messages" not in event:
        continue  # Skip events without messages
      step_msgs = event["messages"]
      for m in step_msgs:
        # Show tool calls
        if hasattr(m, "tool_calls") and m.tool_calls:
          for call in m.tool_calls:
            st.write(f"**Tool Call:** {call['name']}({call['args']})")
        # Show LLM thoughts
        elif getattr(m, "type", None) == "ai":
          st.write(f"**LLM Thought:** {m.content}")
        # Show tool outputs
        elif getattr(m, "type", None) == "tool":
          st.write(f"**Tool Output:** {m.content}")
        else:
          st.write(f"**Message:** {m.content}")
      final = step_msgs[-1].content if step_msgs else None
    if final:
      st.session_state.chat_history.append({"role": "assistant", "content": final})
      st.chat_message("assistant").write(final)
      # Save markdown after each conversation
      exporter = MarkdownExporter()
      timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
      filename = f"travel_convo_{timestamp}.md"
      # Build markdown content: all messages + final output
      md_content = "\n".join([
        f"**{msg['role'].capitalize()}:** {msg['content']}" for msg in st.session_state.chat_history
      ])
      exporter.export(md_content, filename=filename)
    status.update(label="Agent finished", state="complete")
