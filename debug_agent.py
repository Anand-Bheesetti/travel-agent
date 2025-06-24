
#%%from workflow import react_agent
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
    print("EVENT:", event)
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