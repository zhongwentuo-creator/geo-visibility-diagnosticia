from __future__ import annotations

import importlib
import os
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
FIXTURE_ENGINE = Path(__file__).parent / "fixtures" / "engine"
sys.path.insert(0, str(SRC_ROOT))
os.environ["GEO_ENGINE_ROOT"] = str(FIXTURE_ENGINE)
api = importlib.import_module("api")


class DiagnosisApiTest(unittest.TestCase):
    def setUp(self) -> None:
        api._tasks.clear()
        self.client = TestClient(api.app)

    def _start(self, brand: str = "听力熊") -> str:
        response = self.client.post("/api/diagnose", json={"brand": brand, "category": "儿童 AI 对话智能体"})
        self.assertEqual(response.status_code, 200)
        return response.json()["task_id"]

    def test_health_and_workspace_are_served_from_one_origin(self) -> None:
        self.assertEqual(self.client.get("/health").json()["status"], "ok")
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("GEO 可见度诊断师", page.text)

    def test_sse_sequence_and_reports(self) -> None:
        task_id = self._start()
        with self.client.stream("GET", f"/api/diagnose/{task_id}/stream") as response:
            self.assertEqual(response.status_code, 200)
            payload = "".join(response.iter_text())

        self.assertIn("event: start", payload)
        self.assertEqual(payload.count("event: stage_start"), 9)
        self.assertEqual(payload.count("event: stage_complete"), 9)
        self.assertIn("event: complete", payload)
        self.assertLess(payload.index("event: start"), payload.index("event: complete"))
        self.assertEqual(self.client.get(f"/api/diagnose/{task_id}").json()["status"], "success")
        self.assertEqual(self.client.get(f"/api/diagnose/{task_id}/report").json()["aivoScore"]["total"], 74)
        self.assertEqual(self.client.get(f"/api/diagnose/{task_id}/report/html").status_code, 200)

    def test_engine_error_is_reported_without_a_broken_stream(self) -> None:
        task_id = self._start("错误品牌")
        with self.client.stream("GET", f"/api/diagnose/{task_id}/stream") as response:
            payload = "".join(response.iter_text())
        self.assertIn("event: error", payload)
        status = self.client.get(f"/api/diagnose/{task_id}").json()
        self.assertEqual(status["status"], "error")
        self.assertIn("测试引擎故障", status["error"])


if __name__ == "__main__":
    unittest.main()
