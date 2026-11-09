# ---- rhythmic timeline from slot 80 (13.72s) to 407 (66.84s) on a 16th grid ----
G0=0.7198; S16=0.16254
def slot_t(k): return G0+k*S16
LINES={
 "tomo1":[(14.68,15.12),(15.12,15.86),(15.86,16.22),(16.22,16.96),(16.96,17.24)],
 "tomo2":[(17.88,18.82),(18.82,19.32),(19.32,20.36)],
 "tomo3":[(20.36,21.72),(21.72,22.26),(22.26,23.12),(23.12,23.40)],
 "omae":[(104.98,105.46),(105.46,106.12),(106.12,106.54),(106.54,106.96),(106.96,107.50)],
 "itsumo":[(108.06,108.60),(108.60,108.82),(108.82,109.06)],
 "game":[(164.42,164.92),(164.92,165.28),(165.28,165.86),(165.86,166.12),(166.12,166.26),(166.26,166.60)],
 "iuna":[(777.36,778.40),(778.40,778.84),(779.34,779.84),(779.84,780.40)],
 "hisa":[(266.11,266.61),(266.61,266.85),(266.85,267.25),(267.25,267.80)],
 "kami":[(475.30,476.20),(476.20,476.98),(476.98,477.14),(477.28,477.88)],
 "shiawase":[(813.92,814.66),(814.66,815.10),(815.10,815.60)],
 "zutto":[(796.55,797.10),(797.10,797.80)],
 "nani":[(249.79,251.05),(251.05,251.40),(252.23,252.67),(252.67,253.10)],
}
# which clips have a usable vocal stem (all above are inside separated regions)
def chunk_audio(s,e,L=None):
    st=s
    a=raw(s,0.15,True); fr=441;n=len(a)//fr
    if n>2:
        r=np.sqrt((a[:n*fr].reshape(n,fr)**2).mean(1)); i=int(np.argmax(r>max(r.max()*0.3,0.01))); st=s+max(0,i-1)*0.01
    L=(e-st) if L is None else min(L,e-st)
    return st,env(norm(raw(st,max(L,0.05),True)),3,15)
def seg(t,src,fx): segs.append({"t":round(t,4),"src":src,"fx":fx})
def line(k,name,stutter=0,echo=0,maxslots=None):
    ch=LINES[name]; n=len(ch)
    for j in range(stutter):           # ま・ま・まだ…
        st,y=chunk_audio(*ch[0],L=S16-0.012); place(slot_t(k),y); seg(slot_t(k),st,["facepunch"] if j==0 else ["facebig"]); k+=1
    for j,(s,e) in enumerate(ch):
        ln=max(1,int(np.ceil((e-s-0.04)/S16)))
        if maxslots: ln=min(ln,maxslots)
        st,y=chunk_audio(s,e,L=ln*S16-0.012); place(slot_t(k),y)
        seg(slot_t(k),st,["facepunch"] if j==0 else (["facebig"] if j==n-1 else (["face"] if j%2 else ["zoom"])))
        k+=ln
    for j in range(echo):              # いい・いい・いい
        s,e=ch[-1]; st,y=chunk_audio(s,e,L=2*S16-0.012); place(slot_t(k),y,0.9-0.15*j)
        seg(slot_t(k),st,["facebig","shake"]); k+=2
    return k
def jk(k,pat="jan:0 ken:2 pon:4 pon2:6 pon2:7"):
    last=0
    for item in pat.split():
        nm,o=item.split(":"); o=int(o)
        st,y=clip(nm,S16*2-0.012 if nm in("jan","ken") else S16-0.012); place(slot_t(k+o),y)
        seg(slot_t(k+o),st,fxfor(nm,"punch" if o==0 else ("big" if nm.startswith("pon") else "n"))+(["shake"] if o>=6 else []))
        last=max(last,o)
    return k+last+1
def full(k,nm,slots,style="punch"):
    st,y=clip(nm,slots*S16-0.012); place(slot_t(k),y)
    segs.append({"t":round(slot_t(k),4),"src":st,"fx":fxfor(nm,style)+(["shake"] if "scream" in nm else [])}); return k+slots
def rep(k,nm,n,every=2):
    for j in range(n):
        st,y=clip(nm,every*S16-0.012); place(slot_t(k),y); segs.append({"t":round(slot_t(k),4),"src":st,"fx":fxfor(nm,"big" if j%2 else "punch")}); k+=every
    return k
def al(k,m=4): return -(-k//m)*m
def flash(k,a=0.3): flashes.append((slot_t(k),a))
k=80
TL=[
 ("line","tomo1",2,0),("jk","pon2:0 pon2:2"),
 ("line","tomo2",0,0),("line","tomo3",0,2),("full","scream2",12),
 # ---- B1 (bass) ----
 ("jk","jan:0 ken:2 pon:4 pon2:6 pon2:7"),("line","omae",0,0),("line","itsumo",0,2),("full","scream1",10),
 ("line","iuna",0,0),("rep","ban",2,4),("line","game",0,1),("full","uoho",10),
 ("jk","jan:0 ken:2 pon:4 pon2:5 pon2:6 pon2:7"),
 # ---- B2 ----
 ("line","hisa",0,0),("line","kami",0,1),("rep","ban",2,4),("line","shiawase",3,0),("jk","jan:0 ken:2 pon:4 pon2:6 pon2:7"),
 ("line","zutto",0,0),("line","zutto",0,0),("line","nani",0,1),("full","eee",12),
 ("full","scream2","FILL"),
]
for ev in TL:
    flash(k)
    if ev[0]=="line": k=line(k,ev[1],ev[2],ev[3])
    elif ev[0]=="jk": k=jk(k,ev[1])
    elif ev[0]=="full":
        sl=ev[2] if ev[2]!="FILL" else max(4,407-k)
        k=full(k,ev[1],sl)
    elif ev[0]=="rep": k=rep(k,ev[1],ev[2],ev[3])
    k=al(k)
    print(f"{ev[0]:5s} {ev[1]:10s} -> slot {k} t={slot_t(k):.2f}")
