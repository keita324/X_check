import subprocess,sys,numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
src,out,D=sys.argv[1],sys.argv[2],float(sys.argv[3])
W,H,FPS=1280,720,30; VW,VH=1080,1920
FULL=[(0,0.72),(12.42,13.72),(16.32,21.21)]          # 縦画面いっぱいのドアップ区間
FT="fonts/KaiseiTokumin.ttf"
f1=ImageFont.truetype(FT,112); f2=ImageFont.truetype(FT,150); f3=ImageFont.truetype(FT,46)
dec=subprocess.Popen(["ffmpeg","-v","error","-i",src,"-f","rawvideo","-pix_fmt","rgb24","-"],stdout=subprocess.PIPE)
enc=subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{VW}x{VH}","-r",str(FPS),"-i","-",
     "-i",src,"-map","0:v","-map","1:a","-c:v","libx264","-crf","19","-preset","slow","-pix_fmt","yuv420p","-c:a","copy","-shortest","-movflags","+faststart",out],stdin=subprocess.PIPE)
# static title layer
title=Image.new("RGBA",(VW,VH),(0,0,0,0)); d=ImageDraw.Draw(title)
for txt,f,y,col in [("塩崎大智で",f1,250,"#ffffff"),("グルメレース",f2,385,"#ffe14d")]:
    w=d.textlength(txt,font=f); d.text(((VW-w)/2,y),txt,font=f,fill=col,stroke_width=10,stroke_fill="#000000")
i=0
while True:
    raw=dec.stdout.read(W*H*3)
    if len(raw)<W*H*3: break
    t=i/FPS; fr=Image.frombuffer("RGB",(W,H),raw)
    full=any(a<=t<b for a,b in FULL)
    if full:
        cw=int(H*VW/VH); x0=(W-cw)//2
        canvas=fr.crop((x0,0,x0+cw,H)).resize((VW,VH),Image.BILINEAR)
    else:
        sw=int(H*VW/VH)                                   # blurred, darkened background
        small=fr.crop(((W-sw)//2,0,(W-sw)//2+sw,H)).resize((108,192)).filter(ImageFilter.GaussianBlur(4))
        canvas=Image.eval(small.resize((VW,VH),Image.BILINEAR),lambda v:int(v*0.55))
        fg=fr.resize((VW,int(H*VW/W)),Image.BILINEAR); canvas.paste(fg,(0,(VH-fg.size[1])//2))
        canvas=canvas.convert("RGBA"); canvas.alpha_composite(title); canvas=canvas.convert("RGB")
    # race progress bar (bottom)
    d=ImageDraw.Draw(canvas); bx,by,bw,bh=90,1610,900,24; p=min(1,t/D)
    d.rounded_rectangle((bx-4,by-4,bx+bw+4,by+bh+4),12,fill="#000000")
    d.rounded_rectangle((bx,by,bx+bw,by+bh),10,fill="#5a5a5a")
    if p>0.01: d.rounded_rectangle((bx,by,bx+int(bw*p),by+bh),10,fill="#ffe14d")
    cx=bx+int(bw*p); d.ellipse((cx-22,by+bh/2-22,cx+22,by+bh/2+22),fill="#ffffff",outline="#000000",width=5)
    gw=d.textlength("GOAL",font=f3); d.text((bx+bw-gw,by-70),"GOAL",font=f3,fill="#ffffff",stroke_width=5,stroke_fill="#000000")
    enc.stdin.write(canvas.tobytes()); i+=1
enc.stdin.close(); enc.wait(); print("frames",i)
