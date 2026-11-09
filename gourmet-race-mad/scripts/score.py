import json,librosa
n=json.load(open("work/music/notes.json"))
def cluster(lst,key):
    out=[]
    for s,e,p,a in lst:
        if out and s-out[-1][0]<0.08:
            if key(p,out[-1][2]): out[-1]=[out[-1][0],max(e,out[-1][1]),p,a]
            else: out[-1][1]=max(out[-1][1],e)
            continue
        out.append([s,e,p,a])
    return out
mel=json.load(open("work/music/mel.json"))
# merge fast same-pitch fragments
m2=[]
for s,e,p,a in mel:
    if m2 and p==m2[-1][2] and s-m2[-1][0]<0.12: m2[-1][1]=max(e,m2[-1][1]); continue
    m2.append([s,e,p,a])
A=[x+["A"] for x in m2 if 3.2<x[0]<23.6]
B2=[x+["B2"] for x in m2 if 44.7<x[0]<66.8]
bass=[x for x in n if x[2]<=46 and x[3]>=0.5 and 23.4<x[0]<44.4]
bass=cluster(bass,lambda p,q:p<q)
b2=[]
for x in bass:
    if b2 and x[2]==b2[-1][2] and x[0]-b2[-1][0]<0.16: continue
    b2.append(x)
B1=[x+["B1"] for x in b2]
allz=sorted(A+B1+B2)
# end = next onset (cap)
for i,x in enumerate(allz):
    nxt=allz[i+1][0] if i+1<len(allz) else x[0]+0.5
    x.append(nxt)
json.dump(allz,open("work/music/score.json","w"))
print(len(A),len(B1),len(B2))
for sec in ["B1","B2"]:
    print(sec," ".join(f"{x[0]:.2f}{librosa.midi_to_note(x[2])}" for x in allz if x[4]==sec))
