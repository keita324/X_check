import json,librosa
n=json.load(open("work/music/notes.json"))
n=[x for x in n if x[2]>=64 and x[3]>=0.35]   # >=E4
# cluster onsets within 50ms, keep highest
out=[]
for s,e,p,a in n:
    if out and s-out[-1][0]<0.06:
        if p>out[-1][2]: out[-1]=[out[-1][0],e,p,a]
        continue
    out.append([s,e,p,a])
# merge extremely short repeated same pitch fragments (<0.09 gap continuation)
mel=[]
for s,e,p,a in out:
    if mel and p==mel[-1][2] and s-mel[-1][1]<0.03 and (e-s)<0.09:
        mel[-1][1]=e; continue
    mel.append([s,e,p,a])
json.dump(mel,open("work/music/mel.json","w"))
for i in range(0,len(mel),8):
    print(" | ".join(f"{s:5.2f}{librosa.midi_to_note(p):>4s}{e-s:.2f}" for s,e,p,a in mel[i:i+8]))
