import os
import json
import requests
from datetime import datetime, timezone, timedelta

# ============ 配置 ============
PH_API_URL = "https://api.producthunt.com/v2/api/graphql"
LARK_BASE_URL = "https://open.feishu.cn/open-apis"
BEIJING_TZ = timezone(timedelta(hours=8))

PH_TOKEN = os.getenv("PH_TOKEN")
LARK_APP_ID = os.getenv("LARK_APP_ID")
LARK_APP_SECRET = os.getenv("LARK_APP_SECRET")
LARK_CHAT_ID = os.getenv("LARK_CHAT_ID")


# ============ Product Hunt API ============
def fetch_top_products(limit=10):
    """从 Product Hunt GraphQL API 获取当日 Top N 产品"""
    now_bj = datetime.now(BEIJING_TZ)
    today = now_bj.strftime("%Y-%m-%d")

    query = """
    query($date: DateTime!, $limit: Int!) {
        posts(order: VOTES, postedAfter: $date, first: $limit) {
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
                }
            }
        }
    }
    """

    # 当天 00:00 UTC (Product Hunt 按 PST 时区，这里用当天开始时间)
    posted_after = f"{today}T00:00:00Z"

    headers = {
        "Authorization": f"Bearer {PH_TOKEN}",
        "Content-Type": "application/json",
    }

    resp = requests.post(
        PH_API_URL,
        json={"query": query, "variables": {"date": posted_after, "limit": limit}},
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    products = []
    for edge in data.get("data", {}).get("posts", {}).get("edges", []):
        node = edge["node"]
        products.append({
            "name": node["name"],
            "tagline": node["tagline"],
            "description": node.get("description", ""),
            "url": node["url"],
            "website": node.get("website", ""),
            "votes": node.get("votesCount", 0),
            "comments": node.get("commentsCount", 0),
            "topics": [t["node"]["name"] for t in node.get("topics", {}).get("edges", [])],
            "thumbnail": node.get("thumbnail", {}).get("url", ""),
        })

    return products, today


# ============ 飞书 API ============
def get_lark_token():
    """获取飞书 tenant_access_token"""
    resp = requests.post(
        f"{LARK_BASE_URL}/auth/v3/tenant_access_token/internal",
        json={"app_id": LARK_APP_ID, "app_secret": LARK_APP_SECRET},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["tenant_access_token"]


def create_lark_doc(token, title):
    """创建飞书文档，返回 document_id"""
    resp = requests.post(
        f"{LARK_BASE_URL}/docx/v1/documents",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"title": title},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["data"]["document"]["document_id"]


def add_text_block(token, document_id, block_id, text, heading_level=None):
    """向飞书文档追加文本块"""
    if heading_level:
        block_type = {1: 3, 2: 4, 3: 5}[heading_level]
    else:
        block_type = 2  # text

    body = {
        "children": [
            {
                "block_type": block_type,
                f"heading{heading_level or 1}": {
                    "elements": [{"text_run": {"content": text}}],
                    "style": {},
                } if heading_level else None,
                "text": {
                    "elements": [{"text_run": {"content": text}}],
                    "style": {},
                } if not heading_level else None,
            }
        ]
    }

    # 清理 None 字段
    for child in body["children"]:
        if child.get("heading1") is None:
            child.pop("heading1", None)
        if child.get("text") is None:
            child.pop("text", None)

    resp = requests.post(
        f"{LARK_BASE_URL}/docx/v1/documents/{document_id}/blocks/{block_id}/children",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=body,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def write_products_to_doc(token, document_id, products, date_str):
    """将产品列表写入飞书文档"""
    doc_block_id = document_id

    # 写入标题
    add_text_block(token, document_id, doc_block_id,
                   f"Product Hunt 每日热门 Top 10 — {date_str}", heading_level=1)

    for i, p in enumerate(products, 1):
        # 产品名称
        add_text_block(token, document_id, doc_block_id,
                       f"#{i} {p['name']}", heading_level=2)
        # 产品描述
        add_text_block(token, document_id, doc_block_id,
                       f"{p['tagline']}")
        # 详情
        detail = f"👍 {p['votes']} 票  💬 {p['comments']} 评论"
        if p["topics"]:
            detail += f"  🏷️ {', '.join(p['topics'][:5])}"
        add_text_block(token, document_id, doc_block_id, detail)
        # 链接
        links = f"🔗 Product Hunt: {p['url']}"
        if p["website"]:
            links += f"\n🌐 官网: {p['website']}"
        add_text_block(token, document_id, doc_block_id, links)


def send_lark_message(token, products, date_str, doc_url):
    """发送摘要消息到飞书群"""
    top3 = "\n".join(
        f"  {i}. {p['name']} — {p['tagline']} (👍{p['votes']})"
        for i, p in enumerate(products[:3], 1)
    )

    text = (
        f"🚀 Product Hunt 每日热门 Top 10 — {date_str}\n\n"
        f"今日 Top 3:\n{top3}\n\n"
        f"📄 完整报告: {doc_url}"
    )

    resp = requests.post(
        f"{LARK_BASE_URL}/im/v1/messages?receive_id_type=chat_id",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "receive_id": LARK_CHAT_ID,
            "msg_type": "text",
            "content": json.dumps({"text": text}),
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


# ============ 主流程 ============
def main():
    print("=== Product Hunt Daily Top 10 ===")

    # 1. 抓取数据
    print("[1/4] 抓取 Product Hunt 数据...")
    products, date_str = fetch_top_products(limit=10)
    print(f"  获取到 {len(products)} 个产品")

    # 2. 保存 JSON 到本地
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    json_path = os.path.join(data_dir, f"{date_str}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"date": date_str, "products": products}, f, ensure_ascii=False, indent=2)
    print(f"[2/4] 数据已保存到 {json_path}")

    # 3. 飞书文档
    if LARK_APP_ID and LARK_APP_SECRET:
        print("[3/4] 创建飞书文档...")
        token = get_lark_token()
        title = f"PH Daily Top 10 — {date_str}"
        doc_id = create_lark_doc(token, title)
        write_products_to_doc(token, doc_id, products, date_str)
        doc_url = f"https://bytedance.larkoffice.com/docx/{doc_id}"
        print(f"  飞书文档: {doc_url}")

        # 4. 飞书群通知
        if LARK_CHAT_ID:
            print("[4/4] 推送飞书群消息...")
            send_lark_message(token, products, date_str, doc_url)
            print("  群消息已发送")
        else:
            print("[4/4] 跳过群消息 (LARK_CHAT_ID 未配置)")
    else:
        print("[3/4] 跳过飞书写入 (LARK_APP_ID / LARK_APP_SECRET 未配置)")
        print("[4/4] 跳过群消息")

    print("=== 完成 ===")


if __name__ == "__main__":
    main()
