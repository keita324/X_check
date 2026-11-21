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
MAJ=(0.69,0.58,2.4)
LN={ # name: (file, clean, zoom, [(start,end,text),...])
 "ikimasu":("src",0,(0.27,0.42,1.7),[(132.50,133.10,"じゃあ"),(133.26,133.52,"行き"),(133.52,133.72,"ます")]),
 "egui":("n3",1,None,[(1804.04,1804.34,"え"),(1804.34,1804.60,"ぐい"),(1804.60,1804.80,"ぞ")]),
 "fukushu":("n3",1,None,[(1808.48,1808.84,"見"),(1808.84,1809.18,"たよね"),(1809.18,1809.70,"復習"),(1809.70,1810.00,"して"),(1810.68,1811.10,"きたから")]),
 "remy":("n3",1,None,[(1813.48,1813.90,"レミー"),(1813.90,1814.36,"の物語"),(1814.36,1814.64,"見て"),(1814.64,1815.00,"たから"),(1815.00,1815.60,"楽しみ")]),
 "gusto":("n3",1,None,[(1815.68,1816.00,"あ!"),(1816.04,1816.40,"グストー"),(1816.40,1816.70,"がいる!")]),
 "majika":("n3",1,MAJ,[(2087.36,2088.00,"マジ"),(2088.38,2088.74,"か"),(2088.74,2089.38,"マジ"),(2089.38,2089.95,"か!")]),
 "souiu":("n3",1,MAJ,[(2092.56,2092.98,"え"),(2092.98,2093.28,"そう"),(2093.28,2093.70,"いうこと"),(2093.70,2094.28,"あるの?")]),
 "yume":("n3",1,MAJ,[(2094.38,2094.72,"いやや"),(2094.72,2095.04,"ばい"),(2095.04,2095.34,"なんか"),(2095.34,2095.64,"夢"),(2095.64,2096.36,"みたいだった")]),
 "mix":("n3",1,(0.33,0.28,1.9),[(1650.98,1651.64,"ミックスを"),(1651.64,1652.04,"頑張って"),(1652.04,1652.24,"いき"),(1652.24,1652.62,"たいと思います")]),
}
from audiotsm import wsola
from audiotsm.io.array import ArrayReader,ArrayWriter
def fit(a,target,cap=1.7):
    n=int(target*SR)
    if len(a)<=n: return a,1.0
    rate=min(len(a)/n,cap)
    r=ArrayReader(a[None,:].astype(np.float32)); w=ArrayWriter(1); wsola(1,speed=rate,frame_length=1024,synthesis_hop=256).run(r,w)
    return w.data[0][:n],rate
def word(t,line,j,gap,first,rest=False):
    f,c,z,ws=LN[line]; st,en,_=ws[min(j,len(ws)-1)]
    if rest and j<len(ws)-1: en=ws[-1][1]          # last note of the bar: say the rest of the line
    a=rawf(f,st,en-st,c); y,rate=fit(a,max(gap-0.012,0.08),2.0 if rest else 1.7)
    place(t,env(norm(y),3,12))
    fx=(["face"] if z is None else [f"zc:{z[0]}:{z[1]}:{z[2]}:{'p2' if first else 'fix'}"])
    d={"t":round(t,4),"src":st,"file":f,"fx":fx}
    if rate>1.02: d["spd"]=round(rate,3)
    segs.append(d)
def MEL2(sec,plan,bar0,t0,t1):
    notes=[n for n in score if n[4]==sec and t0-0.02<=n[0]<t1-0.02]
    bars={}
    for n in notes: bars.setdefault(int((n[0]-bar0+0.05)//BL),[]).append(n)
    for b,ns in sorted(bars.items()):
        kind,nm=plan[b]
        flashes.append((ns[0][0],0.12))
        for i,n in enumerate(ns):
            s_=n[0]; nxt=min(n[5],t1); gap=nxt-s_; last=(i==len(ns)-1)
            if last: gap=min(bar0+(b+1)*BL,t1)-s_       # last note of the bar may ring to the bar end
            if kind=="L": word(s_,nm,i,gap,i==0,rest=last); continue
            if kind=="F":
                if i>0: continue
                H2(s_,nm,min(bar0+(b+1)*BL,t1)-s_+0.01,"punch"); continue
            H2(s_,nm,(X[nm][2]) if last else gap-0.012,"punch" if i==0 else "n")    # R: restart chop

from audiotsm import wsola as _w
from audiotsm.io.array import ArrayReader as _R,ArrayWriter as _W
def stretch(a,target):
    n=int(target*SR); rate=len(a)/n
    r=_R(a[None,:].astype(np.float32)); w=_W(1); _w(1,speed=rate,frame_length=1024,synthesis_hop=256).run(r,w)
    y=w.data[0][:n]; return np.pad(y,(0,max(0,n-len(y))))
GYU=3.74                         # 「ミルクです、ギュー!」の「ギュー」(n2)
def gyu(t,dur,zz):
    a=rawf("n2",GYU,0.58,1); y,rate=fit(a,max(dur,0.1),2.2)     # say the whole 「ギュー」 inside the note
    place(t,env(norm(y),3,12))
    segs.append({"t":round(t,4),"src":GYU,"file":"n2","spd":round(rate,3),"fx":[f"zc:0.50:0.40:{zz}:fix"]})
    tv=(4.38-GYU)/rate                                   # source cuts to the pool at ~4.45
    if dur>tv: segs.append({"t":round(t+tv,4),"src":4.36,"file":"n2","fx":["freeze",f"zc:0.50:0.40:{zz}:fix"]})
# ---- 16.3-18.9: ギュー x7 on the melody notes ----
mn=[n for n in score if n[4]=="A" and slot_t(96)-0.03<=n[0]<18.85]
for i,n in enumerate(mn[:7]):
    nxt=mn[i+1][0] if (i+1<len(mn) and i<6) else 18.89
    gyu(n[0],nxt-n[0]-0.012,1.5 if i%2==0 else 1.8)
    if i%4==0: flashes.append((n[0],0.12))
# ---- 18.9-21.2: bucket dive unfolds note by note ----
notes=[n for n in score if n[4]=="A" and 18.85<=n[0]<21.15]
BK0,BK1=1.20,2.60
seq=np.linspace(BK0,BK1,len(notes)+1)
for i,n in enumerate(notes):
    t=n[0]; g=(notes[i+1][0] if i+1<len(notes) else 21.21)-t
    st=float(seq[i]) if i<len(notes)-3 else 1.50
    place(t,env(norm(rawf("n1",st,max(g-0.012,0.08),0)),3,10))
    segs.append({"t":round(t,4),"src":st,"file":"n1","fx":[]})
    if i%4==0: flashes.append((t,0.12))
# ---- 21.2: ノブ「素晴らしい!!」 ----
t=21.21; place(t,env(norm(rawf("n1",7.92,1.35,0)),3,40))
segs.append({"t":t,"src":7.92,"file":"n1","fx":[]}); flashes.append((t,0.2))
# ---- 22.5: 叫び一発 (12秒で使っている車内の叫び) ----
t=22.50; place(t,env(norm(rawf("src",111.22,1.20,0)),3,40)); segs.append({"t":t,"src":111.22,"file":"src","fx":["face"]}); flashes.append((t,0.2))
# ---- 23.74-26.0: うーわ最悪もーう → すぐ切る ----
t=23.74; place(t,env(norm(rawf("n2",77.50,2.26,1)),3,30)); segs.append({"t":t,"src":77.50,"file":"n2","fx":["zc:0.74:0.60:2.0:p2"]}); flashes.append((t,0.15))
X.update({"sc2b":("src",134.83,0.9,(0.27,0.42,1.7),0,None),"maji2":("n3",2088.74,1.0,MAJ,1,2089.45),
          "uwa2":("n2",76.66,0.9,(0.74,0.60,2.0),1,None),"sofa2":("n2",69.80,0.9,(0.74,0.60,2.0),1,None),
          "ah":("n3",2084.0,0.5,MAJ,1,None),"uoho2":("src",3.98,0.9,LEFT,1,None),"laugh2":("src",137.9,0.9,(0.27,0.45,1.8),0,None)})
# 26.0-27.3: 車内の叫び4連発 (v16)
for i,n in enumerate([n for n in score if n[4]=="B1" and 26.0<=n[0]<27.25]):
    nx=[m for m in score if m[4]=="B1" and m[0]>n[0]+0.05][0][0]
    H2(n[0],"sc2b",min(nx,27.30)-n[0]-0.012,"punch" if i==0 else "n")
flashes.append((26.02,0.12))
# 27.3-30.2: v15 の腕ぶんぶん2つ (いやーやばい…夢みたいだった / ミックスを頑張っていきたいと思います)
MEL2("B1",{3:("L","yume"),4:("L","mix")},23.44,27.25,30.20)
# 30.2-32.5: ベースの音ごとに叫び (2回ずつ)
CYC=["yosshaF","yosshaF","maji2","maji2","uoho2","uoho2","laugh2","laugh2"]
bn=[n for n in score if n[4]=="B1" and 30.15<=n[0]<32.50]
for i,n in enumerate(bn):
    t=n[0]; nxt=bn[i+1][0] if i+1<len(bn) else 32.58
    H2(t,CYC[i%len(CYC)],nxt-t-0.012,"punch" if i%2==0 else "n")
    if i%4==0: flashes.append((t,0.12))
# last bar (32.54-33.86): 8 x 16th, all different screams
mix=["sc2b","yosshaF","maji2","uwa2","uoho2","laugh2","sofa2","ah"]
t0=slot_t(196)
for j in range(8):
    H2(slot_t(196+j),mix[j],S16-0.012,"punch")
flashes.append((t0,0.15))
k=204
END_T=slot_t(k)
# ---------- END: bucket dive + scream, freeze on the dive ----------
X["kouiu2"]=("n2",106.50,1.10,(0.5,0.5,1.0),0,None)
f_,s0,L0,z0,c0,v0=X["kouiu2"]; place(END_T,env(norm(rawf(f_,s0,L0,c0)),3,80),1.15)
segs.append({"t":round(END_T,4),"src":s0,"file":f_,"fx":["zc:0.5:0.5:1.0:p2"]}); flashes.append((END_T,0.3))
segs.append({"t":round(END_T+0.78,4),"src":107.28,"file":f_,"fx":["freeze","zc:0.5:0.5:1.0:fix"]})
