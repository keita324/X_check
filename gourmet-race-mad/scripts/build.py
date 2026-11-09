import sys;sys.path.insert(0,"scripts")
import json,numpy as np,soundfile as sf,random
from tune import tune
from samples import S,SYL
SR=44100
rng=random.Random(3)
idx=json.load(open("work/cand_idx.json"))
voc,_=sf.read("work/sep/htdemucs/cand/vocals.wav"); voc=voc.mean(1)
orig,_=sf.read("work/src/a44.wav")
def get(name,off=0.0,L=None,clean=True):
    s,Ls=S[name]; L=Ls if L is None else L; s=s+off
    if clean:
        for k,(p,s0,Lr) in idx.items():
            if s0<=s and s+L<=s0+Lr+1e-6:
                a=int((p+s-s0)*SR); return voc[a:a+int(L*SR)].copy()
    return orig[int(s*SR):int((s+L)*SR)].copy()
score=json.load(open("work/music/score.json"))   # [s,e,p,a,sec,next]
music,_=sf.read("work/music/m.wav")
TOTAL=70.6
mix=np.zeros((int(TOTAL*SR),2))
END_MUSIC=68.45
mus=music[:int(END_MUSIC*SR)].copy()*0.55
fl=int(0.25*SR); mus[-fl:]*=np.linspace(1,0,fl)[:,None]
mix[:len(mus)]+=mus
vox=np.zeros(len(mix))
segs=[];flashes=[]
def place(t,y,g=1.0):
    a=int(t*SR); b=min(len(vox),a+len(y)); vox[a:b]+=y[:b-a]*g
def vseg(t,name,off=0.0,fx=(),text="",ts=None,black=False):
    d={"t":round(t,4),"src":S[name][0]+off if name else 0,"fx":list(fx),"text":text,"ts":ts or {}}
    if black: d["black"]=True
    segs.append(d)
def bar_of(t,start,bl=1.3004): return int((t-start+0.05)//bl)
# ---------- INTRO ----------
vseg(0.0,None,black=True,text="M!LK × グルメレース",ts={"pos":"center","size":90,"color":"#ffe14d"})
y=get("lara"); place(0.72,y,0.9)
vseg(0.72,"lara",fx=["zoom"])
vseg(1.71,"lara",off=0.99,fx=["zoom","flip"])
vseg(2.70,"lara",off=1.98,fx=["zoom","rgb"])
flashes+= [(0.72,0.8),(1.71,0.5)]
# ---------- helper: per-bar spec (name, mode, restart) ----------
ctr={}
def melodic(sec,plan,bar0,shift,fxfn,gain=1.0,bl=1.3004):
    notes=[n for n in score if n[4]==sec]
    bars={}
    for n in notes: bars.setdefault(bar_of(n[0],bar0,bl),[]).append(n)
    for b,ns in sorted(bars.items()):
        name,mode,restart=plan[b%len(plan)]
        if restart: ctr[name]=0
        for i,n in enumerate(ns):
            s_,e,p,a,_,nxt=n
            dur=max(min(nxt-s_,0.9),0.09)
            if mode=="line":
                bd=SYL[name]; j=ctr.get(name,0)%(len(bd)-1); ctr[name]=ctr.get(name,0)+1
                off=bd[j]-S[name][0]; L=max(bd[j+1]-bd[j],0.1)
                # last syllable of a line may sustain
            else:
                off=0.0; L=S[name][1]
            x=get(name,off,L)
            y=tune(x,p+shift,dur*0.97,stretch_max=4)
            place(s_,y,gain)
            vseg(s_,name,off=off,fx=fxfn(b,i))
        flashes.append((bar0+b*bl,0.3))
SH=("shiawase","line",False); SHr=("shiawase","line",True); KI=("kimoi","line",True); KIc=("kimoi","line",False)
# ---------- A section: 幸せって2種類あんねん x many, answered by キモいです ----------
A_plan=[SHr,SH,SH,SH,SHr,SH,KI,KIc, SHr,SH,SH,SH,SHr,SH,KI,KIc]
def fxA(b,i): return ["zoom"] if i==0 else (["flip"] if (b%4==3 and i%2) else [])
melodic("A",A_plan,3.32,-12,fxA)
# ---------- B1 bass: 俺 俺 俺 ... ----------
OR=("ore","rep",False); SE=("seeno","line",True)
B1_plan=[OR,OR,OR,SE,OR,OR,OR,SE,OR,OR,OR,SE,OR,OR,OR,SE,OR]
def fxB1(b,i):
    if i==0: return ["zoom"]
    return [[],["flip"],[],["tile2"]][(b+i)%4] if b>=8 else ([] if i%2==0 else ["flip"])
melodic("B1",B1_plan,23.44,+24,fxB1)
# ---------- B2: キモいです x many, then 幸せって ----------
NK=("nanikore","rep",False)
B2_plan=[KI,KIc,KI,KIc,KI,KIc,NK,NK, KI,KIc,KI,KIc,SHr,SH,SH,SH,KI,KIc]
def fxB2(b,i): return ["zoom"] if i==0 else ([] if b<8 else (["flip"] if i%2 else []))
melodic("B2",B2_plan,44.24,-12,fxB2)
# ---------- build-up 66.84 -> 68.18 ----------
t=66.84; i=0; step=0.16254
while t<68.1:
    y=tune(get("ore"),67+i,0.15); place(t,y,0.9)
    vseg(t,"ore",fx=["zoom"] if i<5 else ["zoom","shake"])
    t+=step; i+=1
# ---------- punchline ----------
y=get("warai",clean=False,L=1.4); place(68.18,y,1.3)
vseg(68.18,"warai",fx=["zoom"])
flashes.append((68.18,1.0))
vseg(69.5,"warai",off=1.2,fx=["freeze","gray"])
# ---------- mix ----------
pk=np.max(np.abs(vox)); 
vox=np.tanh(vox*1.2)*0.8
mix+=vox[:,None]
mix=np.tanh(mix*1.1)/np.tanh(1.1)*0.92
sf.write("work/out_audio.wav",mix,SR); sf.write("work/vox.wav",vox,SR)
json.dump({"segs":segs,"flashes":flashes,"total":TOTAL},open("work/segs.json","w"),ensure_ascii=False)
print("segs",len(segs))
