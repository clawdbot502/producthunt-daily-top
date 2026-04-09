import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import List

from src.models import Product

GRAPHQL_URL = "https://api.producthunt.com/v2/api/graphql"

QUERY = """
query Posts($postedAfter: DateTime, $postedBefore: DateTime, $first: Int) {
  posts(
    postedAfter: $postedAfter
    postedBefore: $postedBefore
    order: RANKING
    first: $first
  ) {
    edges {
      node {
        id
        name
        tagline
        description
        url
        website
        votesCount
        commentsCount
        topics {
          edges {
            node {
              name
            }
          }
        }
        thumbnail {
          url
        }
        createdAt
      }
    }
  }
}
"""


def _pt_day_boundaries() -> tuple[str, str, str]:
    """Return (posted_after_utc, posted_before_utc, ph_date_str) for the current PT day."""
    pt = ZoneInfo("America/Los_Angeles")
    now_pt = datetime.now(pt)
    pt_midnight = now_pt.replace(hour=0, minute=0, second=0, microsecond=0)
    pt_next_midnight = pt_midnight + timedelta(days=1)

    posted_after = pt_midnight.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")
    posted_before = pt_next_midnight.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")
    ph_date = pt_midnight.strftime("%Y-%m-%d")
    return posted_after, posted_before, ph_date


def fetch_top_products(ph_token: str, limit: int = 10) -> List[Product]:
    posted_after, posted_before, ph_date = _pt_day_boundaries()

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ph_token}",
    }
    payload = {
        "query": QUERY,
        "variables": {
            "postedAfter": posted_after,
            "postedBefore": posted_before,
            "first": limit,
        },
    }

    resp = requests.post(GRAPHQL_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    edges = data.get("data", {}).get("posts", {}).get("edges", [])
    products: List[Product] = []
    for rank, edge in enumerate(edges, start=1):
        node = edge["node"]
        topics = [t["node"]["name"] for t in node.get("topics", {}).get("edges", [])]
        products.append(
            Product(
                name=node.get("name", ""),
                tagline=node.get("tagline", ""),
                description=node.get("description", ""),
                url=node.get("url", ""),
                website=node.get("website", ""),
                votes=node.get("votesCount", 0),
                comments=node.get("commentsCount", 0),
                topics=topics,
                thumbnail=node.get("thumbnail", {}).get("url", ""),
                rank=rank,
                ph_date=ph_date,
            )
        )
    return products
