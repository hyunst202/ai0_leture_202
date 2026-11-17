# FASTAPI
# Create POST   status 201
# Rread  GET    
# Update PUT/PATCH
# Delete DELETE

# 초기데이터 list[dic]
# dict --> id:int(1이상) name : str (1글자), message: str (1글자 이상)
# tasks = [
#     {'id':1, 'name':'홍길동', 'message': '동해번쩍'}
# ]


from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel, Field

app = FastAPI()


# 할 일을 저장하는 목록
tasks = [
    {"id": 1, "name": "홍길동", "message": "동해번쩍"}
]


# 입력할 데이터의 규칙
class Task(BaseModel):
    id: int = Field(ge=1)               # 1 이상의 정수
    name: str = Field(min_length=1)     # 1글자 이상
    message: str = Field(min_length=1)  # 1글자 이상


# Create: 새로운 할 일 추가
@app.post("/tasks", status_code=201)
def create_task(task: Task):

    # 이미 사용 중인 번호인지 확인
    for item in tasks:
        if item["id"] == task.id:
            raise HTTPException(
                status_code=409,
                detail="이미 사용 중인 id입니다."
            )

    # 입력받은 데이터를 딕셔너리로 변환
    new_task = task.model_dump()

    # 목록에 추가
    tasks.append(new_task)

    return new_task


# Read: 전체 할 일 조회
@app.get("/tasks")
def read_tasks():
    return tasks


# Update: 입력한 id의 할 일 수정
@app.put("/tasks")
def update_task(task: Task):

    for item in tasks:
        if item["id"] == task.id:
            item["name"] = task.name
            item["message"] = task.message
            return item

    raise HTTPException(
        status_code=404,
        detail="수정할 할 일이 없습니다."
    )


# Delete: 해당 id의 할 일 삭제
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int = Path(ge=1)):

    for item in tasks:
        if item["id"] == task_id:
            tasks.remove(item)
            return {"message": "삭제했습니다."}

    raise HTTPException(
        status_code=404,
        detail="삭제할 할 일이 없습니다."
    )