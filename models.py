from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(50), primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(String(50), default="Field Phlebotomist")
    employee_id = Column(String(50), default="EMP-8842")
    phone = Column(String(30), default="+91 98765 43210")
    avatar = Column(String(255), nullable=True)
    vehicle_number = Column(String(50), default="KA-05-MK-4421")
    created_at = Column(DateTime, default=datetime.utcnow)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(50), primary_key=True, index=True) 
    patient_id = Column(String(50), index=True)
    patient_name = Column(String(100), nullable=False)
    patient_phone = Column(String(30), nullable=False)
    patient_age = Column(Integer, nullable=False)
    patient_gender = Column(String(20), nullable=False)
    address = Column(Text, nullable=False)
    distance_km = Column(Float, default=1.0)
    scheduled_date = Column(String(50), nullable=False)
    scheduled_time = Column(String(50), nullable=False)
    type = Column(String(20), default="home") 
    status = Column(String(30), default="pending")
    payment_status = Column(String(30), default="pending") 
    total_amount = Column(Float, default=0.0)
    container_temperature = Column(Float, default=-2.0)
    reference_number = Column(String(100), nullable=True)
    barcode = Column(String(100), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    reassigned_to = Column(String(100), nullable=True)
    payment_method = Column(String(30), nullable=True)
    payment_txn_id = Column(String(100), nullable=True)
    payment_paid_at = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    test_groups = relationship("TaskTestGroup", back_populates="task", cascade="all, delete-orphan")

class TaskTestGroup(Base):
    __tablename__ = "task_test_groups"

    id = Column(String(50), primary_key=True, index=True)
    task_id = Column(String(50), ForeignKey("tasks.id"), nullable=False)
    title = Column(String(100), nullable=False)
    tube_type = Column(String(100), nullable=False)

    task = relationship("Task", back_populates="test_groups")
    tests = relationship("GroupTestItem", back_populates="group", cascade="all, delete-orphan")

class GroupTestItem(Base):
    __tablename__ = "group_test_items"

    id = Column(String(50), primary_key=True, index=True)
    group_id = Column(String(50), ForeignKey("task_test_groups.id"), nullable=False)
    name = Column(String(100), nullable=False)
    is_selected = Column(Boolean, default=True)

    group = relationship("TaskTestGroup", back_populates="tests")

class CenterCollection(Base):
    __tablename__ = "center_collections"

    id = Column(String(50), primary_key=True, index=True)
    processing_center = Column(String(150), nullable=False)
    collection_center = Column(String(150), nullable=False)
    reference_number = Column(String(100), nullable=False)
    batch_barcode = Column(String(100), nullable=False)
    tubes_collected = Column(Integer, default=4)
    actual_tubes = Column(Integer, default=4)
    temperature = Column(Float, default=-2.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class DiagnosticCenter(Base):
    __tablename__ = "diagnostic_centers"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    type = Column(String(30), nullable=False) 
    address = Column(Text, nullable=False)
    city = Column(String(50), default="Bengaluru")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(50), primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(String(50), nullable=True)
    user_name = Column(String(100), nullable=False)
    user_role = Column(String(50), nullable=False)
    employee_id = Column(String(50), nullable=True)
    action = Column(String(50), nullable=False) # e.g. "TASK_REJECTED", "BARCODE_LINKED", "COLLECTION_COMPLETED", "PAYMENT_RECORDED", "BATCH_HANDOVER", "USER_LOGIN"
    target_id = Column(String(50), nullable=True) # e.g. "TK-209312"
    target_name = Column(String(100), nullable=True) # e.g. "Priya Venkatesh"
    details = Column(Text, nullable=False)
    ip_address = Column(String(50), default="127.0.0.1")
    security_hash = Column(String(64), nullable=True)

