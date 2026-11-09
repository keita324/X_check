# ---- v7 timeline: lines fitted to the 16th grid by speeding up / cutting (pitch unchanged) ----
from audiotsm import wsola
from audiotsm.io.array import ArrayReader,ArrayWriter
G0=0.7198; S16=0.16254
def slot_t(k): return G0+k*S16
BACK=(0.41,0.50,2.6)   # back-seat singer in the car
L=lambda *ws:[(a,b,t) for a,b,t in ws]
LINES={
 "tomo1":(L((14.68,15.12,"まだ"),(15.12,15.86,"友達"),(15.86,16.22,"なんか"),(16.22,16.96,"いらない"),(16.96,17.24,"よ")),BACK),
 "tomo2":(L((17.88,18.82,"2年に"),(18.82,19.32,"なっても"),(19.32,20.36,"いらないよ")),BACK),
 "tomo3":(L((20.36,21.72,"一生に"),(21.72,22.26,"1人"),(22.26,23.12,"見つければ"),(23.12,23.40,"いい")),BACK),
 "omae":(L((104.98,105.46,"お前"),(105.46,106.12,"いつも通り"),(106.12,106.54,"なしって"),(106.54,106.96,"自分で"),(106.96,107.50,"言ったじゃん")),None),
 "itsumo":(L((108.06,108.60,"いつも通り"),(108.60,108.82,"なし"),(108.82,109.06,"だよ")),None),
 "game":(L((164.42,164.92,"最高の"),(164.92,165.28,"パフォーマンス"),(165.28,165.86,"するために"),(165.86,166.12,"ゲーム"),(166.12,166.26,"なんか"),(166.26,166.60,"しません")),None),
 "iuna":(L((777.36,778.40,"言うなよ"),(778.40,778.84,"お前!"),(779.34,779.84,"お前"),(779.84,780.40,"言うな!")),None),
 "hisa":(L((266.11,266.61,"久しぶり"),(266.61,266.85,"すぎた"),(266.85,267.25,"久しぶり"),(267.25,267.80,"すぎんだよね")),None),
 "shiawase":(L((813.92,814.66,"幸せって"),(814.66,815.10,"2種類"),(815.10,815.60,"あんねん")),None),
 "zutto":(L((796.55,797.10,"ずっと"),(797.10,797.80,"見続けて")),None),
 "nani":(L((249.79,251.05,"何してんの"),(251.05,251.40,"これ"),(252.23,252.67,"これ"),(252.67,253.10,"なに")),None),
}
def tsm(y,target_len):
    n=int(target_len*SR)
    if len(y)<16 or n<16: return np.zeros(max(n,1))
    rate=len(y)/n
    if rate>2.6:  # too long even at 2.6x: cut
        y=y[:int(2.6*n)]; rate=2.6
    if 0.93<rate<1.07:
        out=y[:n]
    else:
        r=ArrayReader(y[None,:].astype(np.float32)); w=ArrayWriter(1)
        wsola(1,speed=rate,frame_length=1024,synthesis_hop=256).run(r,w)
        out=w.data[0]
    out=out[:n]
    if len(out)<n: out=np.pad(out,(0,n-len(out)))
    return out,rate
def word_audio(s,e):
    st=s
    a=raw(s,0.15,True); fr=441;n=len(a)//fr
    if n>2:
        r=np.sqrt((a[:n*fr].reshape(n,fr)**2).mean(1)); i=int(np.argmax(r>max(r.max()*0.3,0.01))); st=s+max(0,i-1)*0.01
    return st,raw(st,max(e-st,0.05),True)
def kfx(zt,j,n):
    if zt: x,y,z=zt; return [f"zc:{x}:{y}:{z*(1.15 if j==n-1 else 1.0)}:{'punch' if j==0 else 'fix'}"]
    return ["facepunch"] if j==0 else (["facebig"] if j==n-1 else ["face"])
def alloc(ds,T):
    tot=sum(ds); raw_=[d/tot*T for d in ds]; sl=[max(1,int(x)) for x in raw_]
    while sum(sl)<T:
        i=max(range(len(ds)),key=lambda i:raw_[i]-sl[i]); sl[i]+=1
    while sum(sl)>T:
        i=max(range(len(ds)),key=lambda i:sl[i]-raw_[i] if sl[i]>1 else -9); sl[i]-=1
    return sl
def line(k,name,speed=1.3,stutter=0,echo=0,T=None):
    ws,zt=LINES[name]; words=[w[2] for w in ws]; n=len(ws)
    ds=[e-s for s,e,_ in ws]; D=sum(ds)
    if T is None: T=max(4,int(round(D/speed/S16/4))*4)
    sl=alloc(ds,T)
    for j in range(stutter):
        st,y=word_audio(*ws[0][:2]); y=env(norm(y[:int((S16-0.012)*SR)]),3,10); place(slot_t(k),y)
        segs.append({"t":round(slot_t(k),4),"src":st,"fx":kfx(zt,0,n),"kara":{"words":words,"cur":0}}); k+=1
    for j,(s,e,t) in enumerate(ws):
        st,y=word_audio(s,e); y,rate=tsm(y,sl[j]*S16-0.012); y=env(norm(y),3,12); place(slot_t(k),y)
        segs.append({"t":round(slot_t(k),4),"src":st,"spd":round(min(rate,2.6),3),"fx":kfx(zt,j,n),"kara":{"words":words,"cur":j}})
        k+=sl[j]
    for j in range(echo):
        s,e,t=ws[-1]; st,y=word_audio(s,e); y,rate=tsm(y,2*S16-0.012); place(slot_t(k),env(norm(y),3,12),0.9-0.12*j)
        segs.append({"t":round(slot_t(k),4),"src":st,"spd":round(min(rate,2.6),3),"fx":kfx(zt,n-1,n),"kara":{"words":words,"cur":n-1}}); k+=2
    return k
def jk(k,pat):
    last=0
    for item in pat.split():
        nm,o=item.split(":"); o=int(o)
        st,y=clip(nm,S16*2-0.012 if nm in("jan","ken") else S16-0.012); place(slot_t(k+o),y)
        segs.append({"t":round(slot_t(k+o),4),"src":st,"fx":fxfor(nm,"punch" if o==0 else ("big" if nm.startswith("pon") else "n"))}); last=max(last,o)
    return k+last+1
def full(k,nm,slots):
    st,y=clip(nm,slots*S16-0.012); place(slot_t(k),y)
    segs.append({"t":round(slot_t(k),4),"src":st,"fx":fxfor(nm,"punch")+(["shake2"] if "scream" in nm else [])}); return k+slots
def rep(k,nm,n,every=2):
    for j in range(n):
        st,y=clip(nm,every*S16-0.012); place(slot_t(k),y); segs.append({"t":round(slot_t(k),4),"src":st,"fx":fxfor(nm,"big" if j%2 else "punch")}); k+=every
    return k
def al(k,m=4): return -(-k//m)*m
k=80
JK1="jan:0 ken:2 pon:4 pon2:6 pon2:7"
TL=[
 ("line","tomo1",dict(stutter=2,T=12)),("line","tomo1",dict(T=6)),          # normal, then 2x faster
 ("line","tomo2",dict(T=12)),("line","tomo3",dict(T=12,echo=2)),("full","scream2",8),
 ("jk",JK1),("line","omae",dict(T=16)),("line","itsumo",dict(T=6,echo=1)),("line","itsumo",dict(T=4)),("full","scream1",8),
 ("line","iuna",dict(T=12)),("line","iuna",dict(T=8)),("rep","ban",2,4),("line","game",dict(T=16,echo=1)),("full","uoho",10),
 ("jk",JK1),("line","hisa",dict(T=12)),("line","hisa",dict(T=8)),("rep","ban",2,4),
 ("line","shiawase",dict(stutter=3,T=8)),("line","shiawase",dict(T=6)),("jk",JK1),
 ("line","zutto",dict(T=6)),("line","zutto",dict(T=4)),("line","zutto",dict(T=4)),("line","nani",dict(T=12,echo=1)),("full","eee",8),
 ("line","tomo3",dict(T=10)),("jk",JK1),("line","omae",dict(T=12)),("line","game",dict(T=8)),("full","scream1",8),("full","scream2","FILL"),
]
for ev in TL:
    flashes.append((slot_t(k),0.25))
    if ev[0]=="line": k=line(k,ev[1],**ev[2])
    elif ev[0]=="jk": k=jk(k,ev[1])
    elif ev[0]=="full": k=full(k,ev[1],ev[2] if ev[2]!="FILL" else max(4,407-k))
    elif ev[0]=="rep": k=rep(k,ev[1],ev[2],ev[3])
    k=al(k)
    print(f"{ev[0]:5s} {ev[1]:10s} -> slot {k} t={slot_t(k):.2f}")
