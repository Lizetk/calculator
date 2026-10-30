import json, logging, webbrowser, threading, os, uuid, shutil
from pathlib import Path
from fastapi import FastAPI,Depends,HTTPException,UploadFile,File,Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from .database import Base,engine,SessionLocal,get_db,ROOT
from .models import Material,Printer,Setting,CalculationProfile,Project,ModelFile,Tag
from .api.projects import router as projects_router, project_json
from .api.tags import router as tags_router
from .api.settings import router as settings_router
from .api.calculator import router as calculator_router
from .services.scanner import scan_library

LOG=ROOT/"logs"/"app.log";LOG.parent.mkdir(exist_ok=True)
logging.basicConfig(filename=LOG,level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
Base.metadata.create_all(bind=engine)
app=FastAPI(title="3D Print Manager",version="1.0.0")
app.include_router(projects_router);app.include_router(tags_router);app.include_router(settings_router);app.include_router(calculator_router)

def seed():
    db=SessionLocal()
    defaults=[("PLA",1600,1000,1.24),("PETG",1400,1000,1.27),("ABS",1300,1000,1.04),("TPU",2500,500,1.21)]
    for n,price,w,d in defaults:
        if not db.query(Material).filter_by(name=n).first():db.add(Material(name=n,spool_price=price,spool_weight_g=w,density=d))
    if not db.query(Printer).first():db.add(Printer(name="Ender 3 V3 KE",manufacturer="Creality",model="Ender 3 V3 KE",purchase_price=30000,resource_hours=5000,average_power_w=80))
    settings={"electricity_price_kwh":8,"defect_percent":10,"markup_percent":50,"operator_rate":150,"prep_minutes":15,"post_minutes":0,"packaging_per_unit":0,"other_per_unit":0,"ozon_commission_percent":15,"acquiring_percent":1.5,"tax_percent":6,"ozon_logistics":60,"ozon_fixed_fee":0,"ozon_other":50}
    for k,v in settings.items():
        if not db.get(Setting,k):db.add(Setting(key=k,value=json.dumps(v)))
    for name,typ in [("Друг","friend"),("Заказчик","customer"),("Ozon","ozon")]:
        if not db.query(CalculationProfile).filter_by(type=typ).first():db.add(CalculationProfile(name=name,type=typ,settings_json="{}"))
    db.commit();db.close()
seed()


@app.get("/api/system/select-folder")
def select_folder():
    try:
        import tkinter as tk
        from tkinter import filedialog
        root=tk.Tk();root.withdraw();root.attributes("-topmost",True)
        p=filedialog.askdirectory(title="Выберите папку с 3D-моделями");root.destroy()
        return {"path":p}
    except Exception as e:
        return {"path":"","error":str(e)}



@app.post("/api/projects/manual")
async def create_manual_project(
    model: UploadFile = File(...),
    name: str = Form(...),
    tags: str = Form(""),
    weight_g: float = Form(...),
    print_time_seconds: int = Form(...),
    material: str = Form(""),
    thumbnail: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    allowed = {".stl", ".3mf", ".obj", ".step", ".stp"}
    original_name = Path(model.filename or "model").name
    ext = Path(original_name).suffix.lower()
    if ext not in allowed:
        raise HTTPException(400, "Поддерживаются STL, 3MF, OBJ, STEP и STP.")
    if not name.strip():
        raise HTTPException(400, "Введите название проекта.")
    if weight_g <= 0 or print_time_seconds <= 0:
        raise HTTPException(400, "Вес и время печати должны быть больше нуля.")

    uid = uuid.uuid4().hex
    (ROOT / "data" / "thumbnails").mkdir(parents=True, exist_ok=True)
    model_dir = ROOT / "data" / "models" / uid
    model_dir.mkdir(parents=True, exist_ok=True)
    target = model_dir / original_name
    target.write_bytes(await model.read())

    thumb_name = None
    if thumbnail and thumbnail.filename:
        try:
            from PIL import Image
            import io
            raw = await thumbnail.read()
            im = Image.open(io.BytesIO(raw)).convert("RGB")
            im.thumbnail((900, 700))
            thumb_name = f"manual_{uid}.jpg"
            im.save(ROOT / "data" / "thumbnails" / thumb_name, "JPEG", quality=90)
        except Exception as e:
            logging.exception("Manual thumbnail failed: %s", e)
            thumb_name = None

    p = Project(
        name=name.strip(),
        folder_name="Добавлено вручную",
        relative_path="",
        thumbnail_path=thumb_name,
    )
    db.add(p)
    db.flush()
    mf = ModelFile(
        project_id=p.id,
        filename=original_name,
        relative_path=f"manual/{uid}/{original_name}",
        extension=ext,
        sha256=__import__("hashlib").sha256(target.read_bytes()).hexdigest(),
        file_size=target.stat().st_size,
        modified_at=__import__("datetime").datetime.utcnow(),
        weight_g=weight_g,
        print_time_seconds=print_time_seconds,
        material=material.strip() or None,
        manual_weight=True,
        manual_time=True,
        manual_material=bool(material.strip()),
    )
    db.add(mf)
    tag_names = [x.strip() for x in tags.split(",") if x.strip()]
    seen = set()
    for tag_name in tag_names:
        key = tag_name.casefold()
        if key in seen:
            continue
        seen.add(key)
        t = db.query(Tag).filter(Tag.name.ilike(tag_name)).first()
        if not t:
            t = Tag(name=tag_name)
            db.add(t)
            db.flush()
        p.tags.append(t)
    db.commit()
    db.refresh(p)
    return {"project": project_json(p)}

@app.get("/api/health")
def health(): return {"ok":True}

@app.post("/api/library/scan")
def scan(payload:dict,db:Session=Depends(get_db)):
    root=payload.get("root")
    if not root or not Path(root).is_dir(): raise HTTPException(400,"Корневая папка не найдена.")
    s=db.get(Setting,"library_root") or Setting(key="library_root")
    s.value=json.dumps(str(Path(root).resolve()),ensure_ascii=False); db.add(s); db.commit()
    return scan_library(db,Path(root),ROOT/"data"/"thumbnails")

@app.get("/api/file/{file_id}")
def get_file(file_id:int,db:Session=Depends(get_db)):
    from .models import ModelFile
    f=db.get(ModelFile,file_id)
    if not f: raise HTTPException(404,"File not found")
    if f.relative_path.startswith("manual/"):
        path=ROOT/"data"/"models"/Path(f.relative_path).relative_to("manual")
    else:
        root_setting=db.get(Setting,"library_root")
        if not root_setting: raise HTTPException(404,"Library root not configured")
        path=Path(json.loads(root_setting.value))/f.relative_path
    if not path.exists(): raise HTTPException(404,"File not found on disk")
    return FileResponse(path,filename=f.filename)

@app.get("/api/thumbnail/{filename}")
def thumbnail(filename:str):
    p=ROOT/"data"/"thumbnails"/filename
    if not p.exists():raise HTTPException(404)
    return FileResponse(p)

frontend_dist=ROOT/"frontend"/"dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
else:
    @app.get("/{path:path}")
    def spa(path:str):
        return {"message":"Frontend is not built. Run start_windows.bat."}
