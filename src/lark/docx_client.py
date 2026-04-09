import logging
from typing import List, Any, Dict

import requests

from src.models import Product

logger = logging.getLogger(__name__)
DOCX_API = "https://open.feishu.cn/open-apis/docx/v1/documents"


def create_doc(token: str, title: str) -> str:
    url = f"{DOCX_API}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"title": title}
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code", -1) != 0:
        raise RuntimeError(f"Feishu doc creation failed: {data}")
    doc_id = data["data"]["document"]["document_id"]
    logger.info("Created doc %s", doc_id)
    return doc_id


def _text_element(content: str) -> Dict[str, Any]:
    return {"type": "text_run", "text_run": {"content": content}}


def _block_heading(level: int, text: str) -> Dict[str, Any]:
    key = f"heading{level}"
    block_type = 2 + level  # heading1 -> 3, heading2 -> 4, heading3 -> 5
    return {
        "block_type": block_type,
        key: {"elements": [_text_element(text)]},
    }


def _block_text(text: str) -> Dict[str, Any]:
    return {
        "block_type": 2,
        "text": {"elements": [_text_element(text)]},
    }


def _block_bullet(text: str) -> Dict[str, Any]:
    return {
        "block_type": 12,
        "bullet": {
            "elements": [_text_element(text)],
            "style": {"bullet_eq_indent_level": 0},
        },
    }


def _block_divider() -> Dict[str, Any]:
    return {"block_type": 22, "divider": {}}


def build_blocks(products: List[Product], date_str: str) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    blocks.append(_block_heading(1, f"Product Hunt Daily Top 10 — {date_str}"))
    for p in products:
        blocks.append(_block_heading(2, f"#{p.rank} {p.name}"))
        blocks.append(_block_text(f"📝 {p.tagline}"))
        blocks.append(_block_text(f"🤖 AI 摘要: {p.ai_summary}"))
        blocks.append(_block_text(f"👍 {p.votes}  💬 {p.comments}  🏷️ {', '.join(p.topics)}"))
        blocks.append(_block_text(f"🔗 PH: {p.url}  |  官网: {p.website}"))
        blocks.append(_block_divider())
    return blocks


def append_blocks(token: str, document_id: str, blocks: List[Dict[str, Any]]) -> None:
    url = f"{DOCX_API}/{document_id}/blocks/{document_id}/children"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"children": blocks, "index": -1}
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        logger.error("Doc append HTTP error: %s - body: %s", exc, resp.text)
        raise
    data = resp.json()
    if data.get("code", -1) != 0:
        raise RuntimeError(f"Feishu doc append failed: {data}")
    logger.info("Appended %s blocks to doc %s", len(blocks), document_id)
