import logging
from typing import List, Any, Dict

import requests

from src.models import Product

logger = logging.getLogger(__name__)
BASE_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps"


def _product_to_record(product: Product, date_ms: int) -> Dict[str, Any]:
    return {
        "fields": {
            "日期": date_ms,
            "排名": product.rank,
            "产品名称": product.name,
            "标语": product.tagline,
            "AI 摘要": product.ai_summary,
            "投票数": product.votes,
            "评论数": product.comments,
            "话题标签": product.topics,
            "PH 链接": {"text": product.url, "link": product.url},
            "官网链接": {"text": product.website, "link": product.website} if product.website else "",
            "缩略图": {"text": product.thumbnail, "link": product.thumbnail} if product.thumbnail else "",
        }
    }


def batch_create_records(
    token: str,
    app_token: str,
    table_id: str,
    products: List[Product],
    date_ms: int,
) -> List[str]:
    url = f"{BASE_URL}/{app_token}/tables/{table_id}/records/batch_create"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    records = [_product_to_record(p, date_ms) for p in products]
    payload = {"records": records}

    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code", -1) != 0:
        raise RuntimeError(f"Feishu Base batch_create failed: {data}")

    created = data.get("data", {}).get("records", [])
    record_ids = [r.get("record_id", "") for r in created]
    logger.info("Created %s Base records", len(record_ids))
    return record_ids
