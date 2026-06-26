from bs4 import BeautifulSoup
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from pydantic import BaseModel
from typing import List

app = FastAPI()

students = {}


class HistoryCourse(BaseModel):
    course_code: str
    term: str
    credits_earned: int
    status: str


class HistoryBody(BaseModel):
    history: List[HistoryCourse]


class PlannedCourse(BaseModel):
    course_code: str
    term: str


class PlanBody(BaseModel):
    planned_courses: List[PlannedCourse]


@app.get("/")
def home():
    return {"message": "Student Academic Profile API"}


def grade_rank(grade: str):
    grade = grade.strip()

    if grade == "":
        return 0

    try:
        float(grade)
        return 2
    except ValueError:
        return 1


def credits_to_int(credits_text: str):
    try:
        return int(float(credits_text.strip()))
    except ValueError:
        return 0


def parse_transcript(html: str):
    soup = BeautifulSoup(html, "html.parser")
    valid_statuses = {"Completed", "In-Progress", "Attempted"}

    deduped_courses = {}

    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")

        for row in rows[1:]:
            cells = row.find_all(["td", "th"])

            if len(cells) < 6:
                continue

            status_text = cells[0].get_text(strip=True)
            course_code = cells[1].get_text(strip=True)
            grade = cells[3].get_text(strip=True)
            term = cells[4].get_text(strip=True)
            credits = credits_to_int(cells[5].get_text(strip=True))

            if status_text not in valid_statuses:
                continue

            if term == "":
                continue

            course_record = {
                "course_code": course_code,
                "term": term,
                "credits_earned": credits,
                "status": status_text
            }

            key = (course_code, term)

            if key not in deduped_courses:
                deduped_courses[key] = {
                    "record": course_record,
                    "grade_rank": grade_rank(grade),
                    "credits": credits
                }
            else:
                existing = deduped_courses[key]

                new_grade_rank = grade_rank(grade)

                if new_grade_rank > existing["grade_rank"]:
                    deduped_courses[key] = {
                        "record": course_record,
                        "grade_rank": new_grade_rank,
                        "credits": credits
                    }
                elif new_grade_rank == existing["grade_rank"] and credits > existing["credits"]:
                    deduped_courses[key] = {
                        "record": course_record,
                        "grade_rank": new_grade_rank,
                        "credits": credits
                    }

    return [item["record"] for item in deduped_courses.values()]


@app.post("/api/v1/students/{student_id}/history/import", status_code=status.HTTP_201_CREATED)
async def import_history(student_id: str, file: UploadFile = File(...)):
    contents = await file.read()
    html = contents.decode("utf-8", errors="ignore")

    history = parse_transcript(html)

    students[student_id] = {
        "history": history,
        "plan": []
    }

    return {
        "status": "success",
        "past_courses_imported": len(history)
    }


@app.put("/api/v1/students/{student_id}/history")
def update_history(student_id: str, body: HistoryBody):
    if student_id not in students:
        raise HTTPException(status_code=404, detail="Student not found")

    students[student_id]["history"] = [course.model_dump() for course in body.history]

    return {
        "status": "success",
        "message": "Academic history updated successfully"
    }


@app.delete("/api/v1/students/{student_id}/history")
def delete_history(student_id: str):
    if student_id not in students:
        raise HTTPException(status_code=404, detail="Student not found")

    students[student_id]["history"] = []

    return {"status": "success"}


@app.post("/api/v1/students/{student_id}/plan")
def create_plan(student_id: str, body: PlanBody):
    if student_id not in students:
        raise HTTPException(status_code=404, detail="Student not found")

    students[student_id]["plan"] = [course.model_dump() for course in body.planned_courses]

    return {
        "status": "success",
        "planned_courses_saved": len(body.planned_courses)
    }


@app.put("/api/v1/students/{student_id}/plan")
def update_plan(student_id: str, body: PlanBody):
    if student_id not in students:
        raise HTTPException(status_code=404, detail="Student not found")

    students[student_id]["plan"] = [course.model_dump() for course in body.planned_courses]

    return {
        "status": "success",
        "planned_courses_saved": len(body.planned_courses)
    }


@app.delete("/api/v1/students/{student_id}/plan")
def delete_plan(student_id: str):
    if student_id not in students:
        raise HTTPException(status_code=404, detail="Student not found")

    students[student_id]["plan"] = []

    return {"status": "success"}


@app.get("/api/v1/students/{student_id}/profile")
def get_profile(student_id: str):
    if student_id not in students:
        raise HTTPException(status_code=404, detail="Student not found")

    return {
        "student_id": student_id,
        "history": students[student_id]["history"],
        "plan": students[student_id]["plan"]
    }

##****** PHASE-2


##****** PHASE-1

# courses = {}

# def space_handling(course_code):
#     return course_code.replace(" ", "").upper()

# @app.get("/")
# def home():
#     return {"message": "Course Registration API"}

# @app.post("/api/v1/admin/catalog/import")
# async def import_catalog(file: UploadFile = File(...)):
#     contents = await file.read()
#     html = contents.decode("utf-8", errors="ignore")
#     soup = BeautifulSoup(html, "html.parser")
#     table = soup.find("table")
#     if table is None:
#         raise HTTPException(status_code=400, detail="No course table found in the uploaded file")

#     courses.clear()
#     rows = table.find_all("tr")[1:] #skipping the header row

#     for row in rows:
#         cells = row.find_all(["td", "th"])

#         if len(cells) < 5:
#             continue

#         course_code = cells[0].get_text(strip=True)
#         title = cells[1].get_text(strip=True)
#         credits = cells[2].get_text(strip=True)
#         prerequisites = cells[3].get_text(strip=True)
#         cross_listed = cells[4].get_text(strip=True)

#         course_data = {
#             "course_code": course_code,
#             "title": title,
#             "credits": credits,
#             "prerequisites": prerequisites,
#             "cross_listed": cross_listed
#         }

#         updated_key = space_handling(course_code)
#         courses[updated_key] = course_data

#     return {
#         "message": "Course Catalog imported successfully",
#     }

# @app.get("/api/v1/catalog/courses/{course_code}")
# def get_course(course_code: str):

#     updated_key = space_handling(course_code)

#     if updated_key not in courses:
#         raise HTTPException(status_code=404, detail="Course not found")

#     return courses[updated_key]