from typing import Any, Optional

from langchain_core.outputs import ChatResult
from langchain_openai import ChatOpenAI
from pydantic import Field

DEFAULT_OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
DEFAULT_REFERER = "https://github.com/deerflow/deerflow"
DEFAULT_TITLE = "DeerFlow"


class ChatOpenRouter(ChatOpenAI):
    openai_api_base: Optional[str] = Field(
        default=DEFAULT_OPENROUTER_API_BASE,
        alias="base_url",
    )
    referer: Optional[str] = Field(default=DEFAULT_REFERER)
    title: Optional[str] = Field(default=DEFAULT_TITLE)

    def __init__(self, **kwargs: Any):
        referer = kwargs.pop("referer", None) or DEFAULT_REFERER
        title = kwargs.pop("title", None) or DEFAULT_TITLE
        api_base = kwargs.pop("api_base", None) or DEFAULT_OPENROUTER_API_BASE

        base_url = (
            kwargs.pop("base_url", None)
            or kwargs.pop("openai_api_base", None)
            or api_base
        )

        default_headers = dict(kwargs.get("default_headers") or {})
        if referer:
            default_headers.setdefault("HTTP-Referer", referer)
        if title:
            default_headers.setdefault("X-OpenRouter-Title", title)
        kwargs["default_headers"] = default_headers

        super().__init__(base_url=base_url, **kwargs)

    def _create_chat_result(self, response: Any) -> ChatResult:
        result = super()._create_chat_result(response)

        if (
            hasattr(response, "choices")
            and response.choices
            and hasattr(response.choices[0], "message")
        ):
            message = response.choices[0].message
            reasoning = (
                getattr(message, "reasoning", None)
                or getattr(message, "reasoning_content", None)
                or getattr(message, "reasoning_details", None)
            )

            if reasoning and result.generations:
                result.generations[0].message.additional_kwargs["reasoning"] = reasoning

        return result

    @property
    def _llm_type(self) -> str:
        return "openrouter"

    # return "openai-chat"
    if __name__ == "__main__":
        model = ChatOpenRouter(
            model="openai/gpt-4o-mini",
            api_key="test",
        )
        print(model.model_kwargs)
        print(model.openai_api_base)    