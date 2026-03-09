import logging

from langchain.chat_models import BaseChatModel

from src.config import get_app_config, get_tracing_config, is_tracing_enabled
from src.reflection import resolve_class

logger = logging.getLogger(__name__)

def create_chat_model(
    name: str | None = None,
    thinking_enabled: bool = False,
    **kwargs,
) -> BaseChatModel:
    """Create a chat model instance from the config."""
    app_config = get_app_config()

    if name is None:
        name = app_config.models[0].name

    model_config = next((m for m in app_config.models if m.name == name), None)
    if model_config is None:
        raise ValueError(f"Model {name} not found in config") from None

    model_class = resolve_class(model_config.use, BaseChatModel)

    model_settings_from_config = model_config.model_dump(
        exclude_none=True,
        exclude={
            "use",
            "name",
            "display_name",
            "description",
            "supports_thinking",
            "supports_reasoning_effort",
            "when_thinking_enabled",
            "supports_vision",
            "base_url",
            "openai_api_base",
        },
    )
    logger.debug("model_settings_from_config before pop = %s", model_settings_from_config)
    logger.debug("kwargs before pop = %s", kwargs)
    

    # Normalize client base URL to exactly one constructor arg
    base_url = (
        model_config.model_dump(exclude_none=True).get("base_url")
        or model_config.model_dump(exclude_none=True).get("openai_api_base")
    )
    if base_url is not None and "base_url" not in kwargs and "openai_api_base" not in kwargs:
        kwargs["base_url"] = base_url

    if thinking_enabled and model_config.when_thinking_enabled is not None:
        if not model_config.supports_thinking:
            raise ValueError(
                f"Model {name} does not support thinking. "
                "Set `supports_thinking` to true in the `config.yaml` to enable thinking."
            ) from None
        model_settings_from_config.update(model_config.when_thinking_enabled)

    if (
        not thinking_enabled
        and model_config.when_thinking_enabled
        and model_config.when_thinking_enabled.get("extra_body", {})
        .get("thinking", {})
        .get("type")
    ):
        kwargs.update({"extra_body": {"thinking": {"type": "disabled"}}})
        kwargs.update({"reasoning_effort": "minimal"})

    # Final normalization for reasoning_effort
    if not model_config.supports_reasoning_effort:
        # Check both candidates for the parameter
        val1 = model_settings_from_config.pop("reasoning_effort", None)
        val2 = kwargs.pop("reasoning_effort", None)
        # Use existing value if present, otherwise default to "disabled"
        # Priority: explicit kwargs > config settings
        effort_val = val2 if val2 is not None else (val1 if val1 is not None else "disabled")
        kwargs.setdefault("model_kwargs", {})["reasoning_effort"] = effort_val

    logger.debug("Final model settings: %s", model_settings_from_config)
    logger.debug("Final kwargs: %s", kwargs)

    model_instance = model_class(**model_settings_from_config, **kwargs)

    if is_tracing_enabled():
        try:
            from langchain_core.tracers.langchain import LangChainTracer

            tracing_config = get_tracing_config()
            tracer = LangChainTracer(project_name=tracing_config.project)
            existing_callbacks = model_instance.callbacks or []
            model_instance.callbacks = [*existing_callbacks, tracer]
            logger.debug(
                "LangSmith tracing attached to model '%s' (project='%s')",
                name,
                tracing_config.project,
            )
        except Exception as e:
            logger.warning(
                "Failed to attach LangSmith tracing to model '%s': %s",
                name,
                e,
            )

    return model_instance