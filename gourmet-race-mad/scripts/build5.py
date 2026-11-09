import sys;sys.path.insert(0,"scripts")
import json,numpy as np,soundfile as sf
SR=44100
idx=json.load(open("work/cand_idx.json"))
voc,_=sf.read("work/sep/htdemucs/cand/vocals.wav"); voc=voc.mean(1)
orig,_=sf.read("work/src/a44.wav")
# name: (start,len,use_vocal_stem)
S={"seeno":(0.38,0.68,1),"saisho":(1.31,0.64,1),"jan":(2.03,0.24,1),"ken":(2.36,0.22,1),"pon":(2.60,0.15,1),"pon2":(2.87,0.2,1),
   "uoho":(3.98,1.67,1),"eee":(774.30,2.4,1),"scream1":(111.22,1.75,0),"scream2":(134.83,3.15,0),"ban":(746.46,0.46,1),"seeno_ban":(745.26,1.66,1)}
JKSEQ=["jan","ken","pon","pon2","pon2","pon2","pon2","pon2"]
# zoom targets per sample (x,y,zoom) ; None => face detect
LEFT=(0.22,0.36,2.0)
Z={"seeno":LEFT,"saisho":LEFT,"jan":LEFT,"ken":LEFT,"pon":LEFT,"pon2":LEFT,"uoho":LEFT,"scream2":(0.27,0.42,1.7)}
def raw(s,L,clean=True):
    if clean:
        for k,(p,s0,Lr) in idx.items():
            if s0<=s and s+L<=s0+Lr+1e-6:
                a=int((p+s-s0)*SR); return voc[a:a+int(L*SR)].copy()
    return orig[int(s*SR):int((s+L)*SR)].copy()
def tight(nm):
    s,L,c=S[nm]; a=raw(s,min(L,0.5),c); fr=441; n=len(a)//fr
    r=np.sqrt((a[:n*fr].reshape(n,fr)**2).mean(1)); i=int(np.argmax(r>r.max()*0.25)); i=min(i,15)
    return s+max(0,i-1)*0.01
def env(y,a_ms=4,b_ms=18):
    a=int(a_ms*SR/1000); b=min(int(b_ms*SR/1000),len(y)//3); y=y.copy()
    if a: y[:a]*=np.linspace(0,1,a)
    if b: y[-b:]*=np.linspace(1,0,b)
    return y
def norm(y,pk=0.9): return y/(np.max(np.abs(y))+1e-9)*pk
def clip(nm,L=None):
    s,Ls,c=S[nm]; st=tight(nm); L=(Ls-(st-s)) if L is None else min(L,Ls-(st-s))
    return st,env(norm(raw(st,max(L,0.05),c)))
score=json.load(open("work/music/score.json"))
music,_=sf.read("work/music/m.wav")
TOTAL=70.2; END_MUSIC=68.40
vox=np.zeros(int(TOTAL*SR)); segs=[]; flashes=[]
def place(t,y,g=1.0):
    a=int(t*SR); b=min(len(vox),a+len(y)); vox[a:b]+=y[:b-a]*g
def fxfor(nm,style):
    z=Z.get(nm)
    if z:
        x,y,zz={"n":(z[0],z[1],z[2]*0.75),"big":(z[0],z[1],z[2]*1.3),"punch":z,"slow":z}[style] if style in("n","big","punch","slow") else z
        mode={"punch":"punch","slow":"slow"}.get(style,"fix")
        return [f"zc:{x}:{y}:{zz}:{mode}"]
    return [{"n":"face","big":"facebig","punch":"facepunch","slow":"faceslow"}[style]]
def hit(t,nm,style,L=None,extra=(),g=1.0):
    st,y=clip(nm,L); place(t,y,g); segs.append({"t":round(t,4),"src":st,"fx":fxfor(nm,style)+list(extra)})
BL=1.3004
SECEND={'A':23.44,'B1':44.82,'B2':66.84}
def section(sec,plan,bar0,shakey=False):
    notes=[n for n in score if n[4]==sec]; bars={}
    for n in notes: bars.setdefault(int((n[0]-bar0+0.05)//BL),[]).append(n)
    jk=0
    for b,ns in sorted(bars.items()):
        kind,nm=plan[b%len(plan)]
        prevJ=b>0 and plan[(b-1)%len(plan)][0]=="J"
        if kind=="J" and not prevJ: jk=0
        if kind=="H": continue
        for i,n in enumerate(ns):
            s_=n[0]; gap=n[5]-s_; last=i==len(ns)-1
            ex=["shake"] if shakey and i%2 else []
            if kind=="F":
                if i>0: continue
                span=2 if (b+1)<len(plan) and plan[(b+1)%len(plan)][0]=="H" else 1
                end=min(bar0+(b+span)*BL,SECEND[sec]); hit(s_,nm,"punch",L=end-s_+0.02,extra=["shake"] if "scream" in nm else []); continue
            if kind=="J":
                nm2=JKSEQ[min(jk,len(JKSEQ)-1)]; jk+=1
                style="big" if nm2.startswith("pon") and jk>4 else ("punch" if i==0 else "n")
                hit(s_,nm2,style,L=(S[nm2][1]+0.05) if last else min(S[nm2][1]+0.05,gap-0.012),extra=ex); continue
            # R
            style="punch" if i==0 else ("big" if last else ("n" if i%2 else "punch"))
            hit(s_,nm,style,L=None if last else gap-0.012,extra=ex)
        flashes.append((bar0+b*BL,0.28))
# INTRO: 最初はグー / じゃん けん ぽん ぽん ぽん ぽん
segs.append({"t":0.0,"src":0,"fx":[],"black":True})
E8=0.32508;T=0.72
for (nm,k,ln),st in zip([("saisho",0,2),("jan",2,1),("ken",3,1),("pon",4,1),("pon2",5,1),("pon2",6,1),("pon2",7,1)],
                        ["punch","n","n","punch","big","big","big"]):
    hit(T+k*E8,nm,st,L=ln*E8-0.012,extra=["shake"] if k>=5 else [])
flashes+=[(0.72,0.8),(1.71,0.5)]
J=("J","");PN=("R","pon2");BN=("R","ban");H=("H","")
A_plan=[J,PN,J,("F","uoho"), BN,PN,J,("F","scream1"),
        J,PN,J,("F","eee"),  BN,J,PN,("F","scream2")]
section("A",A_plan,3.32)
B1_plan=[J,PN,BN,("F","scream1"), J,PN,("R","seeno"),("F","uoho"), J,PN,BN,("F","eee"), J,J,PN,("F","scream2"),BN]
section("B1",B1_plan,23.44,shakey=True)
B2_plan=[("F","eee"),J,PN,("F","uoho"), BN,J,PN,("F","scream1"), ("F","eee"),H,J,("F","uoho"), BN,PN,("F","scream2"),H, J,PN]
section("B2",B2_plan,44.24)
# build-up: pon 16ths with zoom growing
t=66.84;i=0
while t<68.1:
    z=1.6+0.15*i; st,y=clip("pon2",0.15); place(t,y,0.95)
    segs.append({"t":round(t,4),"src":st,"fx":[f"zc:{LEFT[0]}:{LEFT[1]}:{min(z,3.2)}:fix"]+(["shake"] if i>=4 else [])})
    t+=0.16254;i+=1
# END: うぉほほほ!
hit(68.18,"uoho","punch",L=1.7,g=1.05); flashes.append((68.18,1.0))
segs.append({"t":69.9,"src":segs[-1]["src"]+1.6,"fx":["freeze",f"zc:{LEFT[0]}:{LEFT[1]}:2.4:fix"]})
mus=music[:int(END_MUSIC*SR)].copy()*0.6
fl=int(0.2*SR); mus[-fl:]*=np.linspace(1,0,fl)[:,None]
mix=np.zeros((len(vox),2)); mix[:len(mus)]+=mus
e=np.abs(vox); k=int(0.03*SR); e=np.convolve(e,np.ones(k)/k,mode="same"); e=np.clip(e/0.25,0,1)
mix*=(1-0.4*e)[:,None]; mix+=np.tanh(vox*1.1)[:,None]*0.85
mix=np.tanh(mix*1.05)/np.tanh(1.05)*0.9
sf.write("work/out_audio.wav",mix,SR); sf.write("work/vox.wav",vox,SR)
json.dump({"segs":segs,"flashes":flashes,"total":TOTAL},open("work/segs.json","w"))
print("segs",len(segs))
