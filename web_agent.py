import asyncio
import sys
import traceback

from langchain_community.utilities import SearxSearchWrapper
from pydantic import BaseModel, Field, ValidationError

from beeai_framework.adapters.ollama.backend.chat import OllamaChatModel
from beeai_framework.backend.chat import ChatModelOutput, ChatModelStructureOutput
from beeai_framework.backend.message import UserMessage
from beeai_framework.utils.templates import PromptTemplate #, PromptTemplateInput
from beeai_framework.workflows.workflow import Workflow, WorkflowError


async def main() -> None:
    llm = OllamaChatModel("granite3.1-dense:8b")
    search = SearxSearchWrapper(searx_host="http://localhost:port")

    class State(BaseModel):
        input: str
        search_results: str | None = None
        output: str | None = None

    class InputSchema(BaseModel):
        input: str

    class WebSearchQuery(BaseModel):
        search_query: str = Field(description="Search query.")

    class RAGSchema(InputSchema):
        input: str
        search_results: str

    async def web_search(state: State) -> str:
        print("Step: ", sys._getframe().f_code.co_name)
        # prompt = PromptTemplate(
        #     PromptTemplateInput(
        #         schema=InputSchema,
        #         template="""
        #     Please create a web search query for the following input.
        #     Query: {{input}}""",
        #     )
        # ).render(InputSchema(input=state.input))
        prompt = PromptTemplate(
            schema=InputSchema,
            template="""
                Please create a web search query for the following input.
                Query: {{input}}
            """
        ).render(InputSchema(input=state.input))

        output: ChatModelStructureOutput = await llm.create_structure(
            {
                "schema": WebSearchQuery,
                "messages": [UserMessage(prompt)],
            }
        )
        # TODO Why is object not of type schema T?
        state.search_results = search.run(f"current weather in {output.object['search_query']}")
        return Workflow.NEXT

    async def generate_output(state: State) -> str:
        print("Step: ", sys._getframe().f_code.co_name)

    #     prompt = PromptTemplate(
    #         PromptTemplateInput(
    #             schema=RAGSchema,
    #             template="""
    # Use the following search results to answer the query accurately. If the results are irrelevant or insufficient, say 'I don't know.'

    # Search Results:
    # {{search_results}}

    # Query: {{input}}
    # """,  # noqa: E501
    #         )
    #     ).render(
    #         RAGSchema(
    #             input=state.input,
    #             search_results=state.search_results or "No results available.",
    #         )
    #     )

        prompt = PromptTemplate(
            schema=RAGSchema,
            template="""
                Use the following search results to answer the query accurately.
                If the results are irrelevant or insufficient, say 'I don't know.'

                Search Results:
                {{search_results}}

                Query: {{input}}
            """
            ).render(
                RAGSchema(
                    input=state.input,
                    search_results=state.search_results or "No results available.",
                ) 
            )
        output: ChatModelOutput = await llm.create({"messages": [UserMessage(prompt)]})
        state.output = output.get_text_content()
        return Workflow.END

    try:
        # Define the structure of the workflow graph
        workflow = Workflow(State)
        workflow.add_step("web_search", web_search)
        workflow.add_step("generate_output", generate_output)

        # Execute the workflow
        result = await workflow.run(State(input="Can you recommend fiction books to read, genre science fictio, list them in your answer"))

        print("\n*********************")
        print("Input: ", result.state.input)
        print("Agent: ", result.state.output)

    except WorkflowError:
        traceback.print_exc()
    except ValidationError:
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())