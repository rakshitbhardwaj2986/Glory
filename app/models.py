from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, UniqueConstraint
from pydantic import BaseModel


class Base(DeclarativeBase):
    pass


# ===== Pydantic Models (for API) =====

class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    role: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: str

    model_config = {"from_attributes": True}

class UserUpdate(BaseModel):
    full_name: str
    email: str
    hashed_password: str
    role: str 

    model_config = {"from_attributes": True}

class UserLogin(BaseModel):
    email: str
    password: str
    
    model_config = {"from_attributes": True}


class JobCreate(BaseModel):
    company: str
    job_title: str
    type: str
    location: str

class JobResponse(BaseModel):
    id: int
    company: str
    job_title: str
    type: str
    location: str
    posted_by: int

    model_config = {"from_attributes": True}

class JobUpdate(BaseModel):
    job_title: str
    type: str
    location: str 
 
    model_config = {"from_attributes": True}


class ApplicationCreate(BaseModel):
    job_id: int
    status: str

class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    user_id: int 
    status: str

    model_config = {"from_attributes": True}

class ApplicationUpdate(BaseModel):
    status: str

    model_config = {"from_attributes": True}


class ResumeCreate(BaseModel):
    role: str
    experience: int 
    skills: str 

class ResumeResponse(BaseModel):
    id: int 
    name: str
    user_id: int
    role: str 
    experience: int 
    skills: str 

    model_config = {"from_attributes": True}

class ResumeUpdate(BaseModel):
    name: str
    role: str
    experience: int 
    skills: str 

    model_config = {"from_attributes": True}

class MatchRequest(BaseModel):
    resume_text: str   
    job_text: str   
    model_config = {"from_attributes": True}

class MatchResponse(BaseModel):
    match_score: float           # 0.0 to 100.0
    level: str                   # "Strong" / "Good" / "Weak"
    matched_skills: list[str]    # skills found in both
    missing_skills: list[str] 
    model_config = {"from_attributes": True}
# ===== SQLAlchemy ORM Models (for Database) =====

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)

    jobs: Mapped[list["Job"]] = relationship(back_populates="poster")
    applications: Mapped[list["Application"]] = relationship(back_populates="user")
    resume: Mapped["Resume"] = relationship(back_populates="user", uselist=False)

class Job(Base):
    __tablename__= "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    company:Mapped[str] = mapped_column(String(50), nullable=False)
    job_title: Mapped[str] = mapped_column(String(100),nullable=False)
    type: Mapped[str] = mapped_column(String(50))
    posted_by: Mapped[int]= mapped_column(ForeignKey("users.id"))
    location: Mapped[str]= mapped_column(String(100), nullable=False)
    
    
    poster: Mapped["User"] = relationship(back_populates="jobs")
    applications: Mapped[list["Application"]] = relationship(back_populates="job")

class Application(Base):
    __tablename__="applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int]= mapped_column(ForeignKey("jobs.id"),nullable=False)
    user_id: Mapped[int]= mapped_column(ForeignKey("users.id"),nullable=False)
    status:Mapped[str]= mapped_column(default="Apply")

    __table_args__ = (
        UniqueConstraint("user_id", "job_id"),
    )
    job: Mapped["Job"] = relationship(back_populates="applications")
    user: Mapped["User"] = relationship(back_populates="applications")


class Resume(Base):
    __tablename__="resume"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"),unique=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    experience: Mapped[int] = mapped_column()
    skills: Mapped[str] = mapped_column(String(225), nullable=False)

    user: Mapped["User"] = relationship(back_populates="resume")
