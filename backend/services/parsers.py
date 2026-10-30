import json, zipfile, xml.etree.ElementTree as ET, re
from pathlib import Path
import trimesh

def _parse_3mf(path):
    out={}
    try:
        with zipfile.ZipFile(path) as z:
            names=z.namelist()
            thumbs=[n for n in names if "thumbnail" in n.lower() and n.lower().endswith((".png",".jpg",".jpeg",".webp"))]
            if thumbs: out["thumbnail_member"]=thumbs[0]
            blobs=[]
            for n in names:
                if n.lower().endswith((".xml",".gcode",".json")):
                    try: blobs.append(z.read(n).decode("utf-8","ignore"))
                    except Exception: pass
            text="\n".join(blobs)
            patterns={
                "print_time_seconds":[r"total estimated time\s*=\s*(\d+)",r"estimated[_ ]print[_ ]time[^0-9]*(\d+)"],
                "weight_g":[r"total filament used\s*\[g\]\s*=\s*([0-9.]+)",r"filament[_ ]used[^0-9]*([0-9.]+)\s*g"],
                "material":[r"filament_type\s*=\s*([^\s;\r\n]+)",r"material[^:=]*[:=]\s*([A-Za-z0-9_. -]+)"],
                "layer_height":[r"layer_height\s*=\s*([0-9.]+)"],
                "infill_percent":[r"infill(?:_density)?\s*=\s*([0-9.]+)"],
                "nozzle_diameter":[r"nozzle_diameter\s*=\s*([0-9.]+)"],
            }
            for key,ps in patterns.items():
                for pat in ps:
                    m=re.search(pat,text,re.I)
                    if m:
                        val=m.group(1).strip()
                        if key=="print_time_seconds":
                            out[key]=int(val)
                        elif key in ("weight_g","layer_height","infill_percent","nozzle_diameter"):
                            out[key]=float(val)
                        else: out[key]=val
                        break
            if text:
                out["metadata_detected"]=True
    except Exception as e: out["parse_error"]=str(e)
    return out

def parse_model(path):
    ext=Path(path).suffix.lower()
    meta={}
    try:
        mesh=trimesh.load(path, force="mesh", process=False)
        if hasattr(mesh,"geometry"):
            mesh=trimesh.util.concatenate(tuple(mesh.geometry.values()))
        bounds=mesh.bounds
        dims=(bounds[1]-bounds[0]).tolist()
        volume=float(abs(mesh.volume)) if mesh.is_volume else None
        meta.update({"dimensions_mm":dims,"volume_mm3":volume})
    except Exception as e:
        meta["geometry_error"]=str(e)
    if ext==".3mf": meta.update(_parse_3mf(path))
    return meta
