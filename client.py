"""
LegalLens AI — OpenEnv Client
Standard OpenEnv HTTP client for LegalLensEnv.
"""
from __future__ import annotations
import httpx
from typing import Any, Dict, Optional


class LegalLensClient:
    """HTTP client for LegalLensEnv — OpenEnv compatible."""

    def __init__(self, base_url: str = "https://Adammyya-legallens-openenv.hf.space"):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=30.0)

    def reset(self, task_id: str = "task_1_easy") -> Dict[str, Any]:
        resp = self._client.post(f"{self.base_url}/reset", json={"task_id": task_id})
        resp.raise_for_status()
        return resp.json()

    def step(self, session_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"session_id": session_id, **action}
        resp = self._client.post(f"{self.base_url}/step", json=payload)
        resp.raise_for_status()
        return resp.json()

    def state(self, session_id: str) -> Dict[str, Any]:
        resp = self._client.get(f"{self.base_url}/state/{session_id}")
        resp.raise_for_status()
        return resp.json()

    def health(self) -> Dict[str, Any]:
        resp = self._client.get(f"{self.base_url}/health")
        resp.raise_for_status()
        return resp.json()

    def tasks(self) -> Dict[str, Any]:
        resp = self._client.get(f"{self.base_url}/tasks")
        resp.raise_for_status()
        return resp.json()

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# Quick test
if __name__ == "__main__":
    with LegalLensClient() as client:
        print("Health:", client.health())
        result = client.reset("task_1_easy")
        print("Session:", result["session_id"])
        print("Task:", result["task_id"])
