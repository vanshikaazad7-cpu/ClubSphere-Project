"""Load the college's academic structure (branches + programs) from JSON.

The two JSON files under ``app/data`` are the single source of truth for the
academic hierarchy. Editing them and re-seeding is all that is needed to add or
remove courses -- no code changes required.
"""
import json
import os
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.models import Branch, Program

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _read_json(filename: str) -> dict:
    with open(os.path.join(_DATA_DIR, filename), "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_academic_data() -> Dict[str, List[dict]]:
    """Parse the JSON files into raw dicts keyed by ``branches`` / ``programs``."""
    branches = _read_json("branches.json").get("branches", [])
    programs = _read_json("programs.json").get("programs", [])
    return {"branches": branches, "programs": programs}


def seed_academic_data(db: Session) -> Dict[str, int]:
    """Seed Branch + Program rows from JSON if they are not already present.

    Returns a summary of what happened so callers can log it.
    """
    existing_branches = db.query(Branch).count()
    if existing_branches > 0:
        return {"branches": existing_branches, "programs": db.query(Program).count(), "seeded": False}

    data = load_academic_data()

    branch_key_to_id: Dict[str, int] = {}
    for idx, b in enumerate(data["branches"]):
        branch = Branch(
            BranchKey=b["id"],
            Name=b["name"],
            DegreeLevel=b["degree_level"],
            SortOrder=idx,
        )
        db.add(branch)
        db.flush()
        branch_key_to_id[b["id"]] = branch.BranchId

    for idx, p in enumerate(data["programs"]):
        branch_id = branch_key_to_id.get(p["branch_id"])
        if branch_id is None:
            # programs.json references a branch_id that is not in branches.json
            continue
        db.add(
            Program(
                ProgramKey=p["id"],
                BranchId=branch_id,
                Name=p["name"],
                FullName=p["full_name"],
                CollaborationPartner=p.get("collaboration_partner"),
                SortOrder=idx,
            )
        )

    db.commit()
    return {
        "branches": db.query(Branch).count(),
        "programs": db.query(Program).count(),
        "seeded": True,
    }
