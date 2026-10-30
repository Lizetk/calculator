from pathlib import Path
from PIL import Image, ImageDraw
import zipfile, io, math
import trimesh, numpy as np

def make_thumbnail(path, out):
    out=Path(out); out.parent.mkdir(parents=True,exist_ok=True)
    if Path(path).suffix.lower()==".3mf":
        try:
            with zipfile.ZipFile(path) as z:
                for n in z.namelist():
                    if "thumbnail" in n.lower() and n.lower().endswith((".png",".jpg",".jpeg",".webp")):
                        data=z.read(n); im=Image.open(io.BytesIO(data)).convert("RGB"); im.thumbnail((640,640))
                        canvas=Image.new("RGB",(640,640),(20,23,28)); canvas.paste(im,((640-im.width)//2,(640-im.height)//2)); canvas.save(out,"PNG"); return
        except Exception: pass
    try:
        mesh=trimesh.load(path, force="mesh", process=False)
        if hasattr(mesh,"geometry"): mesh=trimesh.util.concatenate(tuple(mesh.geometry.values()))
        v=np.asarray(mesh.vertices)
        if len(v)==0: raise ValueError("empty")
        # isometric-like projection, normalized into a 640x640 image
        x=v[:,0]*0.866-v[:,1]*0.866
        y=v[:,2]-0.5*(v[:,0]+v[:,1])*0.5
        x=(x-x.min())/(max(x.max()-x.min(),1e-9))*520+60
        y=560-(y-y.min())/(max(y.max()-y.min(),1e-9))*460
        im=Image.new("RGB",(640,640),(20,23,28)); d=ImageDraw.Draw(im)
        # draw sampled triangle edges for manageable size
        faces=np.asarray(mesh.faces)
        step=max(1,len(faces)//3000)
        for tri in faces[::step]:
            pts=[(float(x[i]),float(y[i])) for i in tri]
            d.line(pts+[pts[0]],fill=(145,170,195),width=1)
        im.save(out,"PNG")
    except Exception:
        Image.new("RGB",(640,640),(35,38,45)).save(out,"PNG")
