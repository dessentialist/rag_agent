import logging
from typing import Dict, List, Optional, Tuple

from database import db
from models import Agent

logger = logging.getLogger(__name__)


def list_agents() -> List[Agent]:
    return Agent.query.order_by(Agent.id.asc()).all()


def get_agent_by_name(name: str) -> Optional[Agent]:
    return Agent.query.filter_by(name=name).first()


def create_agent(
    name: str,
    description: Optional[str],
    role_system_prompt: str,
    llm_model: str,
    temperature: float,
    max_tokens: int,
    response_format: Optional[str],
    selection_rules: Dict,
) -> Agent:
    agent = Agent(
        name=name,
        description=description,
        role_system_prompt=role_system_prompt,
        llm_model=llm_model,
        temperature=float(temperature),
        max_tokens=int(max_tokens),
        response_format=response_format,
        selection_rules=selection_rules or {},
    )
    db.session.add(agent)
    db.session.commit()
    logger.info(f"Created agent '{name}'")
    return agent


def update_agent(agent_id: int, **fields) -> Optional[Agent]:
    agent = Agent.query.get(agent_id)
    if agent is None:
        return None
    for key, value in fields.items():
        if hasattr(agent, key):
            setattr(agent, key, value)
    db.session.commit()
    logger.info(f"Updated agent id={agent_id}")
    return agent


def delete_agent(agent_id: int) -> bool:
    agent = Agent.query.get(agent_id)
    if not agent:
        return False
    db.session.delete(agent)
    db.session.commit()
    logger.info(f"Deleted agent id={agent_id}")
    return True


def _doc_types_from_results(relevant_docs: List[Dict]) -> List[str]:
    types: List[str] = []
    for d in relevant_docs:
        md = d.get("metadata", {}) or {}
        # Prefer 'type' but also consider 'doc_type' if present
        t = md.get("type") or md.get("doc_type")
        if isinstance(t, str):
            types.append(t.lower())
    return types


def _matches_rules(rules: Dict, doc_types: List[str], user_query: str) -> bool:
    if not rules:
        return False
    user_query_lower = (user_query or "").lower()

    # Rule 1: doc_type_any_of
    allowed_types = rules.get("doc_type_any_of")
    if isinstance(allowed_types, list) and allowed_types:
        allowed_types_normalized = {str(t).lower() for t in allowed_types}
        if not any(dt in allowed_types_normalized for dt in doc_types):
            return False

    # Rule 2: keyword_any_of (in user query)
    keywords = rules.get("keyword_any_of")
    if isinstance(keywords, list) and keywords:
        if not any(kw.lower() in user_query_lower for kw in keywords if isinstance(kw, str)):
            return False

    # Rule 3: keyword_all_of
    kw_all = rules.get("keyword_all_of")
    if isinstance(kw_all, list) and kw_all:
        if not all(kw.lower() in user_query_lower for kw in kw_all if isinstance(kw, str)):
            return False

    return True


def select_agent_for_request(
    relevant_docs: List[Dict], user_query: str
) -> Tuple[Optional[Agent], Optional[Dict]]:
    """Select an agent using selection_rules evaluated against docs and query.

    Returns (agent, matched_rules) or (None, None) when no matches.
    """
    agents = list_agents()
    if not agents:
        logger.warning("No agents configured in registry")
        return None, None

    doc_types = _doc_types_from_results(relevant_docs)
    logger.info(f"Evaluating selection rules against doc_types={doc_types}")

    for agent in agents:
        rules = agent.selection_rules or {}
        if _matches_rules(rules, doc_types, user_query):
            logger.info(f"Selected agent '{agent.name}' via rules={rules}")
            return agent, rules

    logger.warning("No selection_rules matched for any agent")
    return None, None


def ensure_default_agents() -> None:
    """Seed two example agents if none exist.

    - documentation_agent: selected when doc_type includes 'documentation'
    - course_agent: selected when doc_type includes 'course'
    """
    if Agent.query.count() > 0:
        return

    logger.info("Seeding default agents into registry")
    rag_rigor = (
        "You are a strict RAG agent. Use ONLY retrieved documents. "
        "If insufficient info, reply: 'I'm sorry, I couldn't find information about that in my knowledge base.' "
        "Respond in compact JSON with keys 'main' and 'next_steps'."
    )

    create_agent(
        name="documentation",
        description="Agent specialized for technical documentation",
        role_system_prompt=(
            rag_rigor
            + " Prefer concise technical explanations. Include document references inline."
        ),
        llm_model="gpt-4o",
        temperature=0.3,
        max_tokens=1200,
        response_format="json_object",
        selection_rules={"doc_type_any_of": ["documentation"]},
    )

    create_agent(
        name="course",
        description="Agent specialized for course/help content",
        role_system_prompt=(
            rag_rigor + " Provide helpful, friendly tone and actionable next steps."
        ),
        llm_model="gpt-4o",
        temperature=0.4,
        max_tokens=1200,
        response_format="json_object",
        selection_rules={"doc_type_any_of": ["course"]},
    )
