from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


# ─── Enums / Constants ────────────────────────────────────────────────────────

class Role:
    ADMIN   = "admin"
    COMPANY = "company"
    STUDENT = "student"

class ApprovalStatus:
    PENDING  = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class DriveStatus:
    PENDING  = "pending"
    APPROVED = "approved"
    CLOSED   = "closed"

class ApplicationStatus:
    APPLIED     = "applied"
    SHORTLISTED = "shortlisted"
    SELECTED    = "selected"
    REJECTED    = "rejected"
    WAITING     = "waiting"


# ─── User (unified model for all roles) ──────────────────────────────────────

class User(db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(20), nullable=False)   # admin / company / student
    is_active     = db.Column(db.Boolean, default=True)
    is_blacklisted= db.Column(db.Boolean, default=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    company_profile = db.relationship("Company", back_populates="user", uselist=False,
                                      cascade="all, delete-orphan")
    student_profile = db.relationship("Student", back_populates="user", uselist=False,
                                      cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id":            self.id,
            "email":         self.email,
            "role":          self.role,
            "is_active":     self.is_active,
            "is_blacklisted":self.is_blacklisted,
            "created_at":    self.created_at.isoformat(),
        }


# ─── Company ──────────────────────────────────────────────────────────────────

class Company(db.Model):
    __tablename__ = "companies"

    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name            = db.Column(db.String(150), nullable=False)
    industry        = db.Column(db.String(100))
    location        = db.Column(db.String(150))
    website         = db.Column(db.String(200))
    hr_contact_name = db.Column(db.String(100))
    hr_contact_phone= db.Column(db.String(20))
    description     = db.Column(db.Text)
    logo_url        = db.Column(db.String(300))
    approval_status = db.Column(db.String(20), default=ApprovalStatus.PENDING)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user            = db.relationship("User", back_populates="company_profile")
    placement_drives= db.relationship("PlacementDrive", back_populates="company",
                                      cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id":              self.id,
            "user_id":         self.user_id,
            "name":            self.name,
            "industry":        self.industry,
            "location":        self.location,
            "website":         self.website,
            "hr_contact_name": self.hr_contact_name,
            "hr_contact_phone":self.hr_contact_phone,
            "description":     self.description,
            "logo_url":        self.logo_url,
            "approval_status": self.approval_status,
            "created_at":      self.created_at.isoformat(),
            "email":           self.user.email if self.user else None,
            "is_active":       self.user.is_active if self.user else None,
            "is_blacklisted":  self.user.is_blacklisted if self.user else None,
        }


# ─── Student ──────────────────────────────────────────────────────────────────

class Student(db.Model):
    __tablename__ = "students"

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    full_name    = db.Column(db.String(150), nullable=False)
    roll_number  = db.Column(db.String(50), unique=True)
    department   = db.Column(db.String(100))
    year         = db.Column(db.Integer)
    cgpa         = db.Column(db.Float, default=0.0)
    skills       = db.Column(db.Text)           # comma-separated or JSON string
    resume_url   = db.Column(db.String(300))
    phone        = db.Column(db.String(20))
    dob          = db.Column(db.Date)
    gender       = db.Column(db.String(20))
    address      = db.Column(db.Text)
    about        = db.Column(db.Text)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user         = db.relationship("User", back_populates="student_profile")
    applications = db.relationship("Application", back_populates="student",
                                   cascade="all, delete-orphan")
    placements   = db.relationship("Placement", back_populates="student",
                                   cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id":          self.id,
            "user_id":     self.user_id,
            "full_name":   self.full_name,
            "roll_number": self.roll_number,
            "department":  self.department,
            "year":        self.year,
            "cgpa":        self.cgpa,
            "skills":      self.skills,
            "resume_url":  self.resume_url,
            "phone":       self.phone,
            "gender":      self.gender,
            "about":       self.about,
            "email":       self.user.email if self.user else None,
            "is_active":   self.user.is_active if self.user else None,
            "is_blacklisted": self.user.is_blacklisted if self.user else None,
            "created_at":  self.created_at.isoformat(),
        }


# ─── Placement Drive (Job Position) ──────────────────────────────────────────

class PlacementDrive(db.Model):
    __tablename__ = "placement_drives"

    id                  = db.Column(db.Integer, primary_key=True)
    company_id          = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    job_title           = db.Column(db.String(150), nullable=False)
    job_description     = db.Column(db.Text)
    skills_required     = db.Column(db.Text)     # comma-separated
    salary_min          = db.Column(db.Float)
    salary_max          = db.Column(db.Float)
    location            = db.Column(db.String(150))
    job_type            = db.Column(db.String(50), default="Full-time")
    # Eligibility
    eligible_branches   = db.Column(db.Text)     # comma-separated
    min_cgpa            = db.Column(db.Float, default=0.0)
    eligible_years      = db.Column(db.Text)     # e.g. "3,4"
    # Dates
    application_deadline= db.Column(db.DateTime)
    drive_date          = db.Column(db.DateTime)
    # Status
    status              = db.Column(db.String(20), default=DriveStatus.PENDING)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at          = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company      = db.relationship("Company", back_populates="placement_drives")
    applications = db.relationship("Application", back_populates="drive",
                                   cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id":                   self.id,
            "company_id":           self.company_id,
            "company_name":         self.company.name if self.company else None,
            "company_logo":         self.company.logo_url if self.company else None,
            "job_title":            self.job_title,
            "job_description":      self.job_description,
            "skills_required":      self.skills_required,
            "salary_min":           self.salary_min,
            "salary_max":           self.salary_max,
            "location":             self.location,
            "job_type":             self.job_type,
            "eligible_branches":    self.eligible_branches,
            "min_cgpa":             self.min_cgpa,
            "eligible_years":       self.eligible_years,
            "application_deadline": self.application_deadline.isoformat() if self.application_deadline else None,
            "drive_date":           self.drive_date.isoformat() if self.drive_date else None,
            "status":               self.status,
            "applicant_count":      len(self.applications),
            "created_at":           self.created_at.isoformat(),
        }


# ─── Application ─────────────────────────────────────────────────────────────

class Application(db.Model):
    __tablename__ = "applications"

    id              = db.Column(db.Integer, primary_key=True)
    student_id      = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    drive_id        = db.Column(db.Integer, db.ForeignKey("placement_drives.id"), nullable=False)
    status          = db.Column(db.String(20), default=ApplicationStatus.APPLIED)
    applied_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    interview_type  = db.Column(db.String(50))   # In-person / Virtual / Phone
    interview_date  = db.Column(db.DateTime)
    remarks         = db.Column(db.Text)

    # Unique constraint: one application per student per drive
    __table_args__ = (
        db.UniqueConstraint("student_id", "drive_id", name="uq_student_drive"),
    )

    # Relationships
    student  = db.relationship("Student", back_populates="applications")
    drive    = db.relationship("PlacementDrive", back_populates="applications")
    placement= db.relationship("Placement", back_populates="application",
                               uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id":             self.id,
            "student_id":     self.student_id,
            "student_name":   self.student.full_name if self.student else None,
            "student_dept":   self.student.department if self.student else None,
            "student_cgpa":   self.student.cgpa if self.student else None,
            "drive_id":       self.drive_id,
            "job_title":      self.drive.job_title if self.drive else None,
            "company_name":   self.drive.company.name if self.drive and self.drive.company else None,
            "status":         self.status,
            "applied_at":     self.applied_at.isoformat(),
            "interview_type": self.interview_type,
            "interview_date": self.interview_date.isoformat() if self.interview_date else None,
            "remarks":        self.remarks,
        }


# ─── Placement (final selection record) ─────────────────────────────────────

class Placement(db.Model):
    __tablename__ = "placements"

    id             = db.Column(db.Integer, primary_key=True)
    student_id     = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    company_id     = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"), nullable=False)
    position       = db.Column(db.String(150))
    salary         = db.Column(db.Float)
    joining_date   = db.Column(db.Date)
    offer_letter_url = db.Column(db.String(300))
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student     = db.relationship("Student", back_populates="placements")
    company     = db.relationship("Company")
    application = db.relationship("Application", back_populates="placement")

    def to_dict(self):
        return {
            "id":               self.id,
            "student_id":       self.student_id,
            "student_name":     self.student.full_name if self.student else None,
            "company_id":       self.company_id,
            "company_name":     self.company.name if self.company else None,
            "application_id":   self.application_id,
            "position":         self.position,
            "salary":           self.salary,
            "joining_date":     self.joining_date.isoformat() if self.joining_date else None,
            "offer_letter_url": self.offer_letter_url,
            "created_at":       self.created_at.isoformat(),
        }
