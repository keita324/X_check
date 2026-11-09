"""Video renderer: takes segments json and writes video (no audio)."""
import json,subprocess,numpy as np,sys,random,cv2
_casc=cv2.CascadeClassifier('models/face.xml')
_fcache={}
def face_of(img,key):
    if key in _fcache: return _fcache[key]
    g=cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
    fs=_casc.detectMultiScale(g,1.1,6,minSize=(60,60))
    r=None
    if len(fs):
        x,y,w,h=max(fs,key=lambda f:f[2]*f[3]); r=((x+w/2)/1280,(y+h/2)/720,h/720)
    _fcache[key]=r; return r
from PIL import Image,ImageDraw,ImageFont,ImageFilter
W,H,FPS=1280,720,30
SRC="dl/src.bin"
FONT="/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
_fc={}
def font(sz):
    if sz not in _fc:_fc[sz]=ImageFont.truetype(FONT,sz)
    return _fc[sz]
_cache={}
def grab(src_t,n):
    key=(round(src_t,3),n)
    if key in _cache: return _cache[key]
    cmd=["ffmpeg","-v","error","-ss",f"{max(0,src_t):.3f}","-i",SRC,"-frames:v",str(n),
         "-vf",f"fps={FPS},scale={W}:{H}","-f","rawvideo","-pix_fmt","rgb24","-"]
    raw=subprocess.run(cmd,capture_output=True).stdout
    fr=np.frombuffer(raw,np.uint8).reshape(-1,H,W,3)
    if len(fr)==0: fr=np.zeros((1,H,W,3),np.uint8)
    if len(fr)<n: fr=np.concatenate([fr,np.repeat(fr[-1:],n-len(fr),0)])
    _cache[key]=fr
    return fr
def zoom(img,z,cx=0.5,cy=0.5):
    if abs(z-1)<1e-3: return img
    h,w=img.shape[:2]; cw,ch=int(w/z),int(h/z)
    x0=int(np.clip(cx*w-cw/2,0,w-cw)); y0=int(np.clip(cy*h-ch/2,0,h-ch))
    return np.asarray(Image.fromarray(img[y0:y0+ch,x0:x0+cw]).resize((w,h),Image.BILINEAR))
def tile(img,k):
    small=np.asarray(Image.fromarray(img).resize((W//k,H//k),Image.BILINEAR))
    out=np.tile(small,(k,k,1))
    return np.pad(out,((0,H-out.shape[0]),(0,W-out.shape[1]),(0,0)),mode='edge')
def hue_rot(img,deg):
    im=Image.fromarray(img).convert("HSV"); a=np.asarray(im).copy()
    a[...,0]=(a[...,0].astype(int)+int(deg/360*255))%256
    return np.asarray(Image.fromarray(a,"HSV").convert("RGB"))
def apply_fx(img,fx,i,n,rng,face=None):
    p=i/max(1,n-1)
    for f in fx:
        if f.startswith("zc:"):
            _,x,y,z,mode=f.split(":"); x,y,z=float(x),float(y),float(z)
            if mode=="punch": z=z*(1+0.3*max(0,1-i/4))
            elif mode=="slow": z=1+(z-1)*min(1,p*1.2)
            img=zoom(img,z,x,y); continue
        if f in("face","faceslow","facebig","facepunch"):
            if face is None: img=zoom(img,{"face":1.5,"faceslow":1.0+0.5*p,"facebig":1.9,"facepunch":1.5+0.4*max(0,1-i/4)}[f]); continue
            cx,cy,fh=face
            base=min(max(0.42/fh,1.4),2.6)
            z={"face":base,"faceslow":1.0+(base-1)*min(1,p*1.3),"facebig":base*1.25,"facepunch":base*(1+0.25*max(0,1-i/4))}[f]
            img=zoom(img,z,cx,cy); continue
        if f=="zoom": img=zoom(img,1.0+0.35*max(0,1-i/4))
        elif f=="zoomin": img=zoom(img,1.0+0.6*p)
        elif f=="bigzoom": img=zoom(img,1.6)
        elif f=="flip": img=img[:,::-1]
        elif f=="vflip": img=img[::-1]
        elif f=="invert": img=255-img
        elif f=="tile2": img=tile(img,2)
        elif f=="tile3": img=tile(img,3)
        elif f=="tile4": img=tile(img,4)
        elif f=="mirror": img=img.copy(); img[:,W//2:]=img[:,:W//2][:,::-1]
        elif f=="shake":
            dx,dy=rng.randint(-25,25),rng.randint(-18,18); img=np.roll(img,(dy,dx),(0,1))
        elif f=="rgb":
            o=img.copy(); o[...,0]=np.roll(img[...,0],14,1); o[...,2]=np.roll(img[...,2],-14,1); img=o
        elif f=="hue": img=hue_rot(img,(i*40)%360)
        elif f=="gray": g=img.mean(2,keepdims=True).astype(np.uint8); img=np.repeat(g,3,2)
        elif f=="squash":
            s=1.0-0.25*max(0,1-i/5); hh=int(H*s)
            im=np.asarray(Image.fromarray(img).resize((W,hh))); img=np.zeros_like(img); img[H-hh:]=im
        elif f=="rot":
            img=np.asarray(Image.fromarray(img).rotate(8*np.sin(i*0.9),resample=Image.BILINEAR,expand=False))
        elif f=="freeze": pass
    return img
def draw_text(img,text,style,i):
    if not text: return img
    im=Image.fromarray(img); d=ImageDraw.Draw(im)
    sz=style.get("size",110)
    if style.get("pop") and i<3: sz=int(sz*(1.35-0.12*i))
    f=font(sz)
    bb=d.textbbox((0,0),text,font=f,stroke_width=8)
    tw,th=bb[2]-bb[0],bb[3]-bb[1]
    if tw>W-40:
        sz=int(sz*(W-40)/tw); f=font(sz); bb=d.textbbox((0,0),text,font=f,stroke_width=8); tw,th=bb[2]-bb[0],bb[3]-bb[1]
    pos=style.get("pos","bottom")
    x=(W-tw)//2-bb[0]
    y={"bottom":H-th-40,"center":(H-th)//2,"top":30}[pos]-bb[1]
    d.text((x,y),text,font=f,fill=style.get("color","#ffffff"),stroke_width=max(6,sz//14),stroke_fill=style.get("stroke","#000000"))
    return np.asarray(im)
def render(segs,flashes,total,out):
    nfr=int(round(total*FPS))
    enc=subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
        "-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p",out],stdin=subprocess.PIPE)
    rng=random.Random(7)
    segs=sorted(segs,key=lambda s:s["t"])
    fl=np.zeros(nfr)
    for t,a in flashes:
        f0=int(round(t*FPS))
        for k in range(4):
            if 0<=f0+k<nfr: fl[f0+k]=max(fl[f0+k],a*(1-k/4))
    for si,s in enumerate(segs):
        f0=int(round(s["t"]*FPS)); f1=int(round(segs[si+1]["t"]*FPS)) if si+1<len(segs) else nfr
        f1=min(f1,nfr); n=f1-f0
        if n<=0: continue
        if s.get("black"):
            frames=np.zeros((n,H,W,3),np.uint8)
        else:
            frames=grab(s["src"],n if "freeze" not in s.get("fx",[]) else 1)
        face=None
        if any(f.startswith("face") for f in s.get("fx",[])) and not s.get("black"):
            face=face_of(frames[0],(round(s["src"],2)))
        for i in range(n):
            img=frames[min(i,len(frames)-1)]
            img=apply_fx(img,s.get("fx",[]),i,n,rng,face)
            img=draw_text(img,s.get("text",""),s.get("ts",{}),i)
            a=fl[f0+i]
            if a>0: img=(img*(1-a)+255*a).astype(np.uint8)
            enc.stdin.write(np.ascontiguousarray(img,dtype=np.uint8).tobytes())
        if si%20==0: print("seg",si,"/",len(segs),flush=True)
    enc.stdin.close(); enc.wait()
if __name__=="__main__":
    d=json.load(open(sys.argv[1]))
    render(d["segs"],d["flashes"],d["total"],sys.argv[2])
