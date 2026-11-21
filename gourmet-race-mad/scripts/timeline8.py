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
 "kouiu":("n2",106.58,0.72,(0.5,0.5,1.0),1,None),
 "waa":("n3",1259.06,1.55,(0.62,0.45,1.3),1,1260.0),"tension":("n3",1651.30,2.30,(0.33,0.28,1.9),1,None),
 "ai":("n3",1339.98,0.85,(0.70,0.42,1.7),1,None),"kyaa":("n3",1341.85,1.55,(0.70,0.42,1.7),1,None),
 "sing":("n2",2.30,0.95,(0.50,0.38,1.8),1,None),"sing2":("n2",3.76,0.90,(0.50,0.38,1.8),1,None),
 "yosshi":("n2",14.17,0.80,(0.60,0.60,1.5),1,None),
 "iku1":("n2",19.93,0.20,None,1,21.45),"iku2":("n2",20.28,0.20,None,1,21.60),"iku3":("n2",20.68,0.17,None,1,21.75),
 "sofa":("n2",69.80,1.75,(0.74,0.60,2.0),1,None),"haa":("n2",74.15,0.95,(0.74,0.60,2.0),1,None),
 "uwa":("n2",76.66,0.60,(0.74,0.60,2.0),1,None),"saiaku":("n2",77.50,2.2,(0.74,0.60,2.0),1,None),
 "kyaa2":("n2",109.88,1.0,(0.42,0.32,1.7),1,None),
 "bucket":("n1",1.18,1.30,None,0,None),
 "ban":("src",746.46,0.46,None,1,None),"ikimasu":("src",133.05,0.62,(0.27,0.42,1.7),0,None),
 "suki":("n3",553.62,2.40,(0.56,0.42,1.5),1,None),
 "milk":("n2",2.30,2.32,(0.50,0.40,1.5),1,None),"yosshaF":("n3",1644.85,1.95,(0.27,0.45,1.5),1,None),
 "majikaF":("n3",2089.30,1.70,(0.69,0.58,2.4),1,None),"tensionF":("n3",1651.30,2.32,(0.33,0.28,1.9),1,None),
 "fukuokaF":("n3",1665.20,3.25,(0.50,0.42,1.4),1,None),"saiakuF":("n2",76.66,2.65,(0.74,0.60,2.0),1,None),
 "yossha":("n3",1644.85,1.35,(0.27,0.45,1.5),1,None),"majika":("n3",2089.30,0.95,(0.69,0.58,2.4),1,None),
 "fukuoka":("n3",1665.20,1.45,(0.50,0.42,1.4),1,1665.8),"hey":("n3",1667.62,0.40,(0.50,0.42,1.4),1,None),
 "shout3":("n3",1663.28,0.62,(0.30,0.45,1.4),1,None),"batsu":("n2",114.70,0.70,None,1,114.35),
 "gusteau":("n3",1816.58,1.35,None,1,None),"bk":("n1",1.50,0.55,None,0,None),"bk2":("n1",2.05,0.45,None,0,None),
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
        if nm in ("bucket","bk","bk2"): return []
        return ["face"]
    x,y,zz=z
    return [f"zc:{x}:{y}:{zz}:{'p2' if style=='punch' else 'fix'}"]
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
def P_bk(k):   # bucket dive chopped on the beat
    H(k,"bk",2,"punch");H(k+2,"bk",2,"punch");H(k+4,"bk",1,"punch");H(k+5,"bk",1,"punch");H(k+6,"bk2",2,"punch")
def PH(k,nm,slots):
    """play the whole phrase from slot k; if it ends early, echo its last 0.25s on the 8ths."""
    f,s_,L,z,c,vs=X[nm]; d=tightx(nm); Lp=L-d
    used=min(slots,int(np.ceil((Lp+0.02)/S16)))
    H(k,nm,used,"punch")
    VMAX={"milk":4.42}                       # scene cut in the source right after this time
    if nm in VMAX:
        segs[:]=[x for x in segs if not (x["t"]>slot_t(k)+0.01 and x["t"]<slot_t(k+used)-0.01 and x.get("file")==f)]
        segs.append({"t":round(slot_t(k)+VMAX[nm]-(s_+d),4),"src":VMAX[nm]-0.04,"file":f,"fx":["freeze"]+zfx(nm,"n")})
    j=k+used; j+= (j-k)%2           # next 8th
    while j+2<=k+slots:
        st=s_+L-0.26
        a=rawf(f,st,0.25,c); place(slot_t(j),env(norm(a),3,20),0.8)
        segs.append({"t":round(slot_t(j),4),"src":st-0.15,"file":f,"fx":["freeze"]+zfx(nm,"n")}); j+=2
k=80
flashes.append((slot_t(k),0.12)); PH(k,"milk",16); k+=16

# ---- after 16.3s: voices on the actual MELODY / BASS note onsets (same method as the first 13s) ----
score=json.load(open("work/music/score.json"))
BL=1.3004
def H2(t,nm,dur,style="n",g=1.0):
    f,s_,L,z,c,vs=X[nm]; d=tightx(nm); dur=max(0.06,min(dur,L-d))
    place(t,env(norm(rawf(f,s_+d,dur,c)),3,12),g)
    segs.append({"t":round(t,4),"src":(vs if vs is not None else s_+d),"file":f,"fx":zfx(nm,style)})
def MEL(sec,plan,bar0,t0,t1):
    notes=[n for n in score if n[4]==sec and t0-0.02<=n[0]<t1-0.02]
    bars={}
    for n in notes: bars.setdefault(int((n[0]-bar0+0.05)//BL),[]).append(n)
    jk=0;prevJ=False
    for b,ns in sorted(bars.items()):
        kind,nm=plan[b%len(plan)]
        if kind=="J" and not prevJ: jk=0
        prevJ=(kind=="J")
        flashes.append((ns[0][0],0.12))
        for i,n in enumerate(ns):
            s_=n[0]; nxt=min(n[5],t1); gap=nxt-s_; last=(i==len(ns)-1)
            if kind=="F":
                if i>0: continue
                end=min(bar0+(b+1)*BL,t1); H2(s_,nm,end-s_+0.01,"punch"); continue
            if kind=="J":
                nm2=["jan","ken","pon","pon2","pon2","pon2","pon2","pon2"][min(jk,7)]; jk+=1
                H2(s_,nm2,(X[nm2][2]+0.05) if last else gap-0.012,"punch" if i==0 else "n"); continue
            H2(s_,nm,(X[nm][2]) if last else gap-0.012,"punch" if i==0 else "n")
T_MILK_END=slot_t(96)
# A-section remainder (16.3 -> 23.44): bars counted from 3.32
APLAN=[("R","pon2")]*10+[("R","ikimasu"),("J",""),("R","ban"),("F","yosshaF"),("J",""),("F","scream2")]
MEL("A",APLAN,
    3.32-0*BL, T_MILK_END, 23.44)
# bass break (23.44 -> 33.88): every bass note gets a voice
MEL("B1",[("J",""),("R","ban"),("R","ikimasu"),("F","majikaF"),("J",""),("R","pon2"),("R","ban"),("F","suki")],
    23.44, 23.44, 33.75)
k=204
END_T=slot_t(k)
# ---------- END: bucket dive + scream, freeze on the dive ----------
H(k,"bk",5,"punch",g=1.0)
f,s,L,z,c,vs=X["yosshaF"]; place(END_T,env(norm(rawf(f,s+tightx("yosshaF"),1.6,c)),3,80),0.85)
flashes.append((END_T,0.5))
segs.append({"t":round(END_T+5*S16,4),"src":2.30,"file":"n1","fx":["freeze","zoom"]})
