from typing import Union

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

import db as database
from models import Project, ProjectMembers, User

app = FastAPI()

get_db = database.get_db


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.post("/users/")
def add_user(username: str, db: Session = Depends(get_db)):
    user = User(username=username)
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"user_id": user.id, "username": user.username}


@app.post("/project/{user_id}")
def create_project(user_id: int, name: str, db: Session = Depends(get_db)):
    project = Project(user_id=user_id, name=name)
    user = db.query(User).filter(User.id == user_id).first()
    db.add(project)
    project.members.append(user)
    # user.projects.append(project)
    db.commit()
    db.refresh(project)
    return {"project_id": project.id, "name": project.name}


@app.get("/add-member/{project_id}/{user_id}")
def add_member(project_id: int, user_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    user = db.query(User).filter(User.id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # project.members.append(user)
    user.projects.append(project)
    db.commit()
    return {"project_id": project.id, "user_id": user.id}


@app.get("/project/members/{project_id}")
def get_project_members(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "project_id": project.id,
        "members": [
            {"usernam": member.username, "user_id": member.id}
            for member in project.members
        ],
    }


@app.get("/user/projects/{user_id}")
def get_user_projects(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user_id": user.id,
        "projects": [project.name for project in user.projects],
    }


@app.get("/proj/member/table/{project_id}}")
def get_project_members_table(project_id: int, db: Session = Depends(get_db)):
    project_memmbers = (
        db.query(ProjectMembers).filter(ProjectMembers.project_id == project_id).all()
    )
    return project_memmbers


@app.delete("/proj/member/{project_id}/{user_id}")
def delete_project_member(project_id: int, user_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    user = db.query(User).filter(User.id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    project.members.remove(user)
    db.commit()
    return {"project_id": project.id, "user_id": user.id}


@app.on_event("startup")
async def on_startup():
    await database.init_db()
