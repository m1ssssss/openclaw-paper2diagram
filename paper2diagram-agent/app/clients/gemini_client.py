import json
import httpx


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: int = 180,
        connect_timeout_seconds: int = 60,
        use_query_key: bool = False,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.connect_timeout_seconds = connect_timeout_seconds
        self.use_query_key = use_query_key

    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        if not self.api_key:
            raise ValueError("Missing GEMINI_API_KEY")

        url = f"{self.base_url}/models/{self.model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature},
        }

        headers = {"Content-Type": "application/json"}
        params = {}
        # Google AI Studio uses ?key=...; some mirrors also use ?key= instead of Bearer.
        if "generativelanguage.googleapis.com" in self.base_url or self.use_query_key:
            params = {"key": self.api_key}
        else:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Read timeout covers slow proxies / long generations; connect is separate.
        timeout = httpx.Timeout(
            connect=float(self.connect_timeout_seconds),
            read=float(self.timeout_seconds),
            write=60.0,
            pool=60.0,
        )
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, params=params, headers=headers, json=payload)
            resp.raise_for_status()
            body = resp.text.strip()
            if not body:
                raise RuntimeError(
                    f"Gemini API returned empty body (HTTP {resp.status_code}). URL: {url}"
                )
            try:
                data = json.loads(body)
            except json.JSONDecodeError as exc:
                snippet = body[:800].replace("\n", " ")
                hint = ""
                if body.lstrip().lower().startswith("<!doctype") or body.lstrip().lower().startswith("<html"):
                    hint = (
                        " Response looks like HTML (often the gateway home page). "
                        "Set GEMINI_BASE_URL to the Gemini API prefix, e.g. https://your-host/v1beta "
                        "(not the bare domain)."
                    )
                raise RuntimeError(
                    f"Gemini API returned non-JSON (HTTP {resp.status_code}). "
                    f"Check GEMINI_BASE_URL and model name.{hint} Body starts with: {snippet!r}"
                ) from exc

        candidates = data.get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        return "\n".join(p.get("text", "") for p in parts).strip()
