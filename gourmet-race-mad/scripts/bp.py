import os,basic_pitch
from basic_pitch.inference import predict
d=os.path.dirname(basic_pitch.__file__)+'/saved_models/icassp_2022/nmp.onnx'
mo,midi,notes=predict("work/music/m80.wav",d,minimum_note_length=60)
import json
notes=sorted([(float(s),float(e),int(p),float(a)) for s,e,p,a,_ in notes])
json.dump(notes,open("work/music/notes.json","w"))
print(len(notes))
