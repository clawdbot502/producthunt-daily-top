import base64
import json
import logging
from typing import List

import requests

from src.models import Product

logger = logging.getLogger(__name__)
IM_URL = "https://open.larksuite.com/open-apis/im/v1/messages"


def _build_card(top3: List[Product], date_str: str, doc_url: str) -> dict:
    elements = [
        {
            "tag": "div",
            "text": {
                "tag": "plain_text",
                "content": f"🚀 Product Hunt Daily Top 10 — {date_str}",
            },
        },
        {"tag": "hr"},
    ]
    for p in top3:
        elements.append(
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": (
                        f"**#{p.rank} {p.name}**\n"
                        f"{p.tagline}\n"
                        f"👍 {p.votes}  💬 {p.comments}  🏷️ {', '.join(p.topics)}\n"
                        f"🤖 {p.ai_summary}"
                    ),
                },
            }
        )
        elements.append(
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "查看详情"},
                        "url": p.url,
                        "type": "primary",
                    }
                ],
            }
        )
        elements.append({"tag": "hr"})

    if doc_url:
        elements.append(
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "📄 查看完整报告"},
                        "url": doc_url,
                        "type": "default",
                    }
                ],
            }
        )

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": f"Product Hunt Daily — {date_str}"},
            "template": "blue",
        },
        "elements": elements,
    }


def send_card(token: str, chat_id: str, top3: List[Product], date_str: str, doc_url: str) -> None:
    url = f"{IM_URL}?receive_id_type=chat_id"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    card = _build_card(top3, date_str, doc_url)
    receive_id = base64.b64encode(chat_id.encode("utf-8")).decode("utf-8")
    payload = {
        "receive_id": receive_id,
        "msg_type": "interactive",
        "content": json.dumps({"card": card}),
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        logger.error("IM send HTTP error: %s - body: %s", exc, resp.text)
        raise
    data = resp.json()
    if data.get("code", -1) != 0:
        raise RuntimeError(f"Feishu IM send failed: {data}")
    logger.info("Sent interactive card to chat %s", chat_id)
