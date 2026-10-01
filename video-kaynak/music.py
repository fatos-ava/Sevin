import math, struct, wave, random
SR=22050; D=90.0; N=int(SR*D)
bpm=96; beat=60/bpm; bar=beat*4
def mtof(m): return 440*2**((m-69)/12)
# I–vi–IV–V in D major, 2 bars each
chords=[[50,57,62,66,69],[47,54,59,62,66],[43,50,55,59,62],[45,52,57,61,64]]
buf=[0.0]*N
# pad
for ci in range(int(D/(bar*2))+1):
    t0=ci*bar*2; ch=chords[ci%4]
    s0=int(t0*SR); L=int(bar*2*SR)+int(SR*1.2)
    for m in ch:
        f=mtof(m); ph=random.random()*6.28
        w=2*math.pi*f/SR
        for i in range(L):
            j=s0+i
            if j>=N: break
            tt=i/SR
            env=min(1,tt/0.9)*(1 if tt<bar*2 else max(0,1-(tt-bar*2)/1.2))
            buf[j]+=0.035*env*(math.sin(w*i+ph)+0.25*math.sin(2*w*i+ph))
# soft bell arpeggio (8ths)
step=beat/2; k=0; t=bar*1
while t<D-4:
    ch=chords[int(t/(bar*2))%4]; pat=[0,2,3,4,3,2,1,2]
    m=ch[pat[k%8]]+12; f=mtof(m); w=2*math.pi*f/SR
    s0=int(t*SR); amp=0.05 if k%2==0 else 0.035
    for i in range(int(SR*1.0)):
        j=s0+i
        if j>=N: break
        e=math.exp(-i/SR*4.5)*min(1,i/(SR*0.004))
        buf[j]+=amp*e*(math.sin(w*i)+0.3*math.sin(3*w*i)*math.exp(-i/SR*8))
    t+=step; k+=1
# soft kick on beats 1 & 3 from bar 2 to ~84s
t=bar*2
while t<84:
    s0=int(t*SR)
    for i in range(int(SR*0.25)):
        j=s0+i; tt=i/SR
        f=55+60*math.exp(-tt*30)
        buf[j]+=0.10*math.exp(-tt*14)*math.sin(2*math.pi*f*tt)
    t+=beat*2
peak=max(abs(x) for x in buf)
with wave.open('music.wav','wb') as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes(b''.join(struct.pack('<h',int(x/peak*0.8*32767)) for x in buf))
