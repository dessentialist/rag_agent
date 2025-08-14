import logging
import json
from typing import Dict, Any, List
import traceback
from openai import OpenAI
from config import (
    RAG_SYSTEM_MESSAGE_TEMPLATE,
    NO_DOCUMENTS_MESSAGE,
    CRITICAL_REMINDER_MESSAGE,
)
from services.settings_service import get_openai_settings, SettingsValidationError


logger = logging.getLogger(__name__)


def _get_client() -> OpenAI:
    cfg = get_openai_settings()
    api_key = cfg.get("api_key")
    if not api_key:
        raise SettingsValidationError("OpenAI API key is not configured. Please set it in settings.")
    return OpenAI(api_key=api_key)


def _build_messages(role_system_prompt: str, relevant_docs: List[Dict[str, Any]], user_query: str) -> List[Dict[str, str]]:
    # Prepare documents context block
    docs_context = ""
    if relevant_docs:
        for i, doc in enumerate(relevant_docs):
            metadata = doc.get('metadata', {}) or {}
            source_info = []
            if 'source_filename' in metadata:
                source_info.append(f"Source filename: {metadata['source_filename']}")
            if 'url' in metadata:
                source_info.append(f"Source URL: {metadata['url']}")
            if 'type' in metadata:
                source_info.append(f"Document Type: {metadata['type']}")
            info = "\n".join(source_info)
            docs_context += f"Document {i+1} [ID: {doc.get('id', 'unknown')}]\n{info}\nContent:\n{doc.get('content', '')}\n\n"

    messages = [{"role": "system", "content": role_system_prompt}]
    if docs_context:
        messages.append({
            "role": "system",
            "content": f"## RETRIEVED DOCUMENTS (ONLY USE INFORMATION FROM THESE DOCUMENTS)\n\n{docs_context}",
        })
    else:
        messages.append({"role": "system", "content": NO_DOCUMENTS_MESSAGE})
    messages.append({"role": "system", "content": CRITICAL_REMINDER_MESSAGE})
    messages.append({"role": "user", "content": user_query})
    return messages


def generate_response(agent_cfg: Any, user_query: str, relevant_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a response using OpenAI based on the provided agent configuration.

    agent_cfg must provide: role_system_prompt, llm_model, temperature, max_tokens, response_format
    """
    try:
        messages = _build_messages(agent_cfg.role_system_prompt, relevant_docs, user_query)

        # Load LLM parameters from agent config
        model = agent_cfg.llm_model
        temperature = float(agent_cfg.temperature)
        max_tokens = int(agent_cfg.max_tokens)
        response_format = {"type": agent_cfg.response_format or "json_object"}

        logger.info(f"[API] Calling OpenAI with model={model}, messages={len(messages)}")
        summary = [{"role": m["role"], "len": len(m["content"]) } for m in messages]
        logger.info(f"[API] Message summary: {json.dumps(summary)}")

        response = _get_client().chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )

        text = response.choices[0].message.content
        try:
            parsed = json.loads(text)
            return parsed
        except json.JSONDecodeError:
            logger.warning("Response is not valid JSON; returning plain text in 'main'")
            return {"main": text}
    except Exception as exc:
        logger.error(f"generate_response error: {exc}", exc_info=True)
        return {"main": "An error occurred while generating the response."}
