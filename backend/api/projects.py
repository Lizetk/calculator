from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..database import get_db
from ..models import Project, ModelFile, Tag
from ..schemas import ProjectUpdate
from rapidfuzz import fuzz, process

router=APIRouter(prefix="/api/projects",tags=["projects"])

def project_json(p):
    fs=[]
    for f in p.files:
        fs.append({"id":f.id,"filename":f.filename,"relative_path":f.relative_path,"extension":f.extension,"weight_g":f.weight_g,"print_time_seconds":f.print_time_seconds,"volume_mm3":f.volume_mm3,"dimensions_mm":[f.width_mm,f.depth_mm,f.height_mm],"material":f.material,"file_size":f.file_size,"modified_at":f.modified_at.isoformat(),"metadata":__import__("json").loads(f.metadata_json or "{}")})
    return {"id":p.id,"name":p.name,"folder_name":p.folder_name,"relative_path":p.relative_path,"thumbnail":p.thumbnail_path,"notes":p.notes,"tags":[t.name for t in p.tags],"files":fs,"updated_at":p.updated_at.isoformat()}

def fuzzy_text_match(query:str, value:str)->bool:
    if not query or not value:
        return False
    query=query.strip().casefold()
    value=(value or "").casefold()
    if query in value:
        return True
    if len(query) < 4:
        return False
    words=[w for w in value.replace("#"," ").replace(","," ").split() if w]
    candidates=words + [value]
    return any(fuzz.ratio(query,candidate) >= 80 for candidate in candidates)


@router.get("")
def list_projects(q:str="",tag:str="",page:int=1,page_size:int=48,db:Session=Depends(get_db)):
    # Unicode/case-insensitive search with typo tolerance.
    # Exact substring matching is checked first. For queries of 4+ characters,
    # fuzzy matching at ~80% similarity catches small typos such as:
    # "фанарик" -> "фонарик".
    projects=db.query(Project).order_by(Project.updated_at.desc()).all()
    qn=q.strip().casefold()
    tn=tag.strip().casefold()

    def fuzzy_match(query, value):
        if not query or not value:
            return False
        value=(value or "").casefold()
        if query in value:
            return True
        if len(query) < 4:
            return False
        # Compare against individual words as well as the complete field.
        words=[w for w in value.replace("#"," ").replace(","," ").split() if w]
        candidates=words + [value]
        return any(fuzz.ratio(query,candidate) >= 80 for candidate in candidates)

    if qn:
        def matches_query(p):
            values=[p.name,p.folder_name,p.relative_path]
            values += [f.filename for f in p.files]
            values += [t.name for t in p.tags]
            # For multi-word queries, every query word must be found somewhere.
            query_parts=[part for part in qn.split() if part]
            return all(any(fuzzy_text_match(part,v) for v in values) for part in query_parts)
        projects=[p for p in projects if matches_query(p)]
    if tn:
        projects=[p for p in projects if any(tn in (t.name or "").casefold() for t in p.tags)]
    total=len(projects)
    start=(max(page,1)-1)*page_size
    items=projects[start:start+page_size]
    return {"items":[project_json(p) for p in items],"total":total,"page":page,"page_size":page_size}

@router.get("/{project_id}")
def get_project(project_id:int,db:Session=Depends(get_db)):
    p=db.get(Project,project_id)
    if not p: raise HTTPException(404,"Project not found")
    return project_json(p)

@router.put("/{project_id}")
def update_project(project_id:int,data:ProjectUpdate,db:Session=Depends(get_db)):
    p=db.get(Project,project_id)
    if not p: raise HTTPException(404,"Project not found")
    if data.name is not None:p.name=data.name
    if data.notes is not None:p.notes=data.notes
    if data.tags is not None:
        p.tags=[]
        for name in data.tags:
            t=db.query(Tag).filter_by(name=name.strip()).first()
            if not t:t=Tag(name=name.strip());db.add(t)
            if t.name:p.tags.append(t)
    if any(v is not None for v in [data.weight_g,data.print_time_seconds,data.material]):
        if not p.files: raise HTTPException(400,"Project has no files")
        f=p.files[0]
        if data.weight_g is not None:f.weight_g=data.weight_g;f.manual_weight=True
        if data.print_time_seconds is not None:f.print_time_seconds=data.print_time_seconds;f.manual_time=True
        if data.material is not None:f.material=data.material;f.manual_material=True
    db.commit();db.refresh(p);return project_json(p)
