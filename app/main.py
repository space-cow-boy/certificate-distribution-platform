"""
FastAPI Certificate Distribution System
Main application with all API endpoints
"""

import os
from pathlib import Path
from typing import Dict, Any, List

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    # dotenv is optional on Render; env vars are injected there.
    pass

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.csv_handler import CSVHandler
from app.certificate_generator import CertificateGenerator


# Initialize FastAPI app
app = FastAPI(
    title="Certificate Distribution System",
    description="A system for generating and distributing certificates",
    version="1.0.0"
)

# ---- Environment / Paths (Render-friendly) ----

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = PROJECT_ROOT / "templates"

CSV_PATH = os.getenv("CSV_PATH", "students.csv")
CERTIFICATES_DIR = os.getenv("CERTIFICATES_DIR", "certificates")
TEMPLATE_IMAGE = os.getenv("CERTIFICATE_TEMPLATE_IMAGE", "templates/certificate_template.jpg")

# Admin key for protected endpoints (optional)
ADMIN_KEY = os.getenv("ADMIN_KEY", "")


def _as_abs(path_str: str) -> str:
    # Allow Windows-style env var paths (e.g., "data\\students.csv") even on Linux.
    normalized = (path_str or "").replace("\\", "/")
    p = Path(normalized)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return str(p)


# Add CORS middleware (configure allowed origins via env var)
origins_raw = os.getenv("CORS_ALLOW_ORIGINS", "*")
allow_origins: List[str] = [o.strip() for o in origins_raw.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins if allow_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"],
)


# Initialize handlers
csv_handler = CSVHandler(_as_abs(CSV_PATH), management_csv_path=_as_abs("management.csv"))
cert_generator = CertificateGenerator(
    template_path=_as_abs(TEMPLATE_IMAGE),
    output_dir=_as_abs(CERTIFICATES_DIR),
    management_template_path=_as_abs("templates/CertificateManagement.jpeg"),
)


# Serve templates directory as static (optional assets)
if TEMPLATES_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(TEMPLATES_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def home():
    """
    Serve the main HTML interface
    
    Returns:
        HTML page with certificate search form
    """
    html_path = TEMPLATES_DIR / "index.html"

    if not html_path.exists():
        raise HTTPException(status_code=500, detail="Template file not found")

    with open(html_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    return HTMLResponse(content=html_content)


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring
    
    Returns:
        Status message
    """
    csv_abs = _as_abs(CSV_PATH)
    template_abs = _as_abs(TEMPLATE_IMAGE)
    certificates_abs = _as_abs(CERTIFICATES_DIR)

    return {
        "status": "running",
        "paths": {
            "csv": csv_abs,
            "csv_exists": Path(csv_abs).exists(),
            "template_image": template_abs,
            "template_exists": Path(template_abs).exists(),
            "certificates_dir": certificates_abs,
            "certificates_dir_exists": Path(certificates_abs).exists(),
        },
    }


@app.get("/verify")
async def verify_certificate(name: str, student_id: str) -> Dict[str, Any]:
    """
    Verify a certificate and return student information
    
    Args:
        name: The student's name
        student_id: The student's ID
        
    Returns:
        Student information and validity status
        
    Raises:
        HTTPException: If student not found
    """
    try:
        student = csv_handler.find_student_by_name_and_id(name, student_id)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Student database CSV not available: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while verifying student: {str(e)}",
        )
    
    if not student:
        raise HTTPException(
            status_code=404, 
            detail=f"Student not found with name: {name} and ID: {student_id}"
        )
    
    certificate_id = csv_handler.generate_certificate_id(student.get("Student_Id"), student.get("Name"))
    
    return {
        "name": student.get("Name"),
        "email": student.get("Email_id"),
        "student_id": student.get("Student_Id"),
        "course": student.get("Course"),
        "certificate_id": certificate_id,
        "valid": True
    }



@app.get("/certificate")
async def get_certificate(
    name: str,
    student_id: str,
    force: bool = Query(False, description="Regenerate the certificate PDF even if it already exists"),
):
    """
    Generate certificate if not exists and return as downloadable PDF
    
    Args:
        name: The student's name
        student_id: The student's ID
        
    Returns:
        PDF file as download
        
    Raises:
        HTTPException: If student not found in database
    """
    # Verify student exists
    try:
        student = csv_handler.find_student_by_name_and_id(name, student_id)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Student database CSV not available: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while looking up student: {str(e)}",
        )
    
    if not student:
        raise HTTPException(
            status_code=404,
            detail=f"Student not found with name: {name} and ID: {student_id}"
        )
    
    # Generate certificate ID
    certificate_id = csv_handler.generate_certificate_id(student.get("Student_Id"), student.get("Name"))
    
    # Render/WebService: cache PDFs on disk
    if force or (not cert_generator.certificate_exists(certificate_id)):
        try:
            cert_generator.generate_certificate(
                student_name=student.get("Name"),
                certificate_id=certificate_id,
                course=None,  # Don't include course in student certificates
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating certificate: {str(e)}")

    cert_path = cert_generator.get_certificate_path(certificate_id)
    return FileResponse(path=cert_path, media_type="application/pdf", filename=f"{certificate_id}.pdf")


@app.get("/generate-all")
async def generate_all_certificates(admin_key: str = Query(..., description="Admin key for authorization")) -> Dict[str, Any]:
    """
    Admin endpoint to generate all certificates from CSV
    Protected by admin key
    
    Args:
        admin_key: Admin authorization key
        
    Returns:
        Summary of generated certificates
        
    Raises:
        HTTPException: If admin key is invalid or generation fails
    """
    # Verify admin key (only enforced if ADMIN_KEY is set)
    if ADMIN_KEY and admin_key != ADMIN_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid admin key"
        )
    
    try:
        students = csv_handler.get_all_students()
        generated = []
        skipped = []
        
        for student in students:
            student_id = student.get("Student_Id")
            name = student.get("Name")
            
            # Generate certificate ID
            certificate_id = csv_handler.generate_certificate_id(student_id, name)
            
            # Skip if already exists
            if cert_generator.certificate_exists(certificate_id):
                skipped.append(certificate_id)
                continue
            
            # Generate certificate
            cert_generator.generate_certificate(
                student_name=name,
                certificate_id=certificate_id,
                course=student.get("Course"),
            )
            generated.append(certificate_id)
        
        return {
            "success": True,
            "total_students": len(students),
            "generated": len(generated),
            "skipped": len(skipped),
            "generated_ids": generated,
            "skipped_ids": skipped
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating certificates: {str(e)}"
        )


@app.get("/verify-management")
async def verify_management_certificate(name: str, mgmt_id: str) -> Dict[str, Any]:
    """
    Verify a management team member and return their information
    
    Args:
        name: The person's name
        mgmt_id: The management ID
        
    Returns:
        Management member information and validity status
        
    Raises:
        HTTPException: If person not found
    """
    try:
        person = csv_handler.find_management_by_name_and_id(name, mgmt_id)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Management database CSV not available: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while verifying management member: {str(e)}",
        )
    
    if not person:
        raise HTTPException(
            status_code=404, 
            detail=f"Management member not found with name: {name} and ID: {mgmt_id}"
        )
    
    certificate_id = csv_handler.generate_management_certificate_id(person.get("Student_Id"), person.get("Name"))
    
    return {
        "name": person.get("Name"),
        "email": person.get("Email_id"),
        "position": person.get("Position"),
        "certificate_id": certificate_id,
        "valid": True
    }


@app.get("/certificate-management")
async def get_management_certificate(
    name: str,
    mgmt_id: str,
    force: bool = Query(False, description="Regenerate the certificate PDF even if it already exists"),
):
    """
    Generate management certificate if not exists and return as downloadable PDF
    
    Args:
        name: The person's name
        mgmt_id: The management ID
        force: Whether to regenerate even if exists
        
    Returns:
        PDF file as download
        
    Raises:
        HTTPException: If person not found in database
    """
    # Verify person exists
    try:
        person = csv_handler.find_management_by_name_and_id(name, mgmt_id)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Management database CSV not available: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while looking up management member: {str(e)}",
        )
    
    if not person:
        raise HTTPException(
            status_code=404,
            detail=f"Management member not found with name: {name} and ID: {mgmt_id}"
        )
    
    # Generate certificate ID
    certificate_id = csv_handler.generate_management_certificate_id(person.get("Student_Id"), person.get("Name"))
    
    # Cache PDFs on disk
    if force or (not cert_generator.certificate_exists(certificate_id)):
        try:
            cert_generator.generate_management_certificate(
                person_name=person.get("Name"),
                certificate_id=certificate_id,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating management certificate: {str(e)}")

    cert_path = cert_generator.get_certificate_path(certificate_id)
    return FileResponse(path=cert_path, media_type="application/pdf", filename=f"{certificate_id}.pdf")


@app.get("/generate-all-management")
async def generate_all_management_certificates(admin_key: str = Query(..., description="Admin key for authorization")) -> Dict[str, Any]:
    """
    Admin endpoint to generate all management certificates from CSV
    Protected by admin key
    
    Args:
        admin_key: Admin authorization key
        
    Returns:
        Summary of generated certificates
        
    Raises:
        HTTPException: If admin key is invalid or generation fails
    """
    # Verify admin key (only enforced if ADMIN_KEY is set)
    if ADMIN_KEY and admin_key != ADMIN_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid admin key"
        )
    
    try:
        management = csv_handler.get_all_management()
        generated = []
        skipped = []
        
        for person in management:
            mgmt_id = person.get("Student_Id")
            name = person.get("Name")
            certificate_id = csv_handler.generate_management_certificate_id(mgmt_id, name)
            
            # Skip if already exists
            if cert_generator.certificate_exists(certificate_id):
                skipped.append(certificate_id)
                continue
            
            # Generate certificate
            cert_generator.generate_management_certificate(
                person_name=name,
                certificate_id=certificate_id
            )
            generated.append(certificate_id)
        
        return {
            "success": True,
            "total_management": len(management),
            "generated": len(generated),
            "skipped": len(skipped),
            "generated_ids": generated,
            "skipped_ids": skipped
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating management certificates: {str(e)}"
        )


# Run with: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
