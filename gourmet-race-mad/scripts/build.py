import sys;sys.path.insert(0,"scripts")
import json,numpy as np,soundfile as sf,random
from tune import tune
from samples import S
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
# ---------- helper for melodic sections ----------
def melodic(sec,plan,bar0,shift,fxcycle,gain=1.0,bl=1.3004):
    notes=[n for n in score if n[4]==sec]
    bars={}
    for n in notes: bars.setdefault(bar_of(n[0],bar0,bl),[]).append(n)
    for b,ns in sorted(bars.items()):
        name,mode=plan[b%len(plan)] if isinstance(plan,list) else plan(b)
        k=len(ns)
        for i,n in enumerate(ns):
            s,e,p,a,_,nxt=n
            dur=min(nxt-s,0.9); dur=max(dur,0.09)
            Ls=S[name][1]
            if mode=="syl":
                off=Ls*i/k; L=max(Ls/k,0.12)
            else:
                off=0.0; L=Ls
            x=get(name,off,min(L,Ls-off) if mode=="syl" else L)
            y=tune(x,p+shift,dur*0.97 if mode!="syl" else dur*0.97,stretch_max=3)
            place(s,y,gain)
            fx=list(fxcycle[(b*7+i)%len(fxcycle)])
            if i==0: fx=fx+["zoom"]
            vseg(s,name,off=off,fx=fx)
        flashes.append((bar0+b*bl,0.35))
# ---------- A section ----------
A_plan=[("sugoi","rep"),("sugoi","rep"),("nanikore","rep"),("nanikore","rep"),
        ("shiawase","syl"),("hisashiburi","syl"),("kimoi","syl"),("soccer","syl"),
        ("seeno","rep"),("seeno","rep"),("ore","rep"),("ore","rep"),
        ("lara","syl"),("jessie","syl"),("iuna","syl"),("kimoi","syl")]
melodic("A",A_plan,3.32,-12,[[],["flip"],["rgb"],[],["shake"],["flip"],[] ,["mirror"]])
# ---------- B1 bass ----------
B1_plan=[("ban","rep"),("ban","rep"),("baa","rep"),("chigau","rep"),("ore","rep"),("ikeru","rep"),("ban","rep"),("hai","rep"),
         ("ban","rep"),("baa","rep"),("chigau","rep"),("ikeru","rep"),("imada","rep"),("sugoi","rep"),("agatta","rep"),("seeno","rep"),("ban","rep")]
melodic("B1",B1_plan,23.44,+24,[["tile2"],["invert"],["flip","tile3"],["hue"],["mirror"],["shake","rgb"],["tile2","flip"],["gray"],["squash"],["rot"]],gain=1.0)
# ---------- B2 ----------
B2_plan=[("yesorno","syl"),("shiawase","syl"),("paa","syl"),("kimoi","syl"),("soccer","syl"),("giyutte","syl"),("lara","syl"),("nanzo","syl"),
         ("nanikore2","syl"),("yokatta","syl"),("sugoi3","rep"),("jessie","syl"),("hisashiburi","syl"),("yappa","syl"),("mou_owaru","syl"),("oi","syl"),("ore","rep"),("seeno","rep")]
melodic("B2",B2_plan,44.24,-12,[[],["flip"],["tile2"],["rgb"],[],["mirror"],["zoomin"],["hue"]])
# ---------- build-up 66.84 -> 68.18 ----------
t=66.84; i=0; step=0.16254
while t<68.1:
    y=tune(get("ore"),67+i,0.15); place(t,y,0.9)
    vseg(t,"ore",fx=["zoom","tile2" if i%2 else "flip"] if i<5 else ["shake","tile3" if i%2 else "invert"])
    t+=step; i+=1
# ---------- punchline ----------
y=get("warai",clean=False,L=1.4); place(68.18,y,1.3)
vseg(68.18,"warai",fx=["zoom"])
flashes.append((68.18,1.0))
vseg(69.5,"warai",off=1.2,fx=["freeze","gray"],text="おしまい",ts={"pos":"center","size":150,"color":"#ff4d6d","pop":True})
# ---------- mix ----------
pk=np.max(np.abs(vox)); 
vox=np.tanh(vox*1.2)*0.8
mix+=vox[:,None]
mix=np.tanh(mix*1.1)/np.tanh(1.1)*0.92
sf.write("work/out_audio.wav",mix,SR); sf.write("work/vox.wav",vox,SR)
json.dump({"segs":segs,"flashes":flashes,"total":TOTAL},open("work/segs.json","w"),ensure_ascii=False)
print("segs",len(segs))
