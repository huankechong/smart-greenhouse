# -*- coding: utf-8 -*-
"""
把整机装配模型导出成单文件交互式 HTML (WebGL, 零外部依赖)
- 几何与 build_assembly.py 完全一致
- 顶点数据 int16/uint8 量化后 base64 内嵌, 离线双击可看
用法: python build_html.py
"""
import os, sys, base64, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_assembly as BA   # 复用同一份装配几何

# ---- 图例：按材质归并，颜色统一取自 build_assembly.C（单一数据源，防止漂移）----
LEGEND = [
    ("底盘（两片 + 2 块连接块）", "base"),
    ("3D 打印件 · PLA 白", "white"),
    ("花盆", "pot"),
    ("土壤", "soil"),
    ("植株", "stem"),
    ("面包板", "breadboard"),
    ("ESP32", "mcu"),
    ("继电器", "relay"),
    ("OLED 屏", "screen"),
    ("双色 LED 灯珠", "led"),
    ("传感器 / 模块板", "pcb_green"),
    ("水箱（前壁剖开）", "tank"),
    ("水体", "water"),
    ("水泵", "pump"),
    ("水管", "tube"),
    ("螺丝 / 排针 / 屏蔽罩", "metal"),
    ("铜探头 / 天线", "gold"),
    ("跳线 / 印线", "wire"),
]

SCALE = 50.0     # int16 量化: 1 单位 = 0.02mm, 覆盖 ±655mm

pos, nrm, col = [], [], []
AO_ALL = BA.get_ao()
for k, (mesh, ck, nm) in enumerate(BA.items):
    tri = mesh.triangles.reshape(-1, 3)          # 每三角 3 顶点
    n = np.repeat(mesh.face_normals, 3, axis=0)
    ao = np.repeat(BA.get_ao()[k], 3)[:, None]   # 逐面 AO（与 PNG/glb 同源）
    c = np.tile(np.array(BA.C[ck], dtype=float), (len(tri), 1)) * (0.40 + 0.60 * ao)
    pos.append(tri)
    nrm.append(n)
    col.append(c)

P = np.concatenate(pos).astype(np.float32) * SCALE
N = np.concatenate(nrm).astype(np.float32) * 127.0
C = np.concatenate(col).astype(np.float32) * 255.0

assert np.abs(P).max() < 32760, "超出 int16 量化范围"
Pi = np.round(P).astype(np.int16)
Ni = np.clip(np.round(N), -127, 127).astype(np.int8)
Ci = np.clip(np.round(C), 0, 255).astype(np.uint8)

# 每顶点 4 字节对齐的 normal / color (WebGL 对 BYTE 属性对齐更挑)
Ni4 = np.zeros((len(Ni), 4), dtype=np.int8); Ni4[:, :3] = Ni
Ci4 = np.zeros((len(Ci), 4), dtype=np.uint8); Ci4[:, :3] = Ci
Pi = np.ascontiguousarray(Pi)

b64 = lambda a: base64.b64encode(a.tobytes()).decode("ascii")

data = {
    "n": int(len(Pi)),
    "pos": b64(Pi),
    "nrm": b64(Ni4),
    "col": b64(Ci4),
    "scale": SCALE,
    "bounds": [float(P[:, 0].min() / SCALE), float(P[:, 1].min() / SCALE), float(P[:, 2].min() / SCALE),
               float(P[:, 0].max() / SCALE), float(P[:, 1].max() / SCALE), float(P[:, 2].max() / SCALE)],
    "tris": int(len(Pi) // 3),
    "legend": [{"name": name, "rgb": [round(x * 255) for x in BA.C[key]],
                "hex": "#%02x%02x%02x" % tuple(round(x * 255) for x in BA.C[key])}
               for name, key in LEGEND],
}

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>智能花房养护站 · 整机示意模型</title>
<style>
  :root{
    --ink:#1b2028; --ink2:#5b6675; --line:#e3e7ed; --bg:#f4f6f9;
    --accent:#2f6fd0;
  }
  *{box-sizing:border-box}
  html,body{height:100%;margin:0}
  body{
    font-family:-apple-system,"Segoe UI","Microsoft YaHei",system-ui,sans-serif;
    color:var(--ink); background:var(--bg); overflow:hidden;
    display:flex; flex-direction:column;
  }
  header{
    padding:14px 20px 12px; background:#fff; border-bottom:1px solid var(--line);
    display:flex; align-items:baseline; gap:14px; flex-wrap:wrap; z-index:2;
  }
  header h1{font-size:17px; margin:0; font-weight:650; letter-spacing:.2px}
  header .sub{font-size:12.5px; color:var(--ink2)}
  main{flex:1; display:flex; min-height:0}
  #stage{flex:1; position:relative; min-width:0}
  canvas{display:block; width:100%; height:100%; cursor:grab; touch-action:none}
  canvas:active{cursor:grabbing}
  .hint{
    position:absolute; left:14px; bottom:12px; font-size:12px; color:var(--ink2);
    background:rgba(255,255,255,.82); border:1px solid var(--line); border-radius:8px;
    padding:6px 10px; backdrop-filter:blur(6px);
  }
  .views{
    position:absolute; left:14px; top:12px; display:flex; gap:6px; flex-wrap:wrap;
    max-width:calc(100% - 28px);
  }
  .views button{
    font:inherit; font-size:12.5px; padding:6px 11px; border-radius:8px; cursor:pointer;
    border:1px solid var(--line); background:#fff; color:var(--ink); transition:.15s;
  }
  .views button:hover{border-color:#b9c6d8}
  .views button.on{background:var(--accent); border-color:var(--accent); color:#fff}
  aside{
    width:250px; flex:0 0 250px; background:#fff; border-left:1px solid var(--line);
    padding:16px 16px 20px; overflow:auto;
  }
  aside h2{font-size:12px; letter-spacing:.8px; text-transform:uppercase; color:var(--ink2); margin:0 0 10px}
  .legend{list-style:none; margin:0 0 18px; padding:0; display:grid; gap:7px}
  .legend li{display:flex; align-items:center; gap:9px; font-size:12.5px}
  .sw{width:14px; height:14px; border-radius:4px; border:1px solid rgba(0,0,0,.14); flex:0 0 14px}
  .stat{font-size:12.5px; color:var(--ink2); line-height:1.85}
  .stat b{color:var(--ink); font-weight:600}
  footer{font-size:11.5px; color:#8b95a4; padding:10px 20px; background:#fff; border-top:1px solid var(--line)}
  @media (max-width:820px){
    aside{display:none}
    header h1{font-size:15px}
  }
</style>
</head>
<body>
<header>
  <h1>智能花房养护站 Smart GreenHouse</h1>
  <span class="sub">整机示意模型 · 3D 打印件按 1:1 实体装配</span>
</header>
<main>
  <div id="stage">
    <canvas id="c"></canvas>
    <div class="views">
      <button data-v="iso" class="on">轴测</button>
      <button data-v="front">正视</button>
      <button data-v="top">俯视</button>
      <button data-v="back">左后</button>
      <button data-v="spin" id="spin">自动旋转</button>
    </div>
    <div class="hint">拖拽旋转 · 滚轮缩放 · 右键/Shift 拖拽平移</div>
  </div>
  <aside>
    <h2>图例</h2>
    <ul class="legend" id="legend"></ul>
    <h2>模型信息</h2>
    <div class="stat" id="stat"></div>
  </aside>
</main>
<footer>单位 mm · 底板 z=0 为桌面 · 生成于 2026-10-18</footer>

<script id="payload" type="application/json">__DATA__</script>
<script>
(function(){
"use strict";
const D = JSON.parse(document.getElementById('payload').textContent);

/* ---------- base64 -> typed array ---------- */
function b64ToU8(s){
  const bin = atob(s), n = bin.length, out = new Uint8Array(n);
  for (let i=0;i<n;i++) out[i] = bin.charCodeAt(i);
  return out;
}

const NV = D.n;
const posI = new Int16Array(b64ToU8(D.pos).buffer);
const nrmI = new Int8Array(b64ToU8(D.nrm).buffer);
const colI = new Uint8Array(b64ToU8(D.col).buffer);
const SCALE = D.scale;

/* ---------- canvas ---------- */
const canvas = document.getElementById('c');
const gl = canvas.getContext('webgl', {antialias:true, alpha:false, preserveDrawingBuffer:true});
if(!gl){ document.getElementById('stage').innerHTML =
  '<div style="padding:40px;font-size:14px;color:#b23">当前浏览器不支持 WebGL，请换 Chrome / Edge 打开。</div>'; return; }

function sh(type, src){
  const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
  if(!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
  return s;
}
const prog = gl.createProgram();
gl.attachShader(prog, sh(gl.VERTEX_SHADER, `
  attribute vec3 aPos; attribute vec3 aNrm; attribute vec3 aCol;
  uniform mat4 uMVP; uniform float uScale;
  varying vec3 vN; varying vec3 vC;
  void main(){
    vN = normalize(aNrm);
    vC = aCol;
    gl_Position = uMVP * vec4(aPos / uScale, 1.0);
  }`));
gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, `
  precision mediump float;
  varying vec3 vN; varying vec3 vC;
  uniform vec3 uLight;
  void main(){
    float d = max(dot(normalize(vN), normalize(uLight)), 0.0);
    vec3 c = vC * (0.44 + 0.56 * d);
    /* 顶部微亮、底部略暗，增加体积感 */
    c *= 0.96 + 0.08 * clamp(vN.z, 0.0, 1.0);
    gl_FragColor = vec4(c, 1.0);
  }`));
gl.linkProgram(prog);
if(!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
gl.useProgram(prog);

function buf(arr, target){
  const b = gl.createBuffer();
  gl.bindBuffer(target || gl.ARRAY_BUFFER, b);
  gl.bufferData(target || gl.ARRAY_BUFFER, arr, gl.STATIC_DRAW);
  return b;
}
const bPos = buf(posI), bNrm = buf(nrmI), bCol = buf(colI);

const aPos = gl.getAttribLocation(prog, 'aPos');
const aNrm = gl.getAttribLocation(prog, 'aNrm');
const aCol = gl.getAttribLocation(prog, 'aCol');
const uMVP = gl.getUniformLocation(prog, 'uMVP');
const uScale = gl.getUniformLocation(prog, 'uScale');
const uLight = gl.getUniformLocation(prog, 'uLight');
gl.uniform1f(uScale, SCALE);
gl.uniform3f(uLight, 0.42, 0.55, 0.72);

gl.bindBuffer(gl.ARRAY_BUFFER, bPos);
gl.enableVertexAttribArray(aPos);
gl.vertexAttribPointer(aPos, 3, gl.SHORT, false, 6, 0);

gl.bindBuffer(gl.ARRAY_BUFFER, bNrm);
gl.enableVertexAttribArray(aNrm);
gl.vertexAttribPointer(aNrm, 3, gl.BYTE, false, 4, 0);

gl.bindBuffer(gl.ARRAY_BUFFER, bCol);
gl.enableVertexAttribArray(aCol);
gl.vertexAttribPointer(aCol, 3, gl.UNSIGNED_BYTE, true, 4, 0);

gl.enable(gl.DEPTH_TEST);
gl.enable(gl.CULL_FACE);
gl.cullFace(gl.BACK);

/* ---------- 矩阵 ---------- */
function mul(a,b){
  const o = new Float32Array(16);
  for(let i=0;i<4;i++)for(let j=0;j<4;j++){
    let s=0; for(let k=0;k<4;k++) s += a[k*4+j]*b[i*4+k];
    o[i*4+j]=s;
  }
  return o;
}
function perspective(fovy, aspect, near, far){
  const f = 1/Math.tan(fovy/2), nf = 1/(near-far);
  return new Float32Array([f/aspect,0,0,0, 0,f,0,0, 0,0,(far+near)*nf,-1, 0,0,2*far*near*nf,0]);
}
function lookAt(eye, center, up){
  let zx=eye[0]-center[0], zy=eye[1]-center[1], zz=eye[2]-center[2];
  let l=Math.hypot(zx,zy,zz); zx/=l; zy/=l; zz/=l;
  let xx=up[1]*zz-up[2]*zy, xy=up[2]*zx-up[0]*zz, xz=up[0]*zy-up[1]*zx;
  l=Math.hypot(xx,xy,xz)||1; xx/=l; xy/=l; xz/=l;
  const yx=zy*xz-zz*xy, yy=zz*xx-zx*xz, yz=zx*xy-zy*xx;
  return new Float32Array([
    xx,yx,zx,0, xy,yy,zy,0, xz,yz,zz,0,
    -(xx*eye[0]+xy*eye[1]+xz*eye[2]),
    -(yx*eye[0]+yy*eye[1]+yz*eye[2]),
    -(zx*eye[0]+zy*eye[1]+zz*eye[2]), 1
  ]);
}

/* ---------- 包围盒 / 相机 ---------- */
const B = D.bounds;
const ctr = [(B[0]+B[3])/2, (B[1]+B[4])/2, (B[2]+B[5])/2];
const radius = 0.5*Math.hypot(B[3]-B[0], B[4]-B[1], B[5]-B[2]);
const target0 = [ctr[0], ctr[1], ctr[2] + radius*0.02];

let theta = 42*Math.PI/180, phi = 26*Math.PI/180, dist = radius*2.35;
let target = target0.slice();

const VIEWS = {
  iso:   {th: 42,  ph: 26, k: 2.35},
  front: {th: 8,   ph: 16, k: 2.05},
  top:   {th: 0,   ph: 88, k: 2.30},
  back:  {th: -122,ph: 24, k: 2.35}
};
function setView(name){
  const v = VIEWS[name]; if(!v) return;
  theta = v.th*Math.PI/180; phi = v.ph*Math.PI/180; dist = radius*v.k;
  target = target0.slice();
  spinOn = false;
  document.getElementById('spin').classList.remove('on');
  document.querySelectorAll('.views button[data-v]').forEach(b=>b.classList.toggle('on', b.dataset.v===name));
}

/* ---------- 交互 ---------- */
let drag = null;
canvas.addEventListener('contextmenu', e=>e.preventDefault());
canvas.addEventListener('pointerdown', e=>{
  canvas.setPointerCapture(e.pointerId);
  drag = {x:e.clientX, y:e.clientY, pan:(e.button===2||e.shiftKey)};
});
canvas.addEventListener('pointermove', e=>{
  if(!drag) return;
  const dx = e.clientX-drag.x, dy = e.clientY-drag.y;
  drag.x = e.clientX; drag.y = e.clientY;
  if(drag.pan){
    const s = dist/900;
    const right = [-Math.sin(theta), Math.cos(theta), 0];
    const upv = [-Math.cos(theta)*Math.sin(phi), -Math.sin(theta)*Math.sin(phi), Math.cos(phi)];
    for(let i=0;i<3;i++){
      target[i] -= right[i]*dx*s;
      target[i] += upv[i]*dy*s;
    }
  }else{
    theta -= dx*0.0075;
    phi = Math.max(-1.45, Math.min(1.45, phi + dy*0.0075));
  }
});
canvas.addEventListener('pointerup', e=>{ drag=null; canvas.releasePointerCapture(e.pointerId); });
canvas.addEventListener('wheel', e=>{
  e.preventDefault();
  dist = Math.max(radius*0.35, Math.min(radius*6, dist * (1 + Math.sign(e.deltaY)*0.09)));
}, {passive:false});

document.querySelectorAll('.views button[data-v]').forEach(b=>{
  b.addEventListener('click', ()=>setView(b.dataset.v));
});
let spinOn = false;
document.getElementById('spin').addEventListener('click', function(){
  spinOn = !spinOn;
  this.classList.toggle('on', spinOn);
});

/* ---------- 图例 / 统计 ---------- */
const lg = document.getElementById('legend');
D.legend.forEach(x=>{
  if(!x.name) return;
  const li = document.createElement('li');
  const sw = document.createElement('span');
  sw.className='sw';
  sw.style.background = `rgb(${x.rgb.join(',')})`;
  li.appendChild(sw);
  li.appendChild(document.createTextNode(x.name));
  lg.appendChild(li);
});
document.getElementById('stat').innerHTML =
  `<b>${D.tris.toLocaleString()}</b> 个三角面<br>` +
  `外形 <b>${Math.round(B[3]-B[0])} × ${Math.round(B[4]-B[1])} × ${Math.round(B[5]-B[2])}</b> mm<br>` +
  `坐标系：底板 z=0 为桌面`;

/* ---------- 渲染 ---------- */
function resize(){
  const dpr = Math.min(window.devicePixelRatio||1, 2);
  const w = canvas.clientWidth, h = canvas.clientHeight;
  if(canvas.width!==w*dpr || canvas.height!==h*dpr){
    canvas.width = w*dpr; canvas.height = h*dpr;
  }
  gl.viewport(0,0,canvas.width,canvas.height);
  return canvas.width/canvas.height;
}

let last = performance.now();
function frame(t){
  const dt = Math.min((t-last)/1000, 0.05); last = t;
  if(spinOn) theta += dt*0.45;

  const aspect = resize();
  const cp = Math.cos(phi), sp = Math.sin(phi);
  const eye = [
    target[0] + dist*cp*Math.cos(theta),
    target[1] + dist*cp*Math.sin(theta),
    target[2] + dist*sp
  ];
  const view = lookAt(eye, target, [0,0,1]);
  const proj = perspective(38*Math.PI/180, aspect, dist*0.05, dist*12);
  const mvp = mul(proj, view);

  gl.clearColor(0.955, 0.965, 0.978, 1);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.uniformMatrix4fv(uMVP, false, mvp);
  gl.drawArrays(gl.TRIANGLES, 0, NV);

  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
setView('iso');

window.addEventListener('keydown', e=>{
  const m = {'1':'iso','2':'front','3':'top','4':'back'}[e.key];
  if(m) setView(m);
});
})();
</script>
</body>
</html>
"""

out = os.path.join(HERE, "花房整机示意模型.html")
html = HTML.replace("__DATA__", json.dumps(data, ensure_ascii=False))
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("HTML: %s  %.2f MB  三角面 %d  顶点 %d" % (
    out, os.path.getsize(out) / 1024 / 1024, data["tris"], data["n"]))
