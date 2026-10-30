from dataclasses import dataclass
from typing import Any

@dataclass
class CalcConfig:
    material_price_per_g: float
    power_w: float
    electricity_price_kwh: float
    printer_purchase_price: float
    printer_resource_hours: float
    maintenance_cost: float
    maintenance_resource_hours: float
    consumables_cost: float
    consumables_resource_hours: float
    defect_percent: float
    operator_rate: float
    prep_minutes: float
    post_minutes: float
    packaging_per_unit: float
    other_per_unit: float
    markup_percent: float
    target_profit_percent: float
    ozon_commission_percent: float
    acquiring_percent: float
    tax_percent: float
    ozon_logistics: float
    ozon_fixed_fee: float
    ozon_other: float

def calculate(req: dict[str,Any], c: CalcConfig)->dict[str,Any]:
    weight=req["weight_g"]; hours=req["print_time_seconds"]/3600; qty=req["quantity"]
    material=weight*c.material_price_per_g
    electricity=(c.power_w/1000)*hours*c.electricity_price_kwh
    printer_resource=(c.printer_purchase_price/c.printer_resource_hours*hours) if c.printer_resource_hours else 0
    maintenance=(c.maintenance_cost/c.maintenance_resource_hours*hours) if c.maintenance_resource_hours else 0
    consumables=(c.consumables_cost/c.consumables_resource_hours*hours) if c.consumables_resource_hours else 0
    operator=((c.prep_minutes+c.post_minutes)/60*c.operator_rate) if req.get("mode")=="sale" else 0
    packaging=c.packaging_per_unit
    other=c.other_per_unit
    direct=material+electricity+printer_resource+maintenance+consumables+operator+packaging+other
    defect_rate=min(max(c.defect_percent/100,0),0.999999)
    waste=direct*(1/(1-defect_rate)-1) if defect_rate else 0
    break_even=direct+waste
    client=req["client_type"].lower()
    if client=="friend":
        unit_price=break_even
        profit=0
        ozon_comm=acquiring=tax=0
        recommended=unit_price
    elif client=="ozon":
        fixed=c.ozon_logistics+c.ozon_fixed_fee+c.ozon_other
        desired_profit=break_even*(c.markup_percent/100)
        denom=1-(c.ozon_commission_percent+c.acquiring_percent+c.tax_percent)/100
        if denom<=0: raise ValueError("Комиссия Ozon + эквайринг + налог не могут быть 100% или больше.")
        recommended=(break_even+fixed+desired_profit)/denom
        ozon_comm=recommended*c.ozon_commission_percent/100
        acquiring=recommended*c.acquiring_percent/100
        tax=recommended*c.tax_percent/100
        profit=recommended-ozon_comm-acquiring-tax-fixed-break_even
        unit_price=recommended
    else:
        recommended=break_even*(1+c.markup_percent/100)
        ozon_comm=acquiring=tax=0
        profit=recommended-break_even
        unit_price=recommended
    total_cost=break_even*qty
    total_price=unit_price*qty
    return {
        "material_cost":material*qty,"electricity_cost":electricity*qty,
        "printer_resource_cost":printer_resource*qty,"maintenance_cost":maintenance*qty,
        "consumables_cost":consumables*qty,"operator_cost":operator*qty,
        "packaging_cost":packaging*qty,"other_cost":other*qty,"waste_reserve":waste*qty,
        "direct_cost":direct*qty,"break_even_cost":total_cost,"recommended_price":total_price,
        "price_per_unit":unit_price,"profit":profit*qty,"profit_per_unit":profit,
        "ozon_commission":ozon_comm*qty,"acquiring":acquiring*qty,"tax":tax*qty,
        "ozon_fixed_and_logistics":(c.ozon_logistics+c.ozon_fixed_fee+c.ozon_other)*qty if client=="ozon" else 0,
        "margin_percent":(profit/unit_price*100) if unit_price else 0,
        "quantity":qty,"print_time_hours":hours
    }
