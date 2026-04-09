import requests

AUTH_URL = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"


def get_tenant_token(app_id: str, app_secret: str) -> str:
    resp = requests.post(
        AUTH_URL,
        json={"app_id": app_id, "app_secret": app_secret},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    # Compatibility: token may be top-level or nested under .data
    token = data.get("tenant_access_token") or data.get("data", {}).get("tenant_access_token")
    if not token:
        raise RuntimeError(f"Failed to retrieve tenant_access_token: {data}")
    return token
