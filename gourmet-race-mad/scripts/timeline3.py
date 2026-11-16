# ---- v8: Shiozaki-only, screams / onomatopoeia on a 16th grid ----
G0=0.7198; S16=0.16254
def slot_t(k): return G0+k*S16
PATHS={"src":("work/src/a44.wav",None),"n1":("work/n/n1.wav","work/sep/htdemucs/n1/vocals.wav"),
       "n2":("work/n/n2.wav","work/sep/htdemucs/n2/vocals.wav"),"n3":("work/n/n3.wav","work/sep/htdemucs/n3c/vocals.wav")}
def rawf(file,s,L,clean):
    if file=="src": return raw(s,L,clean)
    p=PATHS[file][1 if clean else 0]
    a,_=sf.read(p,start=int(s*SR),stop=int((s+L)*SR))
    return (a if a.ndim==1 else a.mean(1)).copy()
LEFT=(0.22,0.36,2.0)
# name:(file,start,len,zoom(x,y,z)|None,clean,video_start|None)
X={
 "jan":("src",2.03,0.24,LEFT,1,None),"ken":("src",2.36,0.22,LEFT,1,None),"pon":("src",2.60,0.15,LEFT,1,None),"pon2":("src",2.87,0.2,LEFT,1,None),
 "uoho":("src",3.98,1.67,LEFT,1,None),"saisho":("src",1.31,0.64,LEFT,1,None),
 "scream1":("src",111.22,1.75,None,0,None),"scream2":("src",134.83,3.15,(0.27,0.42,1.7),0,None),
 "kouiu":("n2",106.58,0.72,None,1,None),
 "waa":("n3",1259.06,1.55,(0.62,0.45,1.3),1,1260.0),"tension":("n3",1651.30,2.30,(0.33,0.28,1.9),1,None),
 "ai":("n3",1339.98,0.85,(0.70,0.42,1.7),1,None),"kyaa":("n3",1341.85,1.55,(0.70,0.42,1.7),1,None),
 "sing":("n2",2.30,0.95,(0.50,0.38,1.8),1,None),"sing2":("n2",3.76,0.90,(0.50,0.38,1.8),1,None),
 "yosshi":("n2",14.17,0.80,(0.60,0.60,1.5),1,None),
 "iku1":("n2",19.93,0.20,None,1,21.45),"iku2":("n2",20.28,0.20,None,1,21.60),"iku3":("n2",20.68,0.17,None,1,21.75),
 "sofa":("n2",69.80,1.75,(0.74,0.60,2.0),1,None),"haa":("n2",74.15,0.95,(0.74,0.60,2.0),1,None),
 "uwa":("n2",76.66,0.60,(0.74,0.60,2.0),1,None),"saiaku":("n2",77.50,2.2,(0.74,0.60,2.0),1,None),
 "kyaa2":("n2",109.88,1.0,(0.42,0.32,1.7),1,None),
 "bucket":("n1",1.18,1.30,None,0,None),
}
_tc={}
def tightx(nm):
    if nm in _tc: return _tc[nm]
    f,s,L,z,c,vs=X[nm]; a=rawf(f,s,min(L,0.4),c); fr=441;n=len(a)//fr
    r=np.sqrt((a[:n*fr].reshape(n,fr)**2).mean(1)); i=int(np.argmax(r>r.max()*0.25)); i=min(i,12)
    _tc[nm]=max(0,i-1)*0.01; return _tc[nm]
def zfx(nm,style):
    z=X[nm][3]
    if z is None:
        if nm=="bucket": return ["zoom"] if style=="punch" else []
        return [{"n":"face","big":"facebig","punch":"facepunch"}[style]]
    x,y,zz=z; zz=zz*{"n":0.8,"big":1.25,"punch":1.0}[style]
    return [f"zc:{x}:{y}:{zz}:{'punch' if style=='punch' else 'fix'}"]
def H(k,nm,slots,style="n",off=0.0,spd=1.0,g=1.0):
    """place sample nm at slot k for `slots` 16ths (cut to fit)."""
    f,s,L,z,c,vs=X[nm]; d=tightx(nm)+off; dur=min(slots*S16-0.012,(L-d)/spd if spd!=1 else L-d)
    a=rawf(f,s+d,max(dur*spd,0.05),c)
    if spd!=1.0:
        from audiotsm import wsola
        from audiotsm.io.array import ArrayReader,ArrayWriter
        r=ArrayReader(a[None,:].astype(np.float32)); w=ArrayWriter(1); wsola(1,speed=spd,frame_length=1024,synthesis_hop=256).run(r,w); a=w.data[0]
    place(slot_t(k),env(norm(a),3,14),g)
    d_={"t":round(slot_t(k),4),"src":(vs if vs is not None else s+d),"file":f,"fx":zfx(nm,style)}
    if spd!=1.0: d_["spd"]=spd
    segs.append(d_)
    vis=(L-d)/spd-0.06            # video would run past the sample: hold the last frame
    if vs is None and slots*S16>vis+0.1:
        segs.append({"t":round(slot_t(k)+vis,4),"src":s+L-0.08,"file":f,"fx":["freeze"]+[x.replace(":punch",":fix") for x in d_["fx"]]})
# ---------- bar patterns (8 slots each) ----------
def P_jk(k):
    H(k,"jan",2,"punch");H(k+2,"ken",2);H(k+4,"pon",2,"punch");H(k+6,"pon2",1,"big");H(k+7,"pon2",1,"big")
def P_jk2(k):
    H(k,"jan",2,"punch");H(k+2,"ken",2);[H(k+4+i,"pon2",1,"big" if i%2 else "punch") for i in range(4)]
def P_iku(k):
    for i,(o,nm) in enumerate([(0,"iku1"),(2,"iku2"),(4,"iku3"),(5,"iku1"),(6,"iku2"),(7,"iku3")]): H(k+o,nm,1 if o>=4 else 2,"punch" if i%2==0 else "big")
def P_stut(k,nm):
    H(k,nm,1,"punch");H(k+1,nm,1,"n");H(k+2,nm,2,"big");H(k+4,nm,4,"punch")
def P_stut2(k,nm):   # syncopated 3-3-2
    H(k,nm,3,"punch");H(k+3,nm,3,"big");H(k+6,nm,1,"n");H(k+7,nm,1,"big")
def P_alt(k,a,b):
    H(k,a,2,"punch");H(k+2,b,2,"punch");H(k+4,a,1,"big");H(k+5,a,1,"n");H(k+6,b,2,"big")
def P_long(k,nm,n=8): H(k,nm,n,"punch")
def P_bucket(k): H(k,"bucket",8,"punch")
def P_bucket2(k): H(k,"bucket",4,"punch",spd=2.0);H(k+4,"bucket",4,"n",spd=2.0)
BARS=[
 ("stut","waa"),("iku",),("jk",),("long","kyaa2"),
 ("alt","sing","yosshi"),("stut2","uwa"),("jk2",),("bucket",),
 ("alt","pon2","ai"),("iku",),("stut","sofa"),("long","scream2"),
 ("jk",),("alt","uwa","haa"),("stut2","kyaa2"),("long","tension"),
 ("bucket2",),("iku",),("alt","sing2","ai"),("long","saiaku"),
 ("jk2",),("stut","waa"),("alt","yosshi","uwa"),("long","scream1"),
 ("stut2","tension"),("iku",),("jk",),("long","uoho"),
 ("alt","kyaa2","pon2"),("stut","sing"),("bucket2",),("long","kyaa"),
 ("jk2",),("iku",),("stut","sofa"),("long","waa"),
 ("alt","ai","uwa"),("stut2","kyaa2"),("jk",),("long","scream2"),
 ("long","kouiu"),
]
k=80
for b in BARS:
    flashes.append((slot_t(k),0.25))
    {"stut":P_stut,"stut2":P_stut2,"alt":P_alt,"long":P_long,"jk":P_jk,"jk2":P_jk2,"iku":P_iku,"bucket":P_bucket,"bucket2":P_bucket2}[b[0]](k,*b[1:])
    k+=8
print("end slot",k,slot_t(k))
# ---------- build-up: ぽん 16ths, zoom growing ----------
t=66.84;i=0
while t<68.1:
    H((t-G0)/S16,"pon2",1,"n"); segs[-1]["fx"]=[f"zc:{LEFT[0]}:{LEFT[1]}:{min(1.6+0.15*i,3.0)}:fix"]
    t+=S16;i+=1
# ---------- END: bucket dive + scream, freeze on the dive ----------
kf=(68.18-G0)/S16
H(kf,"bucket",9,"punch",g=1.0)
f,s,L,z,c,vs=X["waa"]; place(68.18,env(norm(rawf(f,s+tightx("waa"),1.5,c)),3,60),0.9)
flashes.append((68.18,1.0))
segs.append({"t":round(68.18+1.28,4),"src":2.46,"file":"n1","fx":["freeze"]})
