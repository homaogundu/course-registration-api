from bs4 import BeautifulSoup
from fastapi import FastAPI, UploadFile, File, HTTPException

app = FastAPI()

courses = {}

def space_handling(course_code):
    return course_code.replace(" ", "").upper()

@app.get("/")
def home():
    return {"message": "Course Registration API"}

@app.post("/api/v1/admin/catalog/import")
async def import_catalog(file: UploadFile = File(...)):
    contents = await file.read()
    html = contents.decode("utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if table is None:
        raise HTTPException(status_code=400, detail="No course table found in the uploaded file")

    courses.clear()
    rows = table.find_all("tr")[1:] #skipping the header row

    for row in rows:
        cells = row.find_all(["td", "th"])

        if len(cells) < 5:
            continue

        course_code = cells[0].get_text(strip=True)
        title = cells[1].get_text(strip=True)
        credits = cells[2].get_text(strip=True)
        prerequisites = cells[3].get_text(strip=True)
        cross_listed = cells[4].get_text(strip=True)

        course_data = {
            "course_code": course_code,
            "title": title,
            "credits": credits,
            "prerequisites": prerequisites,
            "cross_listed": cross_listed
        }

        updated_key = space_handling(course_code)
        courses[updated_key] = course_data

    return {
        "message": "Course Catalog imported successfully",
    }

@app.get("/api/v1/catalog/courses/{course_code}")
def get_course(course_code: str):

    updated_key = space_handling(course_code)

    if updated_key not in courses:
        raise HTTPException(status_code=404, detail="Course not found")

    return courses[updated_key]