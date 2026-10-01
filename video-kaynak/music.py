# Lansman altyapı müziği: 120 BPM, D–Bm–G–A; sahne geçişlerinde riser + impact vurgusu
import math, struct, wave, random
random.seed(7)
SR=32000; D=90.0; N=int(SR*D)
L=[0.0]*N; R=[0.0]*N
BPM=120; beat=60/BPM; bar=beat*4
TR=[7,19,31,41,52,66,75,85]          # sahne geçişleri
def mtof(m): return 440*2**((m-69)/12)
chords=[[50,54,57,62],[47,50,54,59],[43,47,50,55],[45,49,52,57]]
def chord_at(t): return chords[int(t/(bar))%4]
def add(i,v,pan=0.0):
    if 0<=i<N:
        L[i]+=v*(1-pan)*0.5*2**.5; R[i]+=v*(1+pan)*0.5*2**.5
def duck(t):  # geçişlerden sonra kısa sidechain hissi
    for x in TR:
        if 0<=t-x<0.5: return 0.35+0.65*(t-x)/0.5
    return 1.0
def dens(t):  # yoğunluk: giriş sakin, sonra tam, kapanış sakin
    if t<7: return 0.0
    if t>=85: return 0.0
    return 1.0
# --- pad (supersaw benzeri, yumuşak) ---
for b in range(int(D/bar)+1):
    t0=b*bar; ch=chord_at(t0+0.01)
    for m in ch+[ch[0]+12]:
        for det in (-0.08,0.08):
            f=mtof(m+det); w=2*math.pi*f/SR; ph=random.random()*6.3; pan=det*6
            s0=int(t0*SR)
            for i in range(int((bar+0.6)*SR)):
                tt=i/SR; t=t0+tt
                env=min(1,tt/0.25)*(1 if tt<bar else max(0,1-(tt-bar)/0.6))
                lvl=0.010 if t<85 else 0.010*max(0,1-(t-85)/4.5)
                if t<7: lvl*=min(1,0.4+t/7*0.6)
                add(s0+i,lvl*env*duck(t)*(math.sin(w*i+ph)+0.3*math.sin(2*w*i+ph)+0.12*math.sin(3*w*i+ph)),pan)
# --- pluck arpeggio 16'lık (girişte de var) ---
step=beat/4; k=0; t=0.5
while t<85:
    ch=chord_at(t); pat=[0,1,2,3,4,3,2,1]
    m=(ch+[ch[0]+12])[pat[k%8]]+12; f=mtof(m); w=2*math.pi*f/SR
    s0=int(t*SR); amp=(0.045 if k%4==0 else 0.028)*duck(t); pan=0.35 if k%2 else -0.35
    for i in range(int(SR*0.45)):
        e=math.exp(-i/SR*9)*min(1,i/(SR*0.003))
        add(s0+i,amp*e*(math.sin(w*i)+0.4*math.sin(2*w*i)*math.exp(-i/SR*20)),pan)
    t+=step; k+=1
# --- bas (8'lik, kök nota) ---
t=7.0
while t<85:
    f=mtof(chord_at(t)[0]-12); w=2*math.pi*f/SR; s0=int(t*SR)
    for i in range(int(SR*beat/2*0.9)):
        tt=i/SR; e=min(1,tt/0.005)*math.exp(-tt*5)
        add(s0+i,0.09*e*duck(t+tt)*(math.sin(w*i)+0.25*math.sin(2*w*i)))
    t+=beat/2
# --- davul ---
def kick(t,a=0.32):
    s0=int(t*SR)
    for i in range(int(SR*0.35)):
        tt=i/SR; f=48+90*math.exp(-tt*28)
        add(s0+i,a*math.exp(-tt*9)*math.sin(2*math.pi*(48*tt+90*(1-math.exp(-tt*28))/28)))
def clap(t,a=0.10):
    s0=int(t*SR); y=0
    for i in range(int(SR*0.22)):
        tt=i/SR; x=random.uniform(-1,1); y+=0.55*(x-y); hp=x-y
        e=math.exp(-tt*22)*(1 if tt>0.02 else (0.6+0.4*math.sin(tt*900)))
        add(s0+i,a*e*hp,random.uniform(-.2,.2))
def hat(t,a=0.035,pan=0.3):
    s0=int(t*SR); prev=0
    for i in range(int(SR*0.06)):
        x=random.uniform(-1,1); hp=x-prev; prev=x
        add(s0+i,a*math.exp(-i/SR*70)*hp,pan)
b=7.0
while b<85-1e-6:
    for q in range(4):
        tq=b+q*beat
        if tq>=85: break
        kick(tq)
        if q in (1,3): clap(tq)
        hat(tq+beat/2,0.04,0.3); hat(tq+beat/4,0.018,-0.3); hat(tq+3*beat/4,0.018,-0.3)
    b+=bar
# --- geçiş vurguları: riser + impact ---
def riser(tend,dur=1.2,a=0.10):
    s0=int((tend-dur)*SR); y=0
    for i in range(int(dur*SR)):
        p=i/(dur*SR); x=random.uniform(-1,1); c=0.02+0.5*p**2; y+=c*(x-y)
        add(s0+i,a*p**2.2*y*1.8,math.sin(p*12)*0.5)
def impact(t,a=0.5):
    s0=int(t*SR); y=0
    for i in range(int(SR*1.6)):
        tt=i/SR
        boom=math.exp(-tt*3.2)*math.sin(2*math.pi*(40*tt+70*(1-math.exp(-tt*18))/18))
        x=random.uniform(-1,1); y+=0.25*(x-y)
        crash=math.exp(-tt*4)*(x-y)*0.5
        add(s0+i,a*(boom*0.8+crash*0.45),0)
impact(0.0,0.35)
for x in TR:
    riser(x,1.2 if x!=7 else 2.0)
    impact(x,0.55 if x in (7,85) else 0.42)
# kapanış: son akor halkası
for m in [50,57,62,66,69,74]:
    w=2*math.pi*mtof(m+12)/SR; s0=int(85*SR)
    for i in range(int(SR*5)):
        add(s0+i,0.02*math.exp(-i/SR*0.9)*math.sin(w*i),0)
pk=max(max(abs(v) for v in L),max(abs(v) for v in R))
with wave.open('music.wav','wb') as wf:
    wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes(b''.join(struct.pack('<hh',int(l/pk*0.9*32767),int(r/pk*0.9*32767)) for l,r in zip(L,R)))
