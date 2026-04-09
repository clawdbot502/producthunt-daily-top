import logging
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from src.config import Config
from src.ph_client import fetch_top_products
from src.ai_summary import generate_summaries
from src.lark.auth import get_tenant_token
from src.lark.base_client import batch_create_records
from src.lark.docx_client import create_doc, build_blocks, append_blocks
from src.lark.im_client import send_card

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def _pt_midnight_ms() -> int:
    pt = ZoneInfo("America/Los_Angeles")
    pt_midnight = datetime.now(pt).replace(hour=0, minute=0, second=0, microsecond=0)
    return int(pt_midnight.timestamp() * 1000)


def main() -> None:
    config = Config()
    logger.info("Config loaded")

    # 1. Fetch products
    products = fetch_top_products(config.ph_token, limit=10)
    if not products:
        logger.error("No products fetched from Product Hunt")
        sys.exit(1)
    logger.info("Fetched %s products for PT date %s", len(products), products[0].ph_date)

    # 2. AI summaries
    generate_summaries(
        products,
        api_key=config.summary_api_key,
        base_url=config.summary_base_url,
        primary_model=config.summary_model,
        fallback_models=config.summary_fallback_models,
    )
    logger.info("AI summaries generated")

    # 3. Lark auth
    token = get_tenant_token(config.lark_app_id, config.lark_app_secret)
    logger.info("Lark tenant token obtained")

    # 4. Base sync
    try:
        date_ms = _pt_midnight_ms()
        batch_create_records(
            token,
            app_token=config.lark_base_app_token,
            table_id=config.lark_base_table_id,
            products=products,
            date_ms=date_ms,
        )
    except Exception as exc:
        logger.error("Base sync failed: %s", exc)
        # Non-fatal: continue to doc + message

    # 5. Doc creation
    doc_id = None
    try:
        title = f"Product Hunt Daily Top 10 — {products[0].ph_date}"
        doc_id = create_doc(token, title)
        blocks = build_blocks(products, products[0].ph_date)
        append_blocks(token, doc_id, blocks)
    except Exception as exc:
        logger.error("Doc creation failed: %s", exc)

    # 6. Group message
    try:
        doc_url = f"https://open.feishu.cn/docx/{doc_id}" if doc_id else ""
        send_card(token, config.lark_chat_id, products[:3], products[0].ph_date, doc_url)
    except Exception as exc:
        logger.error("Group message failed: %s", exc)

    logger.info("Pipeline finished")


if __name__ == "__main__":
    main()
