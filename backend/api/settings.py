import json, shutil
from pathlib import Path
from fastapi import APIRouter,Depends,HTTPException,UploadFile,File
from sqlalchemy.orm import Session
from ..database import get_db,ROOT
from ..models import Setting,Material,Printer
from ..services.excel_importer import read_excel
router=APIRouter(prefix="/api/settings",tags=["settings"])

def get_all(db):
    return {s.key:s.value for s in db.query(Setting).all()}

@router.get("")
def settings(db:Session=Depends(get_db)):
    return {"settings":get_all(db),"materials":[{"id":m.id,"name":m.name,"spool_price":m.spool_price,"spool_weight_g":m.spool_weight_g,"density":m.density,"active":m.active,"price_per_gram":m.spool_price/m.spool_weight_g if m.spool_weight_g else 0} for m in db.query(Material).all()],"printers":[{"id":p.id,"name":p.name,"manufacturer":p.manufacturer,"model":p.model,"purchase_price":p.purchase_price,"resource_hours":p.resource_hours,"average_power_w":p.average_power_w,"maintenance_cost":p.maintenance_cost,"maintenance_resource_hours":p.maintenance_resource_hours,"consumables_cost":p.consumables_cost,"consumables_resource_hours":p.consumables_resource_hours,"active":p.active} for p in db.query(Printer).all()]}

@router.put("")
def save_settings(payload:dict,db:Session=Depends(get_db)):
    for k,v in payload.get("settings",{}).items():
        s=db.get(Setting,k) or Setting(key=k);s.value=json.dumps(v,ensure_ascii=False);db.add(s)
    db.commit();return settings(db)

@router.post("/excel/import")
async def import_excel(file:UploadFile=File(...),db:Session=Depends(get_db)):
    tmp=ROOT/"data"/"_import.xlsx";tmp.write_bytes(await file.read())
    result=read_excel(tmp);tmp.unlink(missing_ok=True)
    return result

@router.post("/backup")
def backup(db:Session=Depends(get_db)):
    import zipfile,datetime
    out=ROOT/"data"/"backups"/f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        for p in [ROOT/"data"/"database.sqlite",ROOT/"data"/"thumbnails"]:
            if p.is_file():z.write(p,p.relative_to(ROOT))
            elif p.exists():
                for f in p.rglob("*"):
                    if f.is_file():z.write(f,f.relative_to(ROOT))
    return {"path":str(out)}

@router.put("/materials/{material_id}")
def update_material(material_id:int,payload:dict,db:Session=Depends(get_db)):
    m=db.get(Material,material_id)
    if not m: raise HTTPException(404,"Material not found")
    for k in ("name","spool_price","spool_weight_g","density","active"):
        if k in payload:setattr(m,k,payload[k])
    db.commit();return {"ok":True}

@router.post("/excel/apply")
async def apply_excel(file:UploadFile=File(...),db:Session=Depends(get_db)):
    tmp=ROOT/"data"/"_import_apply.xlsx";tmp.write_bytes(await file.read())
    result=read_excel(tmp);tmp.unlink(missing_ok=True)
    for x in result["materials"]:
        m=db.query(Material).filter_by(name=x["name"]).first()
        if not m:m=Material(name=x["name"]);db.add(m)
        m.spool_price=x["spool_price"];m.spool_weight_g=x["spool_weight_g"]
    for x in result["printers"]:
        p=db.query(Printer).filter_by(name=x["name"]).first()
        if not p:p=Printer(name=x["name"]);db.add(p)
        p.average_power_w=x["average_power_w"];p.purchase_price=x["purchase_price"];p.resource_hours=x["resource_hours"]
    for k,v in result["calculation_defaults"].items():
        st=db.get(Setting,k) or Setting(key=k);st.value=json.dumps(v);db.add(st)
    db.commit();return {"ok":True,"imported":result}
