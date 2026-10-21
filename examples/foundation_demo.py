"""Run the real API in-process with temporary storage and fictional data."""
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from deedee.api import create_app

def main():
    with tempfile.TemporaryDirectory() as directory:
        with TestClient(create_app(str(Path(directory) / "demo.db"))) as client:
            response = client.post("/api/v1/companies", json={"name": "Northstar Analytics", "industry": "Business software"})
            response.raise_for_status()
            company = response.json()
            response = client.post("/api/v1/contacts", json={
                "name": "Jordan Lee", "email": "jordan@example.com", "title": "Operations Lead",
                "company_id": company["id"], "tags": ["demo"]})
            response.raise_for_status()
            contact = response.json()
            selection = {"contact_ids": [contact["id"]], "company_ids": [company["id"]]}
            preview = client.post("/api/v1/ai/context", json=selection)
            preview.raise_for_status()
            print("Context preview:", preview.json())
            summary = client.post("/api/v1/ai/summarize", json=dict(selection, confirm=True))
            summary.raise_for_status()
            print("Suggestion:", summary.json())

if __name__ == "__main__":
    main()
