from backend.calculation_engine import calculate,CalcConfig
def cfg():
    return CalcConfig(2,80,8,30000,5000,0,0,0,0,10,150,15,0,0,0,50,30,15,1.5,6,60,0,50)
def test_material_and_quantity():
    r=calculate({"client_type":"friend","weight_g":100,"print_time_seconds":3600,"quantity":2,"mode":"hobby"},cfg())
    assert r["material_cost"]==400
    assert r["quantity"]==2
def test_customer_markup():
    r=calculate({"client_type":"customer","weight_g":100,"print_time_seconds":3600,"quantity":1,"mode":"sale"},cfg())
    assert r["recommended_price"]>=r["break_even_cost"]
def test_ozon_denominator():
    c=cfg(); c.ozon_commission_percent=90;c.acquiring_percent=10
    try: calculate({"client_type":"ozon","weight_g":1,"print_time_seconds":60,"quantity":1,"mode":"sale"},c)
    except ValueError: return
    assert False
