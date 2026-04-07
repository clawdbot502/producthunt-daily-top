# Product Hunt Daily Top 10

每天自动抓取 Product Hunt 当日热门前 10 个产品，存档到 GitHub 并同步到飞书。

## 功能

- **数据抓取**：通过 Product Hunt GraphQL API 获取每日 Top 10 产品（按投票排序）
- **本地存档**：数据以 JSON 格式保存在 `data/` 目录，每日一份
- **飞书文档**：自动创建飞书云文档，写入产品详细信息（名称、描述、投票数、链接等）
- **群消息推送**：将 Top 3 摘要和文档链接推送到飞书群

## 数据结构

每个产品包含以下字段：

```json
{
  "name": "产品名称",
  "tagline": "一句话描述",
  "description": "详细介绍",
  "url": "Product Hunt 链接",
  "website": "官网链接",
  "votes": 999,
  "comments": 88,
  "topics": ["AI", "Developer Tools"],
  "thumbnail": "缩略图 URL"
}
```

## 配置

在 GitHub 仓库 Settings → Secrets and variables → Actions 中添加：

| Secret | 说明 |
|---|---|
| `PH_TOKEN` | [Product Hunt Developer Token](https://www.producthunt.com/v2/oauth/applications) |
| `LARK_APP_ID` | 飞书应用 App ID |
| `LARK_APP_SECRET` | 飞书应用 App Secret |
| `LARK_CHAT_ID` | 飞书目标群聊 chat_id |

## 定时任务

GitHub Actions 每天北京时间 **09:00** 自动执行，也可手动触发。

## 本地运行

```bash
pip install requests
PH_TOKEN=xxx LARK_APP_ID=xxx LARK_APP_SECRET=xxx LARK_CHAT_ID=xxx python main.py
```

## 目录结构

```
├── .github/workflows/daily.yml   # GitHub Actions 定时任务
├── main.py                       # 主脚本
├── requirements.txt              # 依赖
├── data/                         # 历史数据存档
│   └── 2026-04-07.json
└── README.md
```
