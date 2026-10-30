from pathlib import Path
from datetime import datetime
import hashlib, json
from sqlalchemy.orm import Session
from ..models import Project, ModelFile, Tag
from .parsers import parse_model
from .thumbnail_service import make_thumbnail

SUPPORTED={".stl",".3mf",".obj",".step",".stp"}

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def scan_library(db:Session, root:Path, thumbnails:Path):
    root=root.resolve()
    stats={"found":0,"added":0,"changed":0,"unchanged":0,"errors":0}
    existing={f.relative_path:f for f in db.query(ModelFile).all()}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED: continue
        stats["found"]+=1
        rel=str(path.relative_to(root)).replace("\\", "/")
        try:
            st=path.stat(); digest=sha256(path)
            f=existing.get(rel)
            if f and f.sha256==digest and f.file_size==st.st_size and int(f.modified_at.timestamp())==int(st.st_mtime):
                stats["unchanged"]+=1; continue
            parts=Path(rel).parts
            folder=str(Path(*parts[:-1])) if len(parts)>1 else ""
            project_name=parts[-2] if len(parts)>1 else path.stem
            if f is None:
                project=db.query(Project).filter_by(relative_path=folder).first()
                if not project:
                    project=Project(name=project_name,folder_name=project_name,relative_path=folder)
                    db.add(project); db.flush()
                f=ModelFile(project_id=project.id,filename=path.name,relative_path=rel,extension=path.suffix.lower())
                db.add(f); stats["added"]+=1
            else:
                stats["changed"]+=1
            meta=parse_model(path)
            f.sha256=digest; f.file_size=st.st_size; f.modified_at=datetime.fromtimestamp(st.st_mtime)
            dims=meta.get("dimensions_mm") or [None,None,None]
            f.width_mm,f.depth_mm,f.height_mm=dims[0],dims[1],dims[2]
            f.volume_mm3=meta.get("volume_mm3")
            if not f.manual_weight and meta.get("weight_g") is not None: f.weight_g=meta.get("weight_g")
            if not f.manual_time and meta.get("print_time_seconds") is not None: f.print_time_seconds=meta.get("print_time_seconds")
            if not f.manual_material and meta.get("material") is not None: f.material=meta.get("material")
            f.metadata_json=json.dumps(meta,ensure_ascii=False)
            thumb=thumbnails/(hashlib.sha256(rel.encode()).hexdigest()+".png")
            if not thumb.exists(): make_thumbnail(path,thumb)
            project.thumbnail_path=thumb.name
            db.commit()
        except Exception:
            stats["errors"]+=1; db.rollback()
    return stats
