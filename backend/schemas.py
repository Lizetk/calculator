from pydantic import BaseModel, Field
from typing import Any

class CalculateRequest(BaseModel):
    client_type: str="customer"
    material: str="PLA"
    printer_id: int|None=None
    weight_g: float=Field(gt=0)
    print_time_seconds: int=Field(gt=0)
    quantity: int=Field(default=1,gt=0)
    mode: str="sale"
    settings: dict[str,Any]={}

class MaterialIn(BaseModel):
    name:str; spool_price:float=0; spool_weight_g:float=1000; density:float=1.24; active:bool=True

class PrinterIn(BaseModel):
    name:str; manufacturer:str=""; model:str=""; purchase_price:float=0; resource_hours:float=5000
    average_power_w:float=80; idle_power_w:float=0; preheat_power_w:float=0; preheat_minutes:float=0
    maintenance_cost:float=0; maintenance_resource_hours:float=0; consumables_cost:float=0
    consumables_resource_hours:float=0; active:bool=True

class ProjectUpdate(BaseModel):
    name:str|None=None; notes:str|None=None; weight_g:float|None=None
    print_time_seconds:int|None=None; material:str|None=None; tags:list[str]|None=None
