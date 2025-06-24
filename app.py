import streamlit as st
from workflow import react_agent
from langchain_core.messages import HumanMessage

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

  # Show all steps in a status box
  with st.status("Agent reasoning (all steps shown below):", expanded=True) as status:
    final = None
    for event in react_agent.stream({"messages": messages}):
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
    status.update(label="Agent finished", state="complete")

#%%
from workflow import react_agent
from langchain_core.messages import HumanMessage

print("AI Travel Agent CLI Debugger\nType 'exit' to quit.\n")
chat_history = []

while True:
  user_input = input("You: ")
  if user_input.strip().lower() in {"exit", "quit"}:
    break
  chat_history.append({"role": "user", "content": user_input})
  messages = [
    HumanMessage(content=m["content"]) if m["role"] == "user" else None
    for m in chat_history
  ]
  messages = [m for m in messages if m is not None]

  print("\n--- Agent Reasoning Steps ---")
  final = None
  for event in react_agent.stream({"messages": messages}):
    if "messages" not in event:
      continue
    step_msgs = event["messages"]
    for m in step_msgs:
      if hasattr(m, "tool_calls") and m.tool_calls:
        for call in m.tool_calls:
          print(f"[Tool Call] {call['name']}({call['args']})")
      elif getattr(m, "type", None) == "ai":
        print(f"[LLM Thought] {m.content}")
      elif getattr(m, "type", None) == "tool":
        print(f"[Tool Output] {m.content}")
      else:
        print(f"[Message] {m.content}")
    final = step_msgs[-1].content if step_msgs else None
  if final:
    chat_history.append({"role": "assistant", "content": final})
    print(f"\nAgent: {final}\n")
#%%
