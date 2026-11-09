import json,sys
from faster_whisper import WhisperModel
m=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=4)
import soundfile as sf
audio,_=sf.read(sys.argv[1],dtype="float32")
segs,info=m.transcribe(audio,language="ja",word_timestamps=True,vad_filter=True)
out=[]
for s in segs:
    out.append({"s":s.start,"e":s.end,"t":s.text,"w":[(w.start,w.end,w.word,w.probability) for w in s.words]})
    print(f"{s.start:7.2f} {s.end:7.2f} {s.text}",flush=True)
json.dump(out,open(sys.argv[2],"w"),ensure_ascii=False)
