from app.match import calibrate_score, extract_skills

# ─────────────────────────────────────────
# TEST 6: SKILL EXTRACTION FROM RESUME TEXT
# ─────────────────────────────────────────
def test_extract_skills_recognizes_common_skills():
    """Skill extractor should identify known skills from resume text."""
    skills = extract_skills("I am a Python developer with FastAPI and SQLAlchemy experience")
    assert {"python", "fastapi", "sqlalchemy"}.issubset(skills)


# ─────────────────────────────────────────
# TEST 7: SCORE IS ALWAYS WITHIN 0-100
# ─────────────────────────────────────────
def test_calibrate_score_is_clamped_to_expected_range():
    """Score should never go below 0 or above 100 regardless of inputs."""
    assert 0 <= calibrate_score(-100, 0.2) <= 100
    assert 0 <= calibrate_score(200, 0.8) <= 100


# ─────────────────────────────────────────
# TEST 8: GOOD MATCH SCORES HIGHER THAN BAD MATCH
# ─────────────────────────────────────────
def test_match_quality(client):
    """A resume matching the JD should score higher than a mismatched one."""
    good_response = client.post("/match", json={
        "resume_text": "Python FastAPI AWS Docker developer",
        "job_text": "Looking for Python FastAPI developer."
    })
    bad_response = client.post("/match", json={
        "resume_text": "Python FastAPI AWS Docker developer",
        "job_text": "Looking for HTML CSS Frontend developer."
    })
    assert good_response.status_code == 200
    assert bad_response.status_code == 200
    assert good_response.json()["match_score"] > bad_response.json()["match_score"]
