"""End-to-end verification script for Phase 2: Resume Ingestion and Parsing Pipeline."""

import io
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import fitz
import docx
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base, get_db
from tests.conftest import test_engine, TestingSessionLocal


def run_e2e_verification():
    print("=" * 70)
    print("STARTING END-TO-END VERIFICATION: PHASE 2 RESUME INGESTION PIPELINE")
    print("=" * 70)

    # Ensure clean database tables
    Base.metadata.create_all(bind=test_engine)

    # Override get_db dependency for standalone execution
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    # 1. Register Student User
    print("\n[Step 1] Registering student user...")
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "sarik.student@university.edu",
            "password": "SecurePassword2026!",
            "full_name": "Sarik Student",
        },
    )
    assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"
    auth_data = reg_resp.json()
    token = auth_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"  --> Registered successfully! User ID: {auth_data['user']['id']}")
    print(f"  --> JWT Token issued (length: {len(token)})")

    # 2. Upload Real PDF Resume
    print("\n[Step 2] Generating and uploading PDF resume (PyMuPDF)...")
    pdf_text = (
        "Sarik Student\n"
        "sarik.student@university.edu | (555) 789-0123 | San Jose, CA\n"
        "https://linkedin.com/in/sarikstudent | https://github.com/sarikstudent\n\n"
        "PROFESSIONAL SUMMARY\n"
        "Passionate full-stack AI engineer with strong expertise in building scalable REST APIs, "
        "PostgreSQL databases, and modern responsive frontends with React and TypeScript.\n\n"
        "EDUCATION\n"
        "Bachelor of Technology in Computer Science\n"
        "National Institute of Technology - 2026\n\n"
        "WORK EXPERIENCE\n"
        "Software Engineering Intern at CloudScale Inc\n"
        "Jun 2025 - Dec 2025\n"
        "Engineered document processing microservices with FastAPI and Celery. Reduced database query latency by 35%.\n\n"
        "PROJECTS\n"
        "SkillBridge AI Career Platform (Python, FastAPI, React, PostgreSQL)\n"
        "Developed an explainable resume matching and career path engine for students.\n"
        "Distributed Log Aggregator (Go, Docker, Kafka)\n"
        "Engineered a high-throughput streaming log ingestion pipeline.\n\n"
        "TECHNICAL SKILLS\n"
        "Python, FastAPI, TypeScript, React, PostgreSQL, Docker, Git, Linux, Tailwind CSS\n\n"
        "CERTIFICATIONS\n"
        "AWS Certified Cloud Practitioner by Amazon Web Services\n"
    )
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(40, 50), pdf_text)
    pdf_bytes = doc.tobytes()
    doc.close()

    upload_pdf_resp = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("sarik_resume.pdf", pdf_bytes, "application/pdf")},
        data={"title": "Sarik Technical Resume 2026"},
        headers=headers,
    )
    assert upload_pdf_resp.status_code == 201, f"PDF upload failed: {upload_pdf_resp.text}"
    pdf_data = upload_pdf_resp.json()
    print(f"  --> PDF Uploaded & Ingested! ID: {pdf_data['id']}")
    print(f"  --> Extraction Method: {pdf_data['extraction_method']}")
    print(f"  --> Character Count: {pdf_data['character_count']}")
    print(f"  --> Name: {pdf_data['personal_information']['name']}")
    print(f"  --> Email: {pdf_data['personal_information']['email']}")
    print(f"  --> LinkedIn: {pdf_data['personal_information']['linkedin_url']}")
    print(f"  --> Detected Sections: {[s['section_type'] for s in pdf_data['sections']]}")
    print(f"  --> Extracted Experience Entries: {len(pdf_data['experience'])}")
    print(f"  --> Extracted Projects: {len(pdf_data['projects'])}")
    print(f"  --> Extracted Certifications: {len(pdf_data['certifications'])}")

    assert pdf_data["personal_information"]["email"] == "sarik.student@university.edu"
    assert pdf_data["extraction_method"] == "TEXT"
    assert len(pdf_data["sections"]) >= 5

    # 3. Upload Real DOCX Resume
    print("\n[Step 3] Generating and uploading DOCX resume (python-docx)...")
    docx_doc = docx.Document()
    docx_doc.add_heading("Alex Rivera", level=0)
    docx_doc.add_paragraph("alex.rivera@example.com | 415-555-8899 | Seattle, WA | https://github.com/alexrivera")
    docx_doc.add_heading("CAREER OBJECTIVE", level=1)
    docx_doc.add_paragraph("Motivated backend engineer looking to design robust data pipelines.")
    docx_doc.add_heading("EDUCATION", level=1)
    docx_doc.add_paragraph("B.S. in Software Engineering - University of Washington, 2025")
    docx_doc.add_heading("WORK EXPERIENCE", level=1)
    docx_doc.add_paragraph("Junior Backend Developer at DataCorp\nJan 2024 - Present\nBuilt REST APIs with Python and PostgreSQL.")
    docx_doc.add_heading("TECHNICAL SKILLS", level=1)
    docx_doc.add_paragraph("Python, Django, FastAPI, PostgreSQL, Redis, Docker")
    buf = io.BytesIO()
    docx_doc.save(buf)
    docx_bytes = buf.getvalue()

    upload_docx_resp = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("alex_rivera.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=headers,
    )
    assert upload_docx_resp.status_code == 201, f"DOCX upload failed: {upload_docx_resp.text}"
    docx_data = upload_docx_resp.json()
    print(f"  --> DOCX Uploaded & Ingested! ID: {docx_data['id']}")
    print(f"  --> File Type: {docx_data['file_type']}")
    print(f"  --> Email: {docx_data['personal_information']['email']}")
    assert docx_data["file_type"] == "docx"
    assert docx_data["personal_information"]["email"] == "alex.rivera@example.com"

    # 4. List Resumes
    print("\n[Step 4] Querying GET /api/v1/resumes...")
    list_resp = client.get("/api/v1/resumes", headers=headers)
    assert list_resp.status_code == 200
    resumes_list = list_resp.json()
    print(f"  --> Total resumes in user account: {len(resumes_list)}")
    assert len(resumes_list) == 2

    # 5. Fetch Single Resume by ID
    print("\n[Step 5] Querying GET /api/v1/resumes/{id}...")
    first_id = pdf_data["id"]
    get_resp = client.get(f"/api/v1/resumes/{first_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == first_id
    print(f"  --> Successfully retrieved resume: {get_resp.json()['title']}")

    # 6. Delete One Resume
    print("\n[Step 6] Querying DELETE /api/v1/resumes/{id}...")
    del_resp = client.delete(f"/api/v1/resumes/{first_id}", headers=headers)
    assert del_resp.status_code == 204
    print("  --> Successfully deleted resume.")

    # Verify deletion
    after_del_resp = client.get(f"/api/v1/resumes/{first_id}", headers=headers)
    assert after_del_resp.status_code == 404
    print("  --> Confirmed 404 Not Found after deletion.")

    # 7. Check /api prefix compatibility
    print("\n[Step 7] Checking /api/resumes route alias...")
    alias_resp = client.get("/api/resumes", headers=headers)
    assert alias_resp.status_code == 200
    print("  --> /api/resumes alias verified (HTTP 200)!")

    print("\n" + "=" * 70)
    print("ALL 7 END-TO-END VERIFICATION STEPS PASSED PERFECTLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_e2e_verification()
