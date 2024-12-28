from fastapi import APIRouter

api_router = APIRouter(
    prefix="/api",
)


@api_router.get("/students/")
def get_students():
    return ["Student_1", "Student_2", "Student_3"]


@api_router.get("/students/{student_id}")
def get_student_by_id(student_id):
    return {
        "student": {
            "id": student_id,
        }
    }
