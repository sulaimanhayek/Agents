import asyncio

from beeai_framework.agents.bee.agent import BeeAgent
from beeai_framework.agents.types import BeeInput, BeeRunInput
from beeai_framework.backend.chat import ChatModel
from beeai_framework.memory.unconstrained_memory import UnconstrainedMemory


async def main() -> None:
    chat_model = ChatModel.from_name("ollama:granite3.1-dense:8b")

    agent = BeeAgent(BeeInput(llm=chat_model, tools=[], memory=UnconstrainedMemory()))

    result = await agent.run(BeeRunInput(prompt="What is the capital of Massachusetts"))

    print("answer:", result.result.text)
    # try:
    #     result = await agent.run(BeeRunInput(prompt="What is the capital of Massachusetts"))
    #     print("answer:", result.result.text)
    # except Exception as e:
    #     print("Error:", e)
    # result = await agent.run(BeeRunInput(prompt="Provide a JSON response: {'answer': 'your response'}"))
    # print("answer:", result.result.text)

if __name__ == "__main__":
    asyncio.run(main())