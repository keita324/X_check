import sys,json,subprocess,numpy as np,soundfile as sf,librosa
name,vid,N=sys.argv[1],sys.argv[2],int(sys.argv[3])
v,sr=sf.read(f"work/sep/htdemucs/{name}/vocals.wav"); v=v.mean(1)
fr=441; n=len(v)//fr
r=np.sqrt((v[:n*fr].reshape(n,fr)**2).mean(1))
k=5; sm=np.convolve(r,np.ones(k)/k,mode="same")
th=max(np.percentile(sm,97)*0.45,0.03)
ev=[];i=0
while i<n:
    if sm[i]>th:
        j=i
        while j<n and (sm[j]>th*0.5 or sm[j:j+8].max()>th): j+=1
        if 12<=j-i<=400: ev.append((i/100,j/100,float(sm[i:j].max()),float(sm[i:j].mean())))
        i=j
    else: i+=1
# pitch (scream = high f0)
y16=librosa.resample(v.astype(np.float32),orig_sr=sr,target_sr=16000)
res=[]
for s,e,pk,mn in ev:
    seg=y16[int(s*16000):int(e*16000)]
    try:
        f0=librosa.yin(seg,fmin=90,fmax=1200,sr=16000,frame_length=1024)
        med=float(np.median(f0))
    except Exception: med=0
    res.append(dict(s=round(s,2),e=round(e,2),pk=round(pk,3),f0=int(med),score=pk*(1+med/400)))
res=sorted(res,key=lambda d:-d["score"])[:N]; res.sort(key=lambda d:d["s"])
json.dump(res,open(f"work/n/{name}_ev.json","w"))
F="/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
import os; os.makedirs(f"work/n/ev_{name}",exist_ok=True)
for i,d in enumerate(res):
    t=(d["s"]+d["e"])/2
    subprocess.run(["ffmpeg","-v","error","-y","-ss",f"{t:.2f}","-i",vid,"-frames:v","1","-vf",
      f"scale=256:144,drawtext=fontfile={F}:text='{i} {d['s']:.1f}-{d['e']:.1f} f{d['f0']}':fontsize=17:fontcolor=yellow:borderw=2:x=3:y=3",f"work/n/ev_{name}/{i:03d}.png"])
print(len(res)); print(" ".join(f"{i}:{d['s']}-{d['e']}/{d['pk']}/{d['f0']}" for i,d in enumerate(res)))
