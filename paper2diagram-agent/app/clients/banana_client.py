import json
import re
import time
from typing import Any, Dict, Optional
import httpx


class BananaClient:
    def __init__(self, api_key: str, base_url: str, model: str, timeout_seconds: int = 120) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        size: str = "1536x1024",
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("Missing BANANA_PRO_API_KEY")

        # Some gateways expose nano-banana via chat completions instead of images endpoint.
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        content_text = prompt
        if negative_prompt:
            content_text = f"{prompt}\n\nNegative constraints: {negative_prompt}"

        body: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": content_text,
                }
            ],
        }

        retryable = {502, 503, 504}
        max_attempts = 3
        resp: Optional[httpx.Response] = None
        with httpx.Client(timeout=self.timeout_seconds) as client:
            for attempt in range(max_attempts):
                resp = client.post(url, headers=headers, json=body)
                if resp.status_code not in retryable:
                    break
                if attempt < max_attempts - 1:
                    time.sleep(min(2**attempt, 8))
                    continue
            assert resp is not None
            if resp.status_code in retryable:
                snippet = resp.text[:400].replace("\n", " ") if resp.text else ""
                raise RuntimeError(
                    f"Banana/image API unavailable after {max_attempts} attempts "
                    f"(HTTP {resp.status_code}). Often: upstream image service down, overloaded, or not deployed. "
                    f"URL: {url}. Body: {snippet!r}"
                )
            resp.raise_for_status()
            raw = resp.text.strip()
            if not raw:
                raise RuntimeError(
                    f"Banana/image API returned empty body (HTTP {resp.status_code}). URL: {url}"
                )
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                snippet = raw[:600].replace("\n", " ")
                raise RuntimeError(
                    f"Banana/image API returned non-JSON (HTTP {resp.status_code}). "
                    f"Check BANANA_PRO_BASE_URL (expect {self.base_url}/v1/chat/completions). "
                    f"Body starts with: {snippet!r}"
                ) from exc

        # Parse common OpenAI-compatible completion payloads and extract first URL.
        image_url = data.get("image_url")
        if not image_url:
            choices = data.get("choices", [])
            if choices and isinstance(choices, list):
                message = choices[0].get("message", {})
                content = message.get("content", "")
                if isinstance(content, str):
                    m = re.search(r"https?://\S+", content)
                    if m:
                        image_url = m.group(0).rstrip(").,")

        return {
            "raw_response": data,
            "image_url": image_url,
        }
