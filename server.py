import os
import uvicorn
import hashlib
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from database import engine, Base, get_db, SessionLocal
import models

def generate_security_hash(user_name: str, action: str, target_id: str, details: str, timestamp_str: str) -> str:
    content = f"{user_name}|{action}|{target_id}|{details}|{timestamp_str}|MEDREACH_LEDGER_2026"
    return hashlib.sha256(content.encode()).hexdigest()[:16]

AUTHORIZED_USERS = [
    {
        "id": "USR-ADM",
        "name": "System Administrator",
        "role": "System Administrator",
        "employeeId": "ADM-1001",
        "email": "admin@medreach.com",
        "phone": "+91 98000 00001",
        "digitsPhone": "9800000001",
        "passwords": ["medreach@2026", "admin@2026", "ash@123"],
        "vehicle": "HQ-ADMIN-01",
        "isReadOnly": False,
        "canManageUsers": True
    },
    {
        "id": "USR-REC",
        "name": "Front-Desk Reception",
        "role": "Front-Desk Receptionist",
        "employeeId": "REC-2001",
        "email": "reception@medreach.com",
        "phone": "+91 98000 00002",
        "digitsPhone": "9800000002",
        "passwords": ["medreach@2026", "reception@2026"],
        "vehicle": "N/A",
        "isReadOnly": False,
        "canManageUsers": False
    },
    {
        "id": "USR-SUP",
        "name": "Nursing Supervisor",
        "role": "Nursing Supervisor",
        "employeeId": "NUR-3001",
        "email": "supervisor@medreach.com",
        "phone": "+91 98000 00003",
        "digitsPhone": "9800000003",
        "passwords": ["medreach@2026", "supervisor@2026"],
        "vehicle": "KA-01-NS-3001",
        "isReadOnly": False,
        "canManageUsers": False
    },
    {
        "id": "USR-AUD",
        "name": "Compliance Auditor",
        "role": "Compliance Auditor",
        "employeeId": "AUD-4001",
        "email": "auditor@medreach.com",
        "phone": "+91 98000 00004",
        "digitsPhone": "9800000004",
        "passwords": ["medreach@2026", "auditor@2026"],
        "vehicle": "N/A",
        "isReadOnly": True,
        "canManageUsers": False
    },
    {
        "id": "USR-101",
        "name": "Ashwin Kumar",
        "role": "Field Phlebotomist Lead",
        "employeeId": "EMP-9342",
        "email": "ashwinkumaar65@gmail.com",
        "alternateEmail": "ashwinkumar65@gmail.com",
        "phone": "+91 9342600642",
        "digitsPhone": "9342600642",
        "passwords": ["ash@123", "Ash@123", "Ashwin@2005", "medreach@2026"],
        "vehicle": "KA-05-MK-4421",
        "isReadOnly": False,
        "canManageUsers": False
    },
    {
        "id": "USR-105",
        "name": "Ashok Pandian",
        "role": "Senior Field Executive",
        "employeeId": "EMP-8842",
        "email": "ashok.field@medreach.com",
        "phone": "+91 9444155667",
        "digitsPhone": "9444155667",
        "passwords": ["ashok@123", "Ashok@123", "password123", "medreach@2026"],
        "vehicle": "KA-05-MK-4421",
        "isReadOnly": False,
        "canManageUsers": False
    }
]

def seed_default_data():
    db = SessionLocal()
    try:
        user_count = db.query(models.User).count()
        if user_count == 0:
            default_user = models.User(
                id="USR-101",
                username="ashok.field@medreach.com",
                password_hash="password123",
                name="Ashok Pandian",
                role="Field Phlebotomist Lead",
                employee_id="EMP-8842",
                phone="+91 98765 43210",
                vehicle_number="KA-05-MK-4421"
            )
            db.add(default_user)

        center_count = db.query(models.DiagnosticCenter).count()
        if center_count == 0:
            centers = [
                models.DiagnosticCenter(id="DC-P1", name="MedReach Central Processing Lab - Koramangala", type="processing", address="80 Feet Road, 4th Block, Koramangala", city="Bengaluru"),
                models.DiagnosticCenter(id="DC-P2", name="MedReach Bio-Reference Center - Whitefield", type="processing", address="ITPL Main Road, Whitefield", city="Bengaluru"),
                models.DiagnosticCenter(id="DC-C1", name="Indiranagar Collection Clinic - 100ft Road", type="collection", address="Near Metro Pillar 84, Indiranagar", city="Bengaluru"),
                models.DiagnosticCenter(id="DC-C2", name="HSR Layout Diagnostic Point - Sector 2", type="collection", address="27th Main, Sector 2, HSR Layout", city="Bengaluru"),
                models.DiagnosticCenter(id="DC-C3", name="Jayanagar Health Point - 4th Block", type="collection", address="11th Main, 4th Block, Jayanagar", city="Bengaluru"),
            ]
            db.add_all(centers)

        task_count = db.query(models.Task).count()
        if task_count == 0:
            t1 = models.Task(
                id="TSK-201",
                patient_id="PAT-901",
                patient_name="Priya Venkatesh",
                patient_phone="+91 94432 11098",
                patient_age=34,
                patient_gender="Female",
                address="Flat 4/B, Sunrise Apts, Koramangala 5th Block",
                distance_km=1.2,
                scheduled_date="Today",
                scheduled_time="09:30 AM",
                status="pending",
                payment_status="paid",
                total_amount=1250.0,
                container_temperature=-2.0,
                reference_number="REF-PV-8812"
            )
            g1 = models.TaskTestGroup(id="GRP-101", task_id="TSK-201", title="Complete Blood Count (CBC)", tube_type="EDTA (Purple Cap)")
            g1.tests = [
                models.GroupTestItem(id="TI-1", group_id="GRP-101", name="Hemoglobin (Hb)", is_selected=True),
                models.GroupTestItem(id="TI-2", group_id="GRP-101", name="RBC Count", is_selected=True),
                models.GroupTestItem(id="TI-3", group_id="GRP-101", name="Platelet Count", is_selected=True),
                models.GroupTestItem(id="TI-4", group_id="GRP-101", name="WBC & Differential", is_selected=True),
            ]
            g2 = models.TaskTestGroup(id="GRP-102", task_id="TSK-201", title="Lipid Profile & Serum Chemistries", tube_type="Serum (Red / Gold Cap)")
            g2.tests = [
                models.GroupTestItem(id="TI-5", group_id="GRP-102", name="Total Cholesterol", is_selected=True),
                models.GroupTestItem(id="TI-6", group_id="GRP-102", name="Triglycerides", is_selected=True),
                models.GroupTestItem(id="TI-7", group_id="GRP-102", name="HDL & LDL Ratio", is_selected=True),
            ]
            t1.test_groups = [g1, g2]

            t2 = models.Task(
                id="TSK-202",
                patient_id="PAT-902",
                patient_name="Rajesh Sharma",
                patient_phone="+91 98841 77234",
                patient_age=48,
                patient_gender="Male",
                address="Plot 102, Green Glen Layout, Bellandur",
                distance_km=2.4,
                scheduled_date="Today",
                scheduled_time="10:15 AM",
                status="pending",
                payment_status="pending",
                total_amount=850.0,
                container_temperature=-2.0,
                reference_number="REF-RS-4401"
            )
            g3 = models.TaskTestGroup(id="GRP-103", task_id="TSK-202", title="Diabetic Health Panel", tube_type="Fluoride (Grey Cap)")
            g3.tests = [
                models.GroupTestItem(id="TI-8", group_id="GRP-103", name="Fasting Blood Glucose", is_selected=True),
                models.GroupTestItem(id="TI-9", group_id="GRP-103", name="HbA1c Glycated Hemoglobin", is_selected=True),
            ]
            t2.test_groups = [g3]

            t3 = models.Task(
                id="TSK-203",
                patient_id="PAT-903",
                patient_name="Anita Rao",
                patient_phone="+91 97711 55092",
                patient_age=52,
                patient_gender="Female",
                address="32, 14th Main, HSR Layout Sector 4",
                distance_km=3.1,
                scheduled_date="Today",
                scheduled_time="11:00 AM",
                status="pending",
                payment_status="paid",
                total_amount=1600.0,
                container_temperature=-2.0,
                reference_number="REF-AR-1920"
            )
            g4 = models.TaskTestGroup(id="GRP-104", task_id="TSK-203", title="Thyroid Profile (Total T3, T4, TSH)", tube_type="Serum (Red Cap)")
            g4.tests = [
                models.GroupTestItem(id="TI-10", group_id="GRP-104", name="TSH Ultrasensitive", is_selected=True),
                models.GroupTestItem(id="TI-11", group_id="GRP-104", name="Free T3", is_selected=True),
                models.GroupTestItem(id="TI-12", group_id="GRP-104", name="Free T4", is_selected=True),
            ]
            t3.test_groups = [g4]

            t4 = models.Task(
                id="TSK-204",
                patient_id="PAT-904",
                patient_name="Suresh Kumar",
                patient_phone="+91 91234 56780",
                patient_age=29,
                patient_gender="Male",
                address="77, 80ft Road, Indiranagar",
                distance_km=0.8,
                scheduled_date="Today",
                scheduled_time="08:00 AM",
                status="completed",
                payment_status="paid",
                total_amount=950.0,
                barcode="MED-393420194",
                reference_number="REF-SK-1102"
            )

            db.add_all([t1, t2, t3, t4])

        # Seed Multiple Authorized Users
        existing_usernames = {u.username for u in db.query(models.User.username).all()}
        users_to_add = []
        for u in AUTHORIZED_USERS:
            if u["email"] not in existing_usernames:
                users_to_add.append(models.User(
                    id=u["id"],
                    username=u["email"],
                    password_hash=u["passwords"][0],
                    name=u["name"],
                    role=u["role"],
                    employee_id=u["employeeId"],
                    phone=u["phone"],
                    vehicle_number=u.get("vehicle", "KA-05-MK-4421")
                ))
        if users_to_add:
            db.add_all(users_to_add)

        # Seed Initial Audit Log Records
        audit_count = db.query(models.AuditLog).count()
        if audit_count == 0:
            now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            initial_logs = [
                models.AuditLog(
                    id="AUD-1001",
                    timestamp=datetime.utcnow(),
                    user_id="USR-101",
                    user_name="Ashwin Kumar",
                    user_role="Field Phlebotomist Lead",
                    employee_id="EMP-9342",
                    action="COLLECTION_COMPLETED",
                    target_id="TSK-204",
                    target_name="Suresh Kumar",
                    details="Completed home specimen collection: 2 EDTA + 1 Serum tube. Cold chain verified at -2.0°C. Verified via patient OTP.",
                    ip_address="192.168.1.45",
                    security_hash=generate_security_hash("Ashwin Kumar", "COLLECTION_COMPLETED", "TSK-204", "Completed home collection", now_str)
                ),
                models.AuditLog(
                    id="AUD-1002",
                    timestamp=datetime.utcnow(),
                    user_id="USR-101",
                    user_name="Ashwin Kumar",
                    user_role="Field Phlebotomist Lead",
                    employee_id="EMP-9342",
                    action="BARCODE_LINKED",
                    target_id="TSK-204",
                    target_name="Suresh Kumar",
                    details="Specimen vial barcode MED-393420194 scanned and bound to LIMS accession record.",
                    ip_address="192.168.1.45",
                    security_hash=generate_security_hash("Ashwin Kumar", "BARCODE_LINKED", "TSK-204", "Barcode MED-393420194 bound", now_str)
                ),
                models.AuditLog(
                    id="AUD-1003",
                    timestamp=datetime.utcnow(),
                    user_id="USR-101",
                    user_name="Ashwin Kumar",
                    user_role="Field Phlebotomist Lead",
                    employee_id="EMP-9342",
                    action="PAYMENT_RECORDED",
                    target_id="TSK-204",
                    target_name="Suresh Kumar",
                    details="Collected Rs. 950.00 via UPI QR. Txn Ref: UPI-8409210923.",
                    ip_address="192.168.1.45",
                    security_hash=generate_security_hash("Ashwin Kumar", "PAYMENT_RECORDED", "TSK-204", "Collected Rs 950 via UPI", now_str)
                ),
                models.AuditLog(
                    id="AUD-1004",
                    timestamp=datetime.utcnow(),
                    user_id="USR-103",
                    user_name="Rajesh Sharma",
                    user_role="Central Dispatch & Logistics Lead",
                    employee_id="EMP-4021",
                    action="BATCH_HANDOVER",
                    target_id="RAM1001",
                    target_name="Indiranagar Collection Clinic",
                    details="Received Batch manifest RAM1001 from Indiranagar clinic. 4 tubes received at -1.9°C.",
                    ip_address="192.168.1.12",
                    security_hash=generate_security_hash("Rajesh Sharma", "BATCH_HANDOVER", "RAM1001", "Batch manifest RAM1001 received", now_str)
                ),
                models.AuditLog(
                    id="AUD-1005",
                    timestamp=datetime.utcnow(),
                    user_id="USR-104",
                    user_name="Priya Nair",
                    user_role="Quality & Cold-Chain Auditor",
                    employee_id="EMP-3055",
                    action="COLD_CHAIN_AUDIT",
                    target_id="BX-NEO-94",
                    target_name="Smart Cooler Box 94",
                    details="Quarterly container calibration verified. Smart Peltier Box BX-NEO-94 passed cold-integrity audit (-2.0°C compliant).",
                    ip_address="192.168.1.18",
                    security_hash=generate_security_hash("Priya Nair", "COLD_CHAIN_AUDIT", "BX-NEO-94", "Smart Box passed audit", now_str)
                ),
                models.AuditLog(
                    id="AUD-1006",
                    timestamp=datetime.utcnow(),
                    user_id="USR-102",
                    user_name="Dr. Kavitha Sundaram",
                    user_role="Chief Pathologist & Lab Director",
                    employee_id="EMP-1001",
                    action="USER_LOGIN",
                    target_id="SYS-AUTH",
                    target_name="Central Laboratory Workstation",
                    details="Chief Pathologist authenticated to Web Portal with Director permissions.",
                    ip_address="192.168.1.10",
                    security_hash=generate_security_hash("Dr. Kavitha Sundaram", "USER_LOGIN", "SYS-AUTH", "Chief Pathologist authenticated", now_str)
                )
            ]
            db.add_all(initial_logs)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[WARN] Seeding note: {e}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[INFO] Setting up MedReach Web database tables...")
    Base.metadata.create_all(bind=engine)
    seed_default_data()
    print("[OK] MedReach Web Server is ready!")
    yield


app = FastAPI(
    title="MedReach Field Diagnostics Suite (Web Application)",
    description="Interactive Web Application and REST API in Python for MedReach Field Phlebotomy & Diagnostics.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)


class LoginRequest(BaseModel):
    username: str
    password: str

class BarcodeAssignRequest(BaseModel):
    barcode: str

class CenterCollectionRequest(BaseModel):
    processingCenter: str
    collectionCenter: str
    referenceNumber: str
    batchsheetBarcode: str
    noOfContainers: int
    actualContainers: int
    temperature: float = -2.0

class TemperatureRequest(BaseModel):
    temperature: float

class AuditLogCreateRequest(BaseModel):
    user_name: str
    user_role: str
    employee_id: Optional[str] = None
    action: str
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    details: str

class TaskRejectRequest(BaseModel):
    reason: str
    notes: Optional[str] = None
    user_name: Optional[str] = "Ashwin Kumar"
    user_role: Optional[str] = "Field Phlebotomist Lead"
    employee_id: Optional[str] = "EMP-9342"

class TaskCreateRequest(BaseModel):
    patient_name: str
    patient_phone: str
    patient_age: int
    patient_gender: str
    address: str
    distance_km: float = 2.0
    scheduled_time: str = "10:30 AM"
    assays: str = "CBC + Fasting Blood Sugar"
    amount: float = 750.0
    assigned_to: str = "Ashwin Kumar"
    user_name: Optional[str] = "Front-Desk Reception"
    user_role: Optional[str] = "Front-Desk Receptionist"
    employee_id: Optional[str] = "REC-2001"


@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if request.method == "HEAD":
        return HTMLResponse(status_code=200)
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/home", response_class=HTMLResponse)
def home_page(request: Request):
    return templates.TemplateResponse(request=request, name="home.html")

@app.get("/patient-detail", response_class=HTMLResponse)
def patient_detail_page(request: Request, id: Optional[str] = "TK-209312", barcode: Optional[str] = None):
    return templates.TemplateResponse(request=request, name="patient_detail.html", context={"id": id, "barcode": barcode})

@app.get("/collect-payment", response_class=HTMLResponse)
def collect_payment_page(request: Request):
    return templates.TemplateResponse(request=request, name="collect_payment.html")

@app.get("/payment-success", response_class=HTMLResponse)
def payment_success_page(request: Request, method: Optional[str] = "Cash"):
    return templates.TemplateResponse(request=request, name="payment_success.html", context={"method": method})

@app.get("/reject-reassign", response_class=HTMLResponse)
def reject_reassign_page(request: Request, id: Optional[str] = "TK-209312"):
    return templates.TemplateResponse(request=request, name="reject_reassign.html", context={"id": id})

@app.get("/center-collection", response_class=HTMLResponse)
def center_collection_page(request: Request, ref: Optional[str] = "RAM1001"):
    return templates.TemplateResponse(request=request, name="center_collection.html", context={"ref_no": ref})

@app.get("/scanner", response_class=HTMLResponse)
def scanner_page(request: Request, target: Optional[str] = "center"):
    return_url = "/patient-detail" if target == "patient" else "/center-collection"
    return templates.TemplateResponse(request=request, name="scanner.html", context={"target": target, "return_url": return_url})

@app.get("/notifications", response_class=HTMLResponse)
def notifications_page(request: Request):
    return templates.TemplateResponse(request=request, name="notifications.html")

@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    return templates.TemplateResponse(request=request, name="profile.html")

@app.get("/audit-logs", response_class=HTMLResponse)
def audit_logs_page(request: Request):
    return templates.TemplateResponse(request=request, name="audit_logs.html")

@app.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse(request=request, name="forgot_password.html")

@app.get("/verify-otp", response_class=HTMLResponse)
def verify_otp_page(request: Request):
    return templates.TemplateResponse(request=request, name="verify_otp.html")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    favicon_path = os.path.join(static_dir, "images", "favicon.svg")
    if os.path.exists(favicon_path):
        from fastapi.responses import FileResponse
        return FileResponse(favicon_path, media_type="image/svg+xml")
    from fastapi.responses import Response
    return Response(status_code=204)

@app.get("/health")
def health():
    return {
        "status": "UP",
        "service": "MedReach Web Application",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "MySQL / SQLite Fallback"
    }
@app.post("/api/auth/login")
def api_login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    clean_user = req.username.strip().lower()
    clean_pass = req.password.strip()
    digits_only = clean_user.replace(" ", "").replace("+91", "").replace("-", "")

    print(f"\n[AUTH ATTEMPT] Received: username={req.username!r}, password={'*' * len(req.password)}")

    # 1. Look for matching user in AUTHORIZED_USERS
    matched_user = None
    for u in AUTHORIZED_USERS:
        is_match = (
            clean_user == u["email"].lower() or
            clean_user == u.get("alternateEmail", "").lower() or
            clean_user == u["phone"].lower() or
            (digits_only and digits_only == u.get("digitsPhone", "")) or
            (digits_only and u.get("digitsPhone", "") and digits_only == u["digitsPhone"])
        )
        if is_match:
            matched_user = u
            break

    # Also check database models.User if not in in-memory list
    if not matched_user:
        db_user = db.query(models.User).filter(
            (models.User.username == clean_user) | (models.User.phone == req.username.strip())
        ).first()
        if db_user:
            matched_user = {
                "id": db_user.id,
                "name": db_user.name,
                "role": db_user.role,
                "employeeId": db_user.employee_id,
                "email": db_user.username,
                "phone": db_user.phone,
                "passwords": [db_user.password_hash]
            }

    # Collect all valid passwords across system for granular diagnosis
    all_allowed_passwords = {p for u in AUTHORIZED_USERS for p in u["passwords"]}
    pass_matches_any = clean_pass in all_allowed_passwords

    if not matched_user:
        print(f"[AUTH FAILED] ❌ User not found: {req.username}")
        if pass_matches_any:
            raise HTTPException(status_code=401, detail="Wrong email or mobile number.")
        else:
            raise HTTPException(status_code=401, detail="Invalid email/mobile number or password.")

    # User exists: verify password specifically for this user
    if clean_pass not in matched_user["passwords"]:
        print(f"[AUTH FAILED] ❌ Wrong password for user: {matched_user['name']}")
        raise HTTPException(status_code=401, detail="Wrong password.")

    # Login SUCCESS: Record tamper-evident Audit Log
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    client_ip = request.client.host if request.client else "127.0.0.1"
    audit_id = f"AUD-{int(datetime.utcnow().timestamp() * 1000)}"
    log_entry = models.AuditLog(
        id=audit_id,
        timestamp=datetime.utcnow(),
        user_id=matched_user["id"],
        user_name=matched_user["name"],
        user_role=matched_user["role"],
        employee_id=matched_user["employeeId"],
        action="USER_LOGIN",
        target_id="SYS-PORTAL",
        target_name=matched_user["name"],
        details=f"{matched_user['role']} signed in successfully to Field Portal.",
        ip_address=client_ip,
        security_hash=generate_security_hash(matched_user["name"], "USER_LOGIN", "SYS-PORTAL", "signed in", now_str)
    )
    db.add(log_entry)
    db.commit()

    print(f"[AUTH SUCCESS] 👤 User identified: {matched_user['name']} ({matched_user['role']}) logged in at {now_str}\n")
    return {
        "success": True,
        "user": {
            "id": matched_user["id"],
            "name": matched_user["name"],
            "role": matched_user["role"],
            "email": matched_user["email"],
            "employeeId": matched_user["employeeId"],
            "phone": matched_user["phone"],
            "isReadOnly": matched_user.get("isReadOnly", False),
            "canManageUsers": matched_user.get("canManageUsers", False)
        }
    }

@app.get("/api/dashboard/stats")
def api_dashboard_stats(db: Session = Depends(get_db)):
    pending_count = db.query(models.Task).filter(models.Task.status == "pending").count()
    completed_count = db.query(models.Task).filter(models.Task.status == "completed").count()
    total_collections = pending_count + completed_count + 18 # base count matching mobile mock
    
    return {
        "success": True,
        "data": {
            "todayCollectionCount": total_collections,
            "containerTemperature": -2.0,
            "tubesCollected": {
                "edta": 6,
                "citrate": 6,
                "serum": 2,
                "other": 10
            },
            "statusCards": {
                "collected": 18 + completed_count,
                "pending": max(0, pending_count),
                "routeKms": 12.4
            }
        }
    }

@app.get("/api/tasks")
def api_get_tasks(status: Optional[str] = None, search: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Task)
    if status and status != "all":
        query = query.filter(models.Task.status == status)
    
    tasks = query.all()
    results = []
    for t in tasks:
        if search:
            s = search.lower()
            if s not in t.patient_name.lower() and s not in (t.reference_number or "").lower():
                continue
        
        groups = []
        for g in t.test_groups:
            groups.append({
                "id": g.id,
                "title": g.title,
                "tubeType": g.tube_type,
                "tests": [{"id": ti.id, "name": ti.name, "isSelected": ti.is_selected} for ti in g.tests]
            })

        results.append({
            "id": t.id,
            "patientId": t.patient_id,
            "patientName": t.patient_name,
            "patientPhone": t.patient_phone,
            "patientAge": t.patient_age,
            "patientGender": t.patient_gender,
            "address": t.address,
            "distanceKm": t.distance_km,
            "scheduledDate": t.scheduled_date,
            "scheduledTime": t.scheduled_time,
            "status": t.status,
            "paymentStatus": t.payment_status,
            "totalAmount": t.total_amount,
            "barcode": t.barcode,
            "referenceNumber": t.reference_number,
            "testGroups": groups
        })
    return {"success": True, "count": len(results), "tasks": results}

@app.post("/api/tasks")
def api_create_task(req: TaskCreateRequest, request: Request, db: Session = Depends(get_db)):
    task_id = f"TK-{int(datetime.utcnow().timestamp()) % 1000000}"
    new_task = models.Task(
        id=task_id,
        patient_id=f"PAT-{int(datetime.utcnow().timestamp()) % 10000}",
        patient_name=req.patient_name,
        patient_phone=req.patient_phone,
        patient_age=req.patient_age,
        patient_gender=req.patient_gender,
        address=req.address,
        distance_km=req.distance_km,
        scheduled_date="Today",
        scheduled_time=req.scheduled_time,
        status="pending",
        payment_status="pending",
        total_amount=req.amount,
        container_temperature=-2.0,
        reference_number=f"RAM{int(datetime.utcnow().timestamp()) % 10000}",
        reassigned_to=req.assigned_to
    )
    grp = models.TaskTestGroup(
        id=f"GRP-{task_id}",
        task_id=task_id,
        title=req.assays,
        tube_type="EDTA (Purple Cap) + Serum (Gold Cap)"
    )
    new_task.test_groups = [grp]
    db.add(new_task)

    # Log to Security Audit Ledger
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    client_ip = request.client.host if request.client else "127.0.0.1"
    audit_id = f"AUD-{int(datetime.utcnow().timestamp() * 1000)}"
    details = f"Booked home collection for {req.patient_name} ({req.patient_age}Y/{req.patient_gender}). Assays: {req.assays}. Assigned to: {req.assigned_to}."
    hash_sig = generate_security_hash(req.user_name or "Reception", "TASK_BOOKED", task_id, details, now_str)

    audit_entry = models.AuditLog(
        id=audit_id,
        timestamp=datetime.utcnow(),
        user_id=req.employee_id or "REC-2001",
        user_name=req.user_name or "Front-Desk Reception",
        user_role=req.user_role or "Front-Desk Receptionist",
        employee_id=req.employee_id or "REC-2001",
        action="TASK_BOOKED",
        target_id=task_id,
        target_name=req.patient_name,
        details=details,
        ip_address=client_ip,
        security_hash=hash_sig
    )
    db.add(audit_entry)
    db.commit()

    return {
        "success": True,
        "message": f"Task {task_id} booked successfully for {req.patient_name}",
        "task": {
            "id": new_task.id,
            "patientName": new_task.patient_name,
            "patientAge": new_task.patient_age,
            "patientGender": new_task.patient_gender,
            "address": new_task.address,
            "scheduledTime": new_task.scheduled_time,
            "distanceKm": new_task.distance_km,
            "paymentStatus": "DUE",
            "amount": new_task.total_amount,
            "assays": req.assays,
            "referenceNumber": new_task.reference_number,
            "status": "pending"
        }
    }

@app.get("/api/tasks/{task_id}")
def api_get_task_detail(task_id: str, db: Session = Depends(get_db)):
    t = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    
    groups = []
    for g in t.test_groups:
        groups.append({
            "id": g.id,
            "title": g.title,
            "tubeType": g.tube_type,
            "tests": [{"id": ti.id, "name": ti.name, "isSelected": ti.is_selected} for ti in g.tests]
        })

    return {
        "success": True,
        "task": {
            "id": t.id,
            "patientId": t.patient_id,
            "patientName": t.patient_name,
            "patientPhone": t.patient_phone,
            "patientAge": t.patient_age,
            "patientGender": t.patient_gender,
            "address": t.address,
            "distanceKm": t.distance_km,
            "scheduledDate": t.scheduled_date,
            "scheduledTime": t.scheduled_time,
            "status": t.status,
            "paymentStatus": t.payment_status,
            "totalAmount": t.total_amount,
            "barcode": t.barcode,
            "referenceNumber": t.reference_number,
            "testGroups": groups
        }
    }

@app.post("/api/tasks/{task_id}/barcode")
def api_assign_barcode(task_id: str, req: BarcodeAssignRequest, request: Request, db: Session = Depends(get_db)):
    t = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    t.barcode = req.barcode
    db.commit()

    # Log to Audit Trail
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    client_ip = request.client.host if request.client else "127.0.0.1"
    audit_id = f"AUD-{int(datetime.utcnow().timestamp() * 1000)}"
    entry = models.AuditLog(
        id=audit_id,
        timestamp=datetime.utcnow(),
        user_name="Ashwin Kumar",
        user_role="Field Phlebotomist Lead",
        employee_id="EMP-9342",
        action="BARCODE_LINKED",
        target_id=task_id,
        target_name=t.patient_name,
        details=f"Associated specimen vial barcode {req.barcode} with task.",
        ip_address=client_ip,
        security_hash=generate_security_hash("Ashwin Kumar", "BARCODE_LINKED", task_id, req.barcode, now_str)
    )
    db.add(entry)
    db.commit()

    return {"success": True, "message": "Barcode associated successfully", "barcode": t.barcode}

@app.post("/api/tasks/{task_id}/complete")
def api_complete_task(task_id: str, request: Request, db: Session = Depends(get_db)):
    t = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    t.status = "completed"
    db.commit()

    # Log to Audit Trail
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    client_ip = request.client.host if request.client else "127.0.0.1"
    audit_id = f"AUD-{int(datetime.utcnow().timestamp() * 1000)}"
    entry = models.AuditLog(
        id=audit_id,
        timestamp=datetime.utcnow(),
        user_name="Ashwin Kumar",
        user_role="Field Phlebotomist Lead",
        employee_id="EMP-9342",
        action="COLLECTION_COMPLETED",
        target_id=task_id,
        target_name=t.patient_name,
        details=f"Sample collection marked completed. Barcode: {t.barcode or 'N/A'}.",
        ip_address=client_ip,
        security_hash=generate_security_hash("Ashwin Kumar", "COLLECTION_COMPLETED", task_id, "Completed", now_str)
    )
    db.add(entry)
    db.commit()

    return {"success": True, "message": f"Task {task_id} completed successfully", "status": "completed"}

@app.post("/api/tasks/{task_id}/reject")
def api_reject_task(task_id: str, req: TaskRejectRequest, request: Request, db: Session = Depends(get_db)):
    t = db.query(models.Task).filter(models.Task.id == task_id).first()
    patient_name = t.patient_name if t else "Specimen Task"
    if t:
        t.status = "rejected"
        t.rejection_reason = req.reason
        db.commit()

    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    client_ip = request.client.host if request.client else "127.0.0.1"
    audit_id = f"AUD-{int(datetime.utcnow().timestamp() * 1000)}"
    details = f"Reason: {req.reason}."
    if req.notes:
        details += f" Dispatch Notes: {req.notes}"
    hash_sig = generate_security_hash(req.user_name, "TASK_REJECTED", task_id, details, now_str)

    entry = models.AuditLog(
        id=audit_id,
        timestamp=datetime.utcnow(),
        user_id=req.employee_id or "EMP-9342",
        user_name=req.user_name or "Ashwin Kumar",
        user_role=req.user_role or "Field Phlebotomist Lead",
        employee_id=req.employee_id,
        action="TASK_REJECTED",
        target_id=task_id,
        target_name=patient_name,
        details=details,
        ip_address=client_ip,
        security_hash=hash_sig
    )
    db.add(entry)
    db.commit()
    return {"success": True, "message": f"Task {task_id} rejected and logged in security audit trail"}

@app.get("/api/audit-logs")
def api_get_audit_logs(
    action: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(models.AuditLog)
    if action and action != "ALL":
        query = query.filter(models.AuditLog.action == action)
    if search:
        s = f"%{search.lower()}%"
        query = query.filter(
            (models.AuditLog.user_name.ilike(s)) |
            (models.AuditLog.details.ilike(s)) |
            (models.AuditLog.target_id.ilike(s)) |
            (models.AuditLog.target_name.ilike(s)) |
            (models.AuditLog.action.ilike(s))
        )
    logs = query.order_by(models.AuditLog.timestamp.desc()).limit(limit).all()
    return {
        "success": True,
        "count": len(logs),
        "logs": [
            {
                "id": l.id,
                "timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M:%S") if l.timestamp else "",
                "userName": l.user_name,
                "userRole": l.user_role,
                "employeeId": l.employee_id or "EMP-9342",
                "action": l.action,
                "targetId": l.target_id or "-",
                "targetName": l.target_name or "-",
                "details": l.details,
                "ipAddress": l.ip_address or "127.0.0.1",
                "securityHash": l.security_hash or "7f8a32b0c1e8"
            }
            for l in logs
        ]
    }

@app.post("/api/audit-logs")
def api_create_audit_log(req: AuditLogCreateRequest, request: Request, db: Session = Depends(get_db)):
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    client_ip = request.client.host if request.client else "127.0.0.1"
    audit_id = f"AUD-{int(datetime.utcnow().timestamp() * 1000)}"
    hash_sig = generate_security_hash(req.user_name, req.action, req.target_id or "-", req.details, now_str)

    entry = models.AuditLog(
        id=audit_id,
        timestamp=datetime.utcnow(),
        user_id=req.employee_id or "USR-AUTO",
        user_name=req.user_name,
        user_role=req.user_role,
        employee_id=req.employee_id,
        action=req.action,
        target_id=req.target_id,
        target_name=req.target_name,
        details=req.details,
        ip_address=client_ip,
        security_hash=hash_sig
    )
    db.add(entry)
    db.commit()
    return {"success": True, "id": entry.id, "securityHash": hash_sig}

@app.get("/api/centers")
def api_get_centers(db: Session = Depends(get_db)):
    centers = db.query(models.DiagnosticCenter).all()
    processing = [c.name for c in centers if c.type == "processing"]
    collection = [c.name for c in centers if c.type == "collection"]
    return {
        "success": True,
        "processingCenters": processing,
        "collectionCenters": collection
    }

@app.post("/api/centers/collection")
def api_save_center_collection(req: CenterCollectionRequest, request: Request, db: Session = Depends(get_db)):
    record = models.CenterCollection(
        id=f"CC-{int(datetime.utcnow().timestamp())}",
        processing_center=req.processingCenter,
        collection_center=req.collectionCenter,
        reference_number=req.referenceNumber,
        batch_barcode=req.batchsheetBarcode,
        tubes_collected=req.noOfContainers,
        actual_tubes=req.actualContainers,
        temperature=req.temperature,
    )
    db.add(record)

    # Log to Audit Trail
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    client_ip = request.client.host if request.client else "127.0.0.1"
    audit_id = f"AUD-{int(datetime.utcnow().timestamp() * 1000)}"
    entry = models.AuditLog(
        id=audit_id,
        timestamp=datetime.utcnow(),
        user_name="Rajesh Sharma",
        user_role="Central Dispatch & Logistics Lead",
        employee_id="EMP-4021",
        action="BATCH_HANDOVER",
        target_id=req.referenceNumber,
        target_name=req.collectionCenter,
        details=f"Batch handover completed: {req.actualContainers} containers transferred at {req.temperature}°C to {req.processingCenter}.",
        ip_address=client_ip,
        security_hash=generate_security_hash("Rajesh Sharma", "BATCH_HANDOVER", req.referenceNumber, "Batch handover", now_str)
    )
    db.add(entry)
    db.commit()

    return {
        "success": True,
        "message": "Center collection recorded successfully in LIMS database",
        "id": record.id
    }


@app.get("/api/lims/batch/{barcode}")
def api_lims_query_batch(barcode: str):
    
    return {
        "success": True,
        "batchBarcode": barcode,
        "system": "MedReach LIMS Core v4.2",
        "expectedContainers": 4,
        "sampleTypes": [
            {"type": "EDTA Whole Blood", "count": 2, "cap": "Purple"},
            {"type": "Sodium Citrate", "count": 1, "cap": "Blue"},
            {"type": "Serum Clot Activator", "count": 1, "cap": "Red"}
        ],
        "generatedAt": "2026-10-23 08:30:00",
        "originCenter": "Indiranagar Collection Clinic"
    }

if __name__ == "__main__":
    port = int(os.getenv("WEB_PORT", 5000))
    print(f"[INFO] Launching MedReach Web Application on http://localhost:{port}")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
