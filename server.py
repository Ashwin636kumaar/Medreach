import os
import uvicorn
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
def api_login(req: LoginRequest, db: Session = Depends(get_db)):
    clean_user = req.username.strip().lower()
    clean_pass = req.password.strip()

    print(f"\n[AUTH ATTEMPT] Received: username={req.username!r}, password={'*' * len(req.password)}")

    # Check for Ashwin Kumar credentials
    digits_only = clean_user.replace(" ", "").replace("+91", "").replace("-", "")
    is_ashwin_user = (
        clean_user in ["ashwinkumaar65@gmail.com", "ashwinkumar65@gmail.com", "9342600642"] or
        digits_only == "9342600642" or
        "9342600642" in digits_only or
        "ashwin" in clean_user
    )
    is_valid_pass = clean_pass in ["ash@123", "Ashwin@2005", "Ash@123", "ashwin@2005", "password123"]

    if is_ashwin_user and is_valid_pass:
        print(f"[AUTH SUCCESS] 👤 User identified: Ashwin Kumar ({req.username}) logged in successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        return {
            "success": True,
            "user": {
                "id": "USR-102",
                "name": "Ashwin Kumar",
                "role": "Field Phlebotomist Lead",
                "email": "ashwinkumaar65@gmail.com",
                "employeeId": "EMP-9342",
                "phone": "+91 9342600642"
            }
        }

    user = db.query(models.User).filter(models.User.username == req.username).first()
    if not user or user.password_hash != req.password:
        # For testing ease, allow password123 for any username
        if req.password == "password123":
            print(f"\n[AUTH SUCCESS] 👤 User identified: {req.username} logged in at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            return {
                "success": True,
                "user": {
                    "id": "USR-101",
                    "name": "Ashok Pandian",
                    "role": "Field Phlebotomist Lead",
                    "email": req.username,
                    "employeeId": "EMP-8842",
                    "phone": "+91 98765 43210"
                }
            }
        print(f"\n[AUTH FAILED] ❌ Failed login attempt for user: {req.username}\n")
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    print(f"\n[AUTH SUCCESS] 👤 User identified: {user.name} ({user.username}) logged in at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    return {
        "success": True,
        "user": {
            "id": user.id,
            "name": user.name,
            "role": user.role,
            "email": user.username,
            "employeeId": user.employee_id,
            "phone": user.phone
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
def api_assign_barcode(task_id: str, req: BarcodeAssignRequest, db: Session = Depends(get_db)):
    t = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    t.barcode = req.barcode
    db.commit()
    return {"success": True, "message": "Barcode associated successfully", "barcode": t.barcode}

@app.post("/api/tasks/{task_id}/complete")
def api_complete_task(task_id: str, db: Session = Depends(get_db)):
    t = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    t.status = "completed"
    db.commit()
    return {"success": True, "message": f"Task {task_id} completed successfully", "status": "completed"}

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
def api_save_center_collection(req: CenterCollectionRequest, db: Session = Depends(get_db)):
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
