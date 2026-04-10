import logging
import time
from typing import List

import requests

from src.models import Product

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """\
请用不超过两句话概括这个 Product Hunt 产品（使用中文）：
1. 第一句话：核心功能（这个项目是什么，解决什么问题）
2. 第二句话：技术特点（使用什么技术、架构亮点或实现方式）
总字数控制在 150 字以内。

产品名称：{name}
标语：{tagline}
描述：{description}
话题：{topics}
"""


def _call_llm(api_key: str, base_url: str, model: str, prompt: str) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that summarizes tech products in Chinese."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 256,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def generate_summaries(
    products: List[Product],
    api_key: str,
    base_url: str,
    primary_model: str,
    fallback_models: List[str],
) -> None:
    """Generate summaries in-place on Product objects."""
    models = [primary_model] + fallback_models
    for p in products:
        prompt = PROMPT_TEMPLATE.format(
            name=p.name,
            tagline=p.tagline,
            description=p.description,
            topics=", ".join(p.topics),
        )
        summary = ""
        for model in models:
            try:
                summary = _call_llm(api_key, base_url, model, prompt)
                logger.info("Generated summary for %s via %s", p.name, model)
                break
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response else 0
                if status == 429:
                    logger.warning("Rate limited on %s for %s, trying fallback", model, p.name)
                    time.sleep(1)
                    continue
                logger.error("HTTP error summarizing %s with %s: %s", p.name, model, exc)
            except Exception as exc:
                logger.error("Error summarizing %s with %s: %s", p.name, model, exc)
        p.ai_summary = summary or "暂无摘要"
        time.sleep(0.5)
