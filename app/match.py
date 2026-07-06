from functools import lru_cache
from fastapi import APIRouter
from app.models import MatchRequest, MatchResponse
from sentence_transformers import SentenceTransformer, util
import re

router = APIRouter()

@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer("paraphrase-MiniLM-L3-v2")

# Canonical skills -> list of aliases/synonyms that should all count as the same skill
SKILL_ALIASES = {
    "python": ["python", "py"],
    "java": ["java"],
    "javascript": ["javascript", "js", "es6", "ecmascript"],
    "typescript": ["typescript", "ts"],
    "c++": ["c++", "cpp"],
    "c#": ["c#", "csharp", "c sharp"],
    "golang": ["golang", "go lang", "go"],
    "rust": ["rust"],
    "php": ["php"],
    "ruby": ["ruby"],
    "kotlin": ["kotlin"],
    "swift": ["swift"],
    "scala": ["scala"],
    "r": ["r programming", " r "],

    "fastapi": ["fastapi", "fast api"],
    "flask": ["flask"],
    "django": ["django"],
    "spring boot": ["spring boot", "springboot", "spring"],
    "express": ["express", "express.js", "expressjs"],
    "node.js": ["node.js", "nodejs", "node js", "node"],
    "asp.net": ["asp.net", "dotnet", ".net", "dot net"],
    "laravel": ["laravel"],

    "react": ["react", "react.js", "reactjs"],
    "angular": ["angular", "angularjs"],
    "vue": ["vue", "vue.js", "vuejs"],
    "next.js": ["next.js", "nextjs"],
    "html": ["html", "html5"],
    "css": ["css", "css3"],
    "tailwind": ["tailwind", "tailwindcss"],
    "redux": ["redux"],

    "sql": ["sql"],
    "postgresql": ["postgresql", "postgres", "psql"],
    "mysql": ["mysql"],
    "mongodb": ["mongodb", "mongo"],
    "redis": ["redis"],
    "sqlite": ["sqlite"],
    "sqlalchemy": ["sqlalchemy"],
    "dynamodb": ["dynamodb"],
    "elasticsearch": ["elasticsearch", "elastic search"],
    "firebase": ["firebase"],

    "docker": ["docker", "containerization"],
    "kubernetes": ["kubernetes", "k8s"],
    "aws": ["aws", "amazon web services"],
    "gcp": ["gcp", "google cloud", "google cloud platform"],
    "azure": ["azure", "microsoft azure"],
    "ci/cd": ["ci/cd", "cicd", "continuous integration", "continuous deployment"],
    "jenkins": ["jenkins"],
    "github actions": ["github actions"],
    "terraform": ["terraform"],
    "linux": ["linux", "unix"],
    "bash": ["bash", "shell scripting", "shell script"],
    "nginx": ["nginx"],
    "microservices": ["microservices", "micro services", "microservice architecture"],

    "rest api": ["rest api", "restful api", "restful", "rest"],
    "graphql": ["graphql"],
    "grpc": ["grpc"],
    "websocket": ["websocket", "websockets"],
    "oauth": ["oauth", "oauth2"],
    "jwt": ["jwt", "json web token"],
    "authentication": ["authentication", "auth"],

    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning", "dl"],
    "tensorflow": ["tensorflow", "tf"],
    "pytorch": ["pytorch", "torch"],
    "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "nlp": ["nlp", "natural language processing"],
    "data science": ["data science"],
    "llm": ["llm", "large language model", "large language models"],
    "neural network": ["neural network", "neural networks"],
    "transformer": ["transformer", "transformers"],
    "artificial intelligence": ["artificial intelligence", "ai"],
    "data visualization": ["data visualization", "data visualisation", "dataviz"],
    "data analysis": ["data analysis"],
    "etl": ["etl"],
    "spark": ["spark", "apache spark"],
    "hadoop": ["hadoop"],

    "pytest": ["pytest"],
    "unit testing": ["unit testing", "unittest", "unit tests"],
    "jest": ["jest"],
    "selenium": ["selenium"],
    "git": ["git"],
    "github": ["github"],
    "gitlab": ["gitlab"],
    "jira": ["jira"],
    "agile": ["agile", "agile methodology", "agile development"],
    "scrum": ["scrum"],
    "postman": ["postman"],
    "swagger": ["swagger", "openapi"],
    "celery": ["celery"],
    "kafka": ["kafka", "apache kafka"],
    "rabbitmq": ["rabbitmq"],

    "system design": ["system design"],
    "data structures": ["data structures", "dsa"],
    "algorithms": ["algorithms", "algorithm"],
    "object oriented programming": ["object oriented programming", "oop", "object-oriented"],
    "design patterns": ["design patterns"],
    "debugging": ["debugging"],
    "version control": ["version control"],
    "problem solving": ["problem solving", "problem-solving"],
}

def extract_skills(text: str) -> set[str]:
    text_lower = " " + text.lower() + " "
    found = set()
    for canonical, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            pattern = r'(?<![a-zA-Z0-9])' + re.escape(alias.strip()) + r'(?![a-zA-Z0-9])'
            if re.search(pattern, text_lower):
                found.add(canonical)
                break  # one alias match is enough, move to next skill
    return found

def calibrate_score(raw_score: float, skill_overlap_ratio: float) -> float:
    """
    Raw sentence-transformer cosine similarity on long paragraphs tends to
    sit in a compressed 30-65 range even for genuinely strong matches.
    We blend it with actual skill keyword overlap for a realistic score.
    """
    stretched = max(0, min(100, (raw_score - 20) * 1.6))
    blended = (stretched * 0.5) + (skill_overlap_ratio * 100 * 0.5)
    return max(0, min(100, blended))

@router.post("/match", response_model=MatchResponse)
def match_resume_to_job(data: MatchRequest):
    ml_model = get_model()
    resume_embedding = ml_model.encode(data.resume_text, convert_to_tensor=True)
    job_embedding = ml_model.encode(data.job_text, convert_to_tensor=True)
    raw_score = float(util.cos_sim(resume_embedding, job_embedding)[0][0]) * 100

    resume_skills = extract_skills(data.resume_text)
    job_skills = extract_skills(data.job_text)

    matched = sorted(resume_skills & job_skills)
    missing = sorted(job_skills - resume_skills)

    overlap_ratio = (len(matched) / len(job_skills)) if job_skills else 0.5

    score = calibrate_score(raw_score, overlap_ratio)

    if score >= 70:
        level = "Strong"
    elif score >= 45:
        level = "Good"
    else:
        level = "Weak"

    return MatchResponse(
        match_score=round(score, 1),
        level=level,
        matched_skills=matched,
        missing_skills=missing
    )