from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Tag
from rapidfuzz import process,fuzz
router=APIRouter(prefix="/api/tags",tags=["tags"])
@router.get("")
def tags(db:Session=Depends(get_db)):
    return [{"id":t.id,"name":t.name,"count":len(t.projects)} for t in db.query(Tag).order_by(Tag.name).all()]
@router.get("/suggest")
def suggest(q:str,db:Session=Depends(get_db)):
    names=[t.name for t in db.query(Tag).all()]
    return [{"name":n,"score":s} for n,s,_ in process.extract(q,names,scorer=fuzz.ratio,limit=8) if s>=45]
