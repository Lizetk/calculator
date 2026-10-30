from openpyxl import load_workbook
from pathlib import Path

def read_excel(path):
    wb=load_workbook(path,data_only=False)
    result={"materials":[],"printers":[],"clients":[],"calculation_defaults":{},"sheets":wb.sheetnames}
    for ws in wb.worksheets:
        title=ws.title
        if "МАТЕРИАЛ" in title:
            for r in range(2,ws.max_row+1):
                name=ws.cell(r,1).value
                if name:
                    price=ws.cell(r,2).value or 0; weight=ws.cell(r,3).value or 1000
                    result["materials"].append({"name":str(name),"spool_price":float(price),"spool_weight_g":float(weight),"price_per_gram":float(price)/float(weight)})
        elif "ПРИНТЕР" in title:
            for r in range(2,ws.max_row+1):
                name=ws.cell(r,1).value
                if name:
                    result["printers"].append({"name":str(name),"average_power_w":float(ws.cell(r,2).value or 0),"purchase_price":float(ws.cell(r,3).value or 0),"resource_hours":float(ws.cell(r,4).value or 5000)})
        elif "КЛИЕНТ" in title:
            for r in range(2,ws.max_row+1):
                if ws.cell(r,1).value: result["clients"].append({"name":str(ws.cell(r,1).value),"description":str(ws.cell(r,2).value or "")})
        elif "РАСЧЁТ" in title:
            mapping={"electricity_price_kwh":"B16","defect_percent":"B19","markup_percent":"B20","ozon_logistics":"B23","ozon_other":"B24","ozon_commission_percent":"B25","acquiring_percent":"B26","tax_percent":"B27"}
            for k,cell in mapping.items():
                v=ws[cell].value
                if isinstance(v,(int,float)): result["calculation_defaults"][k]=float(v)
    return result
