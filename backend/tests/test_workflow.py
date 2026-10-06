"""Small offline integration test for the upload → retrieve → stream → delete path."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class WorkflowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        root = Path(cls.temp.name)
        os.environ.update({
            "DATABASE_URL": f"sqlite:///{root / 'app.db'}",
            "CHROMA_PATH": str(root / "chroma"),
            "UPLOAD_DIR": str(root / "uploads"),
            "OPENAI_API_KEY": "offline-test-key",
        })
        from fastapi.testclient import TestClient
        from app.main import app
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.temp.cleanup()

    def test_pdf_and_markdown_upload(self):
        import pymupdf

        pdf = pymupdf.open()
        pdf.new_page().insert_text((72, 72), "RAG retrieves relevant document chunks.")
        pdf_bytes = pdf.tobytes()
        pdf.close()

        with patch("app.services.document_service.embed_texts", side_effect=lambda texts: [[1.0, 0.0, 0.0] for _ in texts]):
            pdf_response = self.client.post("/api/documents", files={"file": ("guide.pdf", pdf_bytes, "application/pdf")})
            md_response = self.client.post("/api/documents", files={"file": ("guide.md", b"# RAG\nRetrieval first.", "text/markdown")})
        self.assertEqual(pdf_response.status_code, 201, pdf_response.text)
        self.assertEqual(md_response.status_code, 201, md_response.text)
        self.assertGreater(pdf_response.json()["chunk_count"], 0)
        self.assertGreater(md_response.json()["chunk_count"], 0)
        for document_id in (pdf_response.json()["id"], md_response.json()["id"]):
            self.assertEqual(self.client.delete(f"/api/documents/{document_id}").status_code, 204)

    def test_upload_chat_history_and_delete(self):
        from app.services.document_service import get_collection

        def fake_embeddings(texts):
            return [[1.0, 0.0, 0.0] for _ in texts]

        async def fake_answer(_question, _context):
            yield "答案"
            yield " [1]"

        with patch("app.services.document_service.embed_texts", side_effect=fake_embeddings), \
             patch("app.services.rag_service.embed_texts", side_effect=fake_embeddings), \
             patch("app.api.chat.stream_answer", side_effect=fake_answer):
            response = self.client.post("/api/documents", files={"file": ("notes.txt", "期末项目是知识库系统。".encode(), "text/plain")})
            self.assertEqual(response.status_code, 201, response.text)
            document_id = response.json()["id"]
            self.assertGreater(response.json()["chunk_count"], 0)
            self.assertEqual(get_collection().count(), response.json()["chunk_count"])

            stats = self.client.get("/api/dashboard/stats").json()
            self.assertEqual(stats["document_count"], 1)
            self.assertEqual(stats["chunk_count"], response.json()["chunk_count"])

            stream = self.client.post("/api/chat/stream", json={"question": "期末项目是什么？"})
            self.assertEqual(stream.status_code, 200, stream.text)
            self.assertIn("event: token", stream.text)
            meta = json.loads(stream.text.split("event: meta\ndata: ")[1].split("\n\n")[0])
            self.assertEqual(meta["sources"][0]["file_name"], "notes.txt")
            conversation = self.client.get(f"/api/conversations/{meta['conversation_id']}").json()
            self.assertEqual([item["role"] for item in conversation["messages"]], ["user", "assistant"])
            self.assertEqual(conversation["messages"][1]["content"], "答案 [1]")

            self.assertEqual(self.client.delete(f"/api/documents/{document_id}").status_code, 204)
            self.assertEqual(get_collection().count(), 0)
            self.assertEqual(self.client.get("/api/dashboard/stats").json()["document_count"], 0)
            self.assertEqual(self.client.delete(f"/api/conversations/{meta['conversation_id']}").status_code, 204)
            self.assertEqual(self.client.get("/api/conversations").json(), [])


if __name__ == "__main__":
    unittest.main()
