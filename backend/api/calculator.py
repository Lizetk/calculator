import json
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Material,Printer,Setting,CalculationHistory
from ..schemas import CalculateRequest
from ..calculation_engine import calculate,CalcConfig
router=APIRouter(prefix="/api",tags=["calculator"])

def sval(db,k,default):
    s=db.get(Setting,k)
    if not s:return default
    try:return json.loads(s.value)
    except:return default

@router.post("/calculate")
def calc(req:CalculateRequest,db:Session=Depends(get_db)):
    m=db.query(Material).filter(Material.name==req.material).first()
    if not m or not m.active: raise HTTPException(400,f"Для материала {req.material} не указана цена.")
    p=db.get(Printer,req.printer_id) if req.printer_id else db.query(Printer).filter(Printer.active==True).first()
    if not p: raise HTTPException(400,"Не выбран принтер.")
    c=CalcConfig(
      material_price_per_g=m.spool_price/m.spool_weight_g if m.spool_weight_g else 0,
      power_w=p.average_power_w,electricity_price_kwh=sval(db,"electricity_price_kwh",8),
      printer_purchase_price=p.purchase_price,printer_resource_hours=p.resource_hours,
      maintenance_cost=p.maintenance_cost,maintenance_resource_hours=p.maintenance_resource_hours,
      consumables_cost=p.consumables_cost,consumables_resource_hours=p.consumables_resource_hours,
      defect_percent=sval(db,"defect_percent",10),operator_rate=sval(db,"operator_rate",150),
      prep_minutes=sval(db,"prep_minutes",15),post_minutes=sval(db,"post_minutes",0),
      packaging_per_unit=sval(db,"packaging_per_unit",0),other_per_unit=sval(db,"other_per_unit",0),
      markup_percent=sval(db,"markup_percent",30),target_profit_percent=sval(db,"target_profit_percent",30),
      ozon_commission_percent=sval(db,"ozon_commission_percent",15),acquiring_percent=sval(db,"acquiring_percent",1.5),
      tax_percent=sval(db,"tax_percent",6),ozon_logistics=sval(db,"ozon_logistics",60),
      ozon_fixed_fee=sval(db,"ozon_fixed_fee",0),ozon_other=sval(db,"ozon_other",50))
    try:r=calculate(req.model_dump(),c)
    except ValueError as e:raise HTTPException(400,str(e))
    h=CalculationHistory(project_id=None,client_type=req.client_type,material=req.material,weight_g=req.weight_g,print_time_seconds=req.print_time_seconds,quantity=req.quantity,mode=req.mode,result_json=json.dumps(r,ensure_ascii=False));db.add(h);db.commit()
    return r

@router.get("/calculation-history")
def history(db:Session=Depends(get_db)):
    return [{"id":h.id,"client_type":h.client_type,"material":h.material,"weight_g":h.weight_g,"quantity":h.quantity,"result":json.loads(h.result_json),"created_at":h.created_at.isoformat()} for h in db.query(CalculationHistory).order_by(CalculationHistory.created_at.desc()).limit(100).all()]
