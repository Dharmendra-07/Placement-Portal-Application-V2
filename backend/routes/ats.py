"""
routes/ats.py
--------------
ATS (Applicant Tracking System) resume screener.

POST /api/ats/screen
  Body: { resume_text: str, job_description: str, skills_required: str }
  Returns: match score, matched/missing skills, keyword analysis, suggestions

Accessible by Student and Company roles.
Uses simple NLP (no external AI dependency) — keyword frequency scoring.
"""

import re
import math
from collections import Counter
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

ats_bp = Blueprint("ats", __name__)

# ── Common stop words ─────────────────────────────────────────────────────────
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "was", "are", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "this", "that", "these", "those",
    "we", "you", "i", "it", "he", "she", "they", "our", "your", "their",
    "its", "not", "no", "nor", "so", "yet", "both", "either", "neither",
    "as", "if", "then", "than", "such", "when", "while", "although",
    "though", "because", "since", "until", "unless", "however", "also",
    "about", "above", "after", "before", "between", "during", "each",
    "how", "into", "more", "most", "other", "over", "same", "through",
    "up", "use", "used", "using", "very", "work", "working", "new",
    "strong", "good", "excellent", "experience", "knowledge", "ability",
}

# Tech / domain keyword taxonomy (for category grouping)
KEYWORD_CATEGORIES = {
    "Languages":   {"python","java","javascript","typescript","c++","c#","go","rust","kotlin","swift","r","scala","php","ruby"},
    "Frontend":    {"react","vue","angular","html","css","sass","webpack","vite","nextjs","nuxt","tailwind","bootstrap"},
    "Backend":     {"flask","django","fastapi","spring","express","nodejs","rails","laravel","nestjs","gin"},
    "Database":    {"sql","mysql","postgresql","mongodb","redis","sqlite","oracle","cassandra","dynamodb","elasticsearch"},
    "Cloud":       {"aws","azure","gcp","docker","kubernetes","terraform","ci/cd","jenkins","github actions","heroku"},
    "ML/AI":       {"machine learning","deep learning","tensorflow","pytorch","scikit-learn","nlp","computer vision","pandas","numpy"},
    "Mobile":      {"android","ios","react native","flutter","swift","kotlin"},
    "Tools":       {"git","jira","agile","scrum","rest","graphql","grpc","microservices"},
}


def _tokenize(text: str) -> list[str]:
    text   = text.lower()
    tokens = re.findall(r'\b[a-z][a-z0-9+#\-\.]{1,}\b', text)
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


def _extract_bigrams(tokens: list[str]) -> list[str]:
    return [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]


def _tfidf_score(term_freq: Counter, doc_len: int) -> dict:
    return {term: (count / doc_len) * math.log(1 + count)
            for term, count in term_freq.items()}


def _find_category(skill: str) -> str:
    skill_lower = skill.lower()
    for cat, members in KEYWORD_CATEGORIES.items():
        if skill_lower in members:
            return cat
    return "General"


@ats_bp.route("/screen", methods=["POST"])
@jwt_required()
def screen_resume():
    data = request.get_json()
    resume_text     = data.get("resume_text", "").strip()
    job_description = data.get("job_description", "").strip()
    skills_required = data.get("skills_required", "").strip()

    if not resume_text:
        return jsonify({"message": "'resume_text' is required"}), 400
    if not job_description and not skills_required:
        return jsonify({"message": "Provide 'job_description' or 'skills_required'"}), 400

    # ── Tokenize ─────────────────────────────────────────────────────────────

    resume_tokens   = _tokenize(resume_text)
    resume_bigrams  = _extract_bigrams(resume_tokens)
    resume_all      = resume_tokens + resume_bigrams
    resume_freq     = Counter(resume_all)

    jd_tokens       = _tokenize(job_description)
    jd_bigrams      = _extract_bigrams(jd_tokens)
    jd_all          = jd_tokens + jd_bigrams
    jd_freq         = Counter(jd_all)

    # ── Required skills matching ──────────────────────────────────────────────

    required_skills = []
    if skills_required:
        required_skills = [s.strip().lower()
                           for s in re.split(r"[,;\n]", skills_required)
                           if s.strip()]

    matched_skills  = []
    missing_skills  = []
    for skill in required_skills:
        skill_tokens = skill.split()
        # Check exact phrase in resume
        if skill in " ".join(resume_tokens) or all(t in resume_freq for t in skill_tokens):
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    skill_match_pct = (
        round(len(matched_skills) / len(required_skills) * 100)
        if required_skills else 0
    )

    # ── JD keyword overlap ────────────────────────────────────────────────────

    jd_keywords   = set(jd_all)
    res_keywords  = set(resume_all)
    overlap       = jd_keywords & res_keywords
    jd_match_pct  = (
        round(len(overlap) / len(jd_keywords) * 100)
        if jd_keywords else 0
    )

    # Top JD keywords not in resume (most impactful missing terms)
    missing_kw = sorted(
        [t for t in jd_keywords - res_keywords if len(t) > 3],
        key=lambda t: -jd_freq.get(t, 0)
    )[:12]

    # Top keywords in resume that match JD
    matching_kw = sorted(
        [t for t in overlap if len(t) > 3],
        key=lambda t: -jd_freq.get(t, 0)
    )[:12]

    # ── TF-IDF scoring ────────────────────────────────────────────────────────

    resume_tfidf = _tfidf_score(resume_freq, max(len(resume_all), 1))

    # Weighted overall score
    skill_w  = 0.6
    keyword_w = 0.4
    overall  = round(skill_match_pct * skill_w + jd_match_pct * keyword_w)

    # ── Skill categorisation ──────────────────────────────────────────────────

    categorized_matched = {}
    for sk in matched_skills:
        cat = _find_category(sk)
        categorized_matched.setdefault(cat, []).append(sk)

    categorized_missing = {}
    for sk in missing_skills:
        cat = _find_category(sk)
        categorized_missing.setdefault(cat, []).append(sk)

    # ── Suggestions ──────────────────────────────────────────────────────────

    suggestions = []
    if missing_skills:
        suggestions.append(
            f"Add these missing skills to your resume: "
            f"{', '.join(missing_skills[:5])}"
            + (f" and {len(missing_skills)-5} more." if len(missing_skills) > 5 else ".")
        )
    if missing_kw:
        suggestions.append(
            f"Consider incorporating these JD keywords: "
            f"{', '.join(missing_kw[:6])}."
        )
    if overall < 40:
        suggestions.append("Your resume may need significant tailoring for this role.")
    elif overall < 65:
        suggestions.append("A few targeted additions could significantly improve your match.")
    else:
        suggestions.append("Your profile is a strong match for this role!")

    # ── Resume strength indicators ────────────────────────────────────────────

    word_count  = len(resume_tokens)
    has_numbers = bool(re.search(r'\d+', resume_text))
    has_email   = bool(re.search(r'[^\s@]+@[^\s@]+\.[^\s@]+', resume_text))
    has_phone   = bool(re.search(r'[+\d][\d\s\-]{8,}', resume_text))
    has_links   = bool(re.search(r'https?://', resume_text))

    strength = []
    if word_count >= 300: strength.append("Good length (≥300 words)")
    else:                 strength.append(f"Resume may be too short ({word_count} words, aim for 300+)")
    if has_numbers: strength.append("Contains quantified achievements")
    if has_email:   strength.append("Contact email present")
    if has_phone:   strength.append("Contact phone present")
    if has_links:   strength.append("Online profiles/links present")

    return jsonify({
        "overall_score":     overall,
        "skill_match_pct":   skill_match_pct,
        "keyword_match_pct": jd_match_pct,
        "matched_skills":    matched_skills,
        "missing_skills":    missing_skills,
        "categorized_matched": categorized_matched,
        "categorized_missing": categorized_missing,
        "matching_keywords": matching_kw,
        "missing_keywords":  missing_kw,
        "suggestions":       suggestions,
        "resume_strength":   strength,
        "word_count":        word_count,
    }), 200
