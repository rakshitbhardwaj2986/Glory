from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from app.models import Base, UserCreate, UserResponse, UserUpdate, JobCreate, JobResponse, User,Job, JobUpdate,Resume, ResumeCreate, ResumeResponse, ResumeUpdate, Application, ApplicationCreate,ApplicationResponse,ApplicationUpdate, UserLogin
from app.Database import engine
from app.match import router as match_router
from pathlib import Path
from sqlalchemy.orm import Session
from . import models
from .Database import get_db
from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_admin,
    
    require_jobseeker,
    require_employer
)

app = FastAPI()
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(match_router)

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = Path(__file__).resolve().parent / "static" / "index.html"
    return index_path.read_text(encoding="utf-8")

def read_static_page(filename: str):
    page_path = Path(__file__).resolve().parent / "static" / filename
    return page_path.read_text(encoding="utf-8")

@app.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard():
    return read_static_page("dashboard.html")

@app.get("/jobs-page", response_class=HTMLResponse)
async def read_jobs_page():
    return read_static_page("jobs.html")

@app.get("/match", response_class=HTMLResponse)
async def read_match_page():
    return read_static_page("match.html")

try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Error creating tables: {e}")

#CREATE USER
@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password before saving
    hashed_pwd = hash_password(user.password)
    
    # Pydantic → SQLAlchemy
    new_user = models.User(
        full_name=user.full_name,
        email=user.email,
        hashed_password=hashed_pwd,
        role=user.role
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

#LOGIN USER
@app.post("/login")
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Find user by email
    db_user = db.query(User).filter(User.email == form_data.username).first()
    
    if not db_user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    # Verify password
    if not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    # Create access token
    access_token = create_access_token(data={"sub": db_user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "email": db_user.email,
            "full_name": db_user.full_name,
            "role": db_user.role
        }
    }

   # GET ALL USERS - ADMIN ONLY
@app.get("/users", response_model= list[UserResponse])
def get_users(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    users = db.query(models.User).all()
    return users

   # GET ONE USER - USER OR ADMIN
@app.get("/users/{user_id}", response_model= UserResponse)
def get_user(user_id :int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user= db.query(User).filter(User.id == user_id).first()
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return user

  # UPDATE USER - USER OR ADMIN
@app.put("/users/{user_id}", response_model= UserUpdate)
def update_user(user_id :int, updated_data: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user= db.query(User).filter(User.id == user_id).first()
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    for key,value in updated_data.dict().items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user
    
    #DELETE USER - ADMIN ONLY
@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    user= db.query(User).filter(User.id == user_id).first()
    db.delete(user)
    db.commit()
    return {"message": "deleted"}

    #CREATE JOB - EMPLOYER REQUIRED
@app.post("/jobs", response_model=JobResponse)
def create_job(job: JobCreate, db: Session = Depends(get_db), current_user: User = Depends(require_employer)):
    new_job = models.Job(
        company=job.company,
        job_title=job.job_title,
        type=job.type,
        location=job.location,
        posted_by=current_user.id
    )
    

    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return new_job

   #GET ALL JOBS
@app.get("/jobs", response_model=list[JobResponse])
def get_all_jobs(db: Session = Depends(get_db)):
    jobs= db.query(Job).all()
    return jobs

    #GET ONE JOB
@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job= db.query(Job).filter(Job.id == job_id).first()
    return job

   #UPDATE JOB - JOB OWNER OR ADMIN
@app.put("/jobs/{job_id}", response_model=JobUpdate)
def update_job(job_id: int, updated_job: JobUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job= db.query(Job).filter(Job.id == job_id).first()
    if job.posted_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    for key, value in updated_job.dict().items():
        setattr(job, key, value)
    db.commit()
    db.refresh(job)
    return job
    
    #DELETE JOB - JOB OWNER OR ADMIN
@app.delete("/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job= db.query(Job).filter(Job.id == job_id).first()
    if job.posted_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(job)
    db.commit()
    return {"message": "deleted"}

    #CREATE RESUME - JOBSEEKER REQUIRED
@app.post("/resume", response_model= ResumeResponse)
def create_resume(resume: ResumeCreate, db: Session = Depends(get_db), current_user: User = Depends(require_jobseeker)):
    new_resume= Resume(
        name=current_user.full_name,
        user_id=current_user.id,
        role=resume.role,
        experience=resume.experience,
        skills=resume.skills
    )
    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)

    return new_resume

     #GET ALL RESUMES - ADMIN ONLY
@app.get("/resume", response_model= list[ResumeResponse])
def get_resumes(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    resumes= db.query(Resume).all()
    return resumes

     #GET ONE RESUME - USER OR ADMIN
@app.get("/resume/{resume_id}", response_model= ResumeResponse)
def get_resume(resume_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resume= db.query(Resume).filter(Resume.id == resume_id).first()
    if resume.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return resume

    #UPDATE RESUME - USER OR ADMIN
@app.put("/resume/{resume_id}", response_model= ResumeUpdate)
def update_resume(resume_id: int, updated_resume: ResumeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resume= db.query(Resume).filter(Resume.id == resume_id).first()
    if resume.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    for key,value in updated_resume.dict().items():
        setattr(resume,key,value)
    db.commit()
    db.refresh(resume)
    return resume
    
    #DELETE RESUME - USER OR ADMIN
@app.delete("/resume/{resume_id}")
def delete_resume(resume_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resume= db.query(Resume).filter(Resume.id == resume_id).first()
    if resume.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(resume)
    db.commit()
    return {"message": "deleted"} 

    # GET CURRENT USER - ANY LOGGED IN USER
@app.get("/users/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

    # GET MY RESUME - JOBSEEKER
@app.get("/resume/me", response_model=ResumeResponse)
def get_my_resume(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="No resume found")
    return resume

    # GET MY APPLICATIONS - JOBSEEKER
@app.get("/applications/me", response_model=list[ApplicationResponse])
def get_my_applications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(models.Application).filter(models.Application.user_id == current_user.id).all()

    # GET APPLICATIONS FOR EMPLOYER'S JOBS
@app.get("/applications/my-jobs", response_model=list[ApplicationResponse])
def get_applications_for_my_jobs(db: Session = Depends(get_db), current_user: User = Depends(require_employer)):
    my_job_ids = [j.id for j in db.query(Job).filter(Job.posted_by == current_user.id).all()]
    return db.query(models.Application).filter(models.Application.job_id.in_(my_job_ids)).all()

    #CREATE APPLICATION - JOBSEEKER REQUIRED
@app.post("/applications", response_model= ApplicationResponse)
def create_application(application: ApplicationCreate, db: Session = Depends(get_db), current_user: User = Depends(require_jobseeker)):
    new_application= models.Application(
        job_id=application.job_id,
        user_id=current_user.id,
        status=application.status
    )
    db.add(new_application)
    db.commit()
    db.refresh(new_application)
    
    return new_application

    # GET ALL APPLICATIONS - ADMIN ONLY
@app.get("/applications", response_model= list[ApplicationResponse])
def get_applications(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    applications = db.query(models.Application).all()
    return applications

   # GET ONE APPLICATION - APPLICANT/JOB OWNER/ADMIN
@app.get("/applications/{application_id}", response_model= ApplicationResponse)
def get_application(application_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    application= db.query(Application).filter(Application.id == application_id).first()
    job = db.query(Job).filter(Job.id == application.job_id).first()
    if application.user_id != current_user.id and job.posted_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return application

  # UPDATE APPLICATION - APPLICANT/JOB OWNER/ADMIN
@app.put("/applications/{application_id}", response_model=ApplicationUpdate)
def update_application(application_id: int, updated_data: ApplicationUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    application = db.query(Application).filter(Application.id == application_id).first()
    job = db.query(Job).filter(Job.id == application.job_id).first()
    if application.user_id != current_user.id and job.posted_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    for key, value in updated_data.dict().items():
        setattr(application, key, value)
    
    db.commit()
    db.refresh(application)
    return application
    
    #DELETE APPLICATION - APPLICANT/JOB OWNER/ADMIN
@app.delete("/applications/{application_id}")
def delete_application(application_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    application= db.query(Application).filter(Application.id == application_id).first()
    job = db.query(Job).filter(Job.id == application.job_id).first()
    if application.user_id != current_user.id and job.posted_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(application)
    db.commit()
    return {"message": "deleted"}
    
