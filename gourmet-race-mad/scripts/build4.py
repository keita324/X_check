import sys;sys.path.insert(0,"scripts")
import json,numpy as np,soundfile as sf
from tune import tune
from samples import S,SYL
SR=44100
idx=json.load(open("work/cand_idx.json"))
voc,_=sf.read("work/sep/htdemucs/cand/vocals.wav"); voc=voc.mean(1)
orig,_=sf.read("work/src/a44.wav")
CH={"janken":[2.03,2.30,2.60,2.75],"shiawase":[813.92,814.66,815.10,815.60],"kimoi":[792.62,793.04,793.40]}
RAWONLY=set()
def raw(s,L,clean=True):
    if clean and not any(a<=s<b for a,b in RAWONLY):
        for k,(p,s0,Lr) in idx.items():
            if s0<=s and s+L<=s0+Lr+1e-6:
                a=int((p+s-s0)*SR); return voc[a:a+int(L*SR)].copy()
    return orig[int(s*SR):int((s+L)*SR)].copy()
def tight(s,look=0.25):
    a=raw(s,look+0.3); fr=441; n=len(a)//fr
    r=np.sqrt((a[:n*fr].reshape(n,fr)**2).mean(1)); th=r.max()*0.25
    i=int(np.argmax(r>th)); i=min(i,int(look*100))
    return s+max(0,i-1)*0.01
def env(y,ms_in=4,ms_out=15):
    a=int(ms_in*SR/1000); b=min(int(ms_out*SR/1000),len(y)//3)
    y=y.copy()
    if a: y[:a]*=np.linspace(0,1,a)
    if b: y[-b:]*=np.linspace(1,0,b)
    return y
def norm(y,pk=0.9): return y/(np.max(np.abs(y))+1e-9)*pk
S.update({"seeno":(0.38,0.68),"saisho":(1.31,0.64),"jan":(2.03,0.24),"ken":(2.36,0.22),"pon":(2.60,0.15),"pon2":(2.87,0.2),
 "uoho":(3.98,1.67),"scream1":(111.22,1.75),"scream2":(134.83,3.15),"hahaha":(138.03,1.2)})
RAWONLY.update([(110,120),(132,145)])
JK=[("jan",0.24),("ken",0.22),("pon",0.15),("pon2",0.2),("pon2",0.2),("pon2",0.2),("pon2",0.2),("pon2",0.2)]
score=json.load(open("work/music/score.json"))
music,_=sf.read("work/music/m.wav")
TOTAL=70.2; END_MUSIC=68.40
vox=np.zeros(int(TOTAL*SR))
segs=[];flashes=[]
def place(t,y,g=1.0):
    a=int(t*SR); b=min(len(vox),a+len(y)); vox[a:b]+=y[:b-a]*g
def vseg(t,src,fx=(),black=False,text="",ts=None):
    d={"t":round(t,4),"src":src,"fx":list(fx),"text":text,"ts":ts or {}}
    if black: d["black"]=True
    segs.append(d)
BL=1.3004
SECEND={'A':23.44,'B1':44.82,'B2':66.84}
def bar_of(t,start): return int((t-start+0.05)//BL)
ctr={}
# kinds: ("P",name) pitched line | ("R",name) raw restart chop | ("Q",name) raw sequential chunks | ("F",name) full raw on first note, rest silent
def section(sec,plan,bar0,shift,fxfn):
    notes=[n for n in score if n[4]==sec]
    bars={}
    for n in notes: bars.setdefault(bar_of(n[0],bar0),[]).append(n)
    for b,ns in sorted(bars.items()):
        kind,name=plan[b%len(plan)]
        if kind=="J" and (b==0 or plan[(b-1)%len(plan)][0]!="J"): ctr["JK"]=0
        if kind in("P","Q") and (b==0 or plan[(b-1)%len(plan)]!=(kind,name)): ctr[name]=0
        for i,n in enumerate(ns):
            s_,e,p,a,_,nxt=n
            gap=nxt-s_
            if kind=="F" and i>0: continue
            if kind=="F":
                # play whole phrase until the end of the bar
                endbar=min(bar0+(b+1)*BL,SECEND.get(sec,999)); L=min(S[name][1],endbar-s_+0.02)
                st=tight(S[name][0]); y=env(norm(raw(st,L))); place(s_,y,1.0)
                vseg(s_,st,fxfn(b,i,kind,len(ns)))
                continue
            if kind=="J":
                j=ctr.setdefault("JK",0); ctr["JK"]+=1
                nm,Lj=JK[min(j,len(JK)-1)]; st=S[nm][0]
                g=min(Lj+0.05,gap-0.012) if i<len(ns)-1 else Lj+0.05
                y=env(norm(raw(st,max(g,0.06)))); place(s_,y,1.0); vseg(s_,st,fxfn(b,i,kind,len(ns))); continue
            if kind=="P":
                bd=SYL[name]; j=ctr[name]%(len(bd)-1); ctr[name]+=1
                st=bd[j]; L=max(bd[j+1]-bd[j],0.1)
                y=tune(raw(st,L),p+shift,max(min(gap,0.8),0.09)*0.97,stretch_max=4)
                place(s_,y,0.85); vseg(s_,st,fxfn(b,i,kind,len(ns))); continue
            if kind=="Q":
                bd=CH[name]; j=ctr[name]%(len(bd)-1); ctr[name]+=1
                st=tight(bd[j],0.12); L=bd[j+1]-st
            else:
                st=tight(S[name][0]); L=S[name][1]-(st-S[name][0])
            last=(i==len(ns)-1)
            g=min(L,gap-0.012) if not last else min(L,max(gap-0.012,0.12))
            y=env(norm(raw(st,max(g,0.06))))
            place(s_,y,1.0); vseg(s_,st,fxfn(b,i,kind,len(ns)))
        flashes.append((bar0+b*BL,0.28))
# ---------- INTRO: せーの / 最初はグー / じゃん けん ぽん ぽん ぽん ぽん ----------
vseg(0.0,0,black=True)
E8=0.32508; T=0.72
seq=[("saisho",0,2),("jan",2,1),("ken",3,1),("pon",4,1),("pon2",5,1),("pon2",6,1),("pon2",7,1)]
fxs=[["facepunch"],["zoom"],["zoom"],["facebig"],["face","shake"],["facebig","shake"],["facebig","shake","rgb"]]
for (nm,k,ln),fx in zip(seq,fxs):
    t=T+k*E8; st=S[nm][0]; L=min(S[nm][1]+0.04,ln*E8-0.012)
    place(t,env(norm(raw(st,L))),1.0); vseg(t,st,fx)
flashes+=[(0.72,0.8),(1.71,0.5)]
def fxA(b,i,kind,n):
    if kind=="P": return ["faceslow"]
    if kind=="F": return ["facepunch"]
    if i==n-1: return ["facebig"]
    return ["zoom"] if i%2==0 else ["face"]
A_plan=[("P","shiawase"),("P","shiawase"),("R","kimoi"),("R","kimoi"),("R","sugoi"),("R","nanikore"),("Q","shiawase"),("F","uoho"),
        ("R","ban"),("R","ban"),("R","chigau"),("R","nanikore"),("P","kimoi"),("P","kimoi"),("R","sugoi"),("F","scream2")]
section("A",A_plan,3.32,-12,fxA)
def fxB1(b,i,kind,n):
    name=B1_plan[b%len(B1_plan)][1]
    if kind=="F": return ["facepunch","shake"]
    if kind=="J": return [["zoom"],["zoom"],["facebig"],["face","shake"],["facebig","shake"],["face","shake"],["facebig","shake","rgb"],["facebig"]][min(i,7)]
    if b==11 and i>0: return ["tile2"]
    return [["zoom","shake"],["face"],["shake"],["facebig"]][i%4]
B1_plan=[("J","janken"),("J","janken"),("R","pon2"),("F","uoho"),("R","ban"),("R","chigau"),("R","seeno"),("F","scream1"),
         ("J","janken"),("J","janken"),("R","pon2"),("F","uoho"),("R","kimoi"),("R","chigau"),("R","seeno"),("F","scream1"),("R","ban")]
section("B1",B1_plan,23.44,0,fxB1)
def fxB2(b,i,kind,n):
    if kind=="P": return ["faceslow"]
    if kind=="F": return ["facepunch"]
    if i==n-1: return ["facebig"]
    return ["zoom"] if i%2==0 else ["face"]
B2_plan=[("Q","shiawase"),("Q","shiawase"),("R","kimoi"),("F","kimoi"),("P","shiawase"),("P","shiawase"),("R","ban"),("F","scream1"),
         ("R","sugoi"),("R","chigau"),("P","kimoi"),("P","kimoi"),("F","iuna"),("R","nanikore"),("R","pon2"),("F","scream2"),("Q","janken"),("Q","janken")]
section("B2",B2_plan,44.24,-12,fxB2)
# ---------- build-up: キ キ キ ... 16ths ----------
t=66.84;i=0;step=0.16254
st=tight(S["kimoi"][0])
while t<68.1:
    y=env(norm(raw(st,0.11))); place(t,y,0.9)
    vseg(t,st,["facepunch"] if i<3 else (["facebig","shake"] if i<6 else ["facebig","shake","rgb"]))
    t+=step;i+=1
# ---------- end: キモいです! ----------
place(68.18,env(norm(raw(st,0.85))),1.1)
vseg(68.18,st,["facepunch"]); flashes.append((68.18,1.0))
vseg(69.0,st+0.6,["freeze","facebig"])
# ---------- mix with ducking ----------
mus=music[:int(END_MUSIC*SR)].copy()*0.6
fl=int(0.2*SR); mus[-fl:]*=np.linspace(1,0,fl)[:,None]
mix=np.zeros((len(vox),2)); mix[:len(mus)]+=mus
e=np.abs(vox); k=int(0.03*SR)
e=np.convolve(e,np.ones(k)/k,mode="same"); e=np.clip(e/0.25,0,1)
mix*= (1-0.4*e)[:,None]
mix+=np.tanh(vox*1.1)[:,None]*0.85
mix=np.tanh(mix*1.05)/np.tanh(1.05)*0.9
sf.write("work/out_audio.wav",mix,SR); sf.write("work/vox.wav",vox,SR)
json.dump({"segs":segs,"flashes":flashes,"total":TOTAL},open("work/segs.json","w"),ensure_ascii=False)
print("segs",len(segs))
