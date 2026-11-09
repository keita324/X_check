import numpy as np,pyworld as pw
SR=44100
def tune(x,midi,dur,sr=SR,stretch_max=4.0,keep_len=False,formant=1.0):
    """x: mono float64 clip. returns audio of length dur seconds, f0 flattened to midi."""
    x=np.ascontiguousarray(x,dtype=np.float64)
    fp=5.0
    f0,t=pw.harvest(x,sr,f0_floor=70,f0_ceil=800,frame_period=fp)
    sp=pw.cheaptrick(x,f0,t,sr); ap=pw.d4c(x,f0,t,sr)
    n=len(f0)
    nout=max(2,int(round(dur*1000/fp)))
    if keep_len:
        idx=np.minimum(np.arange(nout),n-1)
    else:
        r=n/nout
        r=min(max(r,1/stretch_max),1.0) if n<nout else 1.0   # stretch if short; if long, play at normal speed and truncate
        idx=np.minimum((np.arange(nout)*r).astype(int),n-1)
    f=f0[idx].copy(); s=sp[idx].copy(); a=ap[idx].copy()
    hz=440*2**((midi-69)/12)
    voiced=f>0
    # fill small unvoiced gaps -> voiced for a more "sung" sound
    f[voiced]=hz
    if voiced.sum()<len(f)*0.3:
        f[:]=hz; a=np.minimum(a,0.6)
    if formant!=1.0:
        # shift spectral envelope
        nb=s.shape[1]; src=np.clip(np.arange(nb)/formant,0,nb-1)
        s=np.array([np.interp(src,np.arange(nb),row) for row in s])
    y=pw.synthesize(np.ascontiguousarray(f),np.ascontiguousarray(s),np.ascontiguousarray(a),sr,fp)
    L=int(dur*sr); y=y[:L]
    if len(y)<L: y=np.pad(y,(0,L-len(y)))
    fade=min(int(0.012*sr),L//4)
    if fade>0:
        y[:fade]*=np.linspace(0,1,fade); y[-fade:]*=np.linspace(1,0,fade)
    pk=np.max(np.abs(y))+1e-9
    return y/pk*0.9
