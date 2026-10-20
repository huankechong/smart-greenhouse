# AGENTS.md — 花房项目 AI 行为准则

> 给在本工作区干活的 AI（Claude Code / Codex / WorkBuddy 等）。
> **规则手册，不是变更日志**：不写"某日某功能上线"，历史叙事归 `docs/审计报告/` 与 `memory/`。
> 接手第一件事：读 `docs/index.md` → `docs/花房项目_AI工作交接文档_2026-10-18.md`。

## 1. 身份与沟通

- 用户称"**领导**"，AI 自称"**小马**"；中文为主，术语/代码保留英文。
- 指令极简（"好""可以""a"= 选定该方案）；收到"可以了/完事了"后**自动推进下一步**，不要再问一次。
- **先推断意图 → 给 2–4 个带利弊的方案 → 领导拍板 → 执行**。不替他定死，但也不要把选择题变成问卷（一次 1–2 题）。
- 结论先行；不编数据、不猜图（读不出就走 RapidOCR，并注明"以实物/邮件为准"）。

## 2. 交付纪律

| 规则 | 具体做法 |
|---|---|
| **审计修 bug 必写报告** | `docs/审计报告/AR序号_项目名_修复报告_日期.md`，序号项目内递增（**已到 AR11，下一个 AR12**；AR08 圆桶化 / AR09 走线 / AR10 代码审计 / AR11 知识库审计，勿混用） |
| **改动后同步 E 盘** | `E:\Documents\BU\第一学期\Introduction to Project Work\花房项目\`，cp 完必须 `ls` 验证（有首拷未落盘的前科） |
| **删/移文件先问** | 包括"已被取代"的 STL——先标注"勿打印"，等领导明确说要删再删 |
| **大文档整份重建** | 多处改动时重写源文件再落盘，不要逐处 find/replace（换行符 CRLF/LF 和中文路径会坑你） |
| **URL 必须实测** | 写进交付物的链接先 WebFetch 验证 |
| **改完必须验证** | 跑校验脚本、读回文件、实开 HTML；没验证的不算完成 |

## 3. 3D 建模专项红线（踩过的坑都在这里）

1. **一切几何由参数化脚本生成**（`outputs/花房3D_*/  *.py`），禁止手改 STL。改尺寸 = 改脚本顶部 `PARAMS`/`P`。
2. **布尔运算一律 `engine="manifold"`**，否则非流形 / 破面。
3. **坐标必须从参数反算，不许凭几何直觉拍**。历史事故：OLED 屏盒子朝向按局部 Y 当厚度（屏面看不见）、管夹坐标按 `ring_y=8` 算（实际 12，水管穿歪 4mm）、传感器板槽封底（板进不了土）。
4. **"看出来对不对"不算验证**。必须用：布尔求交体积、逐顶点算半径 vs 盆壁、截面面积反算理论值、射线遮挡采样。
   - ❌ 不要用 `mesh.contains()`（STL 射线法不可靠）
   - ❌ 不要用 `Path.section().to_planar()` 判断点在实体内（它会换坐标系）→ 用 **1mm 探针盒布尔求交**
   - ❌ 不要把 `trimesh.util.concatenate` 放进网格搜索内循环（会直接跑死，先预合并）
5. **薄板 + 圆形容器的配合**（盆沿夹爪、弦高、锥度）必须逐顶点验，cm 级件在 mm 级公差下肉眼完全不可靠。
6. **改板厚/槽深时用"从顶面加深"而不是"挪槽底"**——槽底绝对高度不变，装配里所有件都不用重摆。
7. 改完依次跑：`build_*.py` / `p10_tank_lid.py` → `check_base_fit.py` → `check_wires.py` → `audit.py` → `build_html.py` → `verify_html.js`。**改走线先跑 `check_wires.py`（3 秒）快迭代，确认 0 穿模再跑全链（AO 重烘焙约 7 分钟）。**

## 4. 环境与命令

```bash
PY="C:/Users/junbo/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
NODE="C:/Users/junbo/.workbuddy/binaries/node/versions/22.22.2-6/node.exe"
# 依赖：trimesh manifold3d numpy matplotlib scipy networkx rtree shapely
# HTML 验证：NODE_PATH=C:/Users/junbo/.workbuddy/binaries/node/workspace/node_modules $NODE verify_html.js
```

- Arduino：`outputs/.tools/arduino-cli/arduino-cli.exe`（1.5.2-rc.1）+ `esp32:esp32@2.0.18-arduino.5`（fqbn `esp32:esp32:esp32`）。编译缓存被强杀损坏时用 `--build-path` 换新目录，别怀疑代码。
- 固件版本：**v1.5.1**（v1.5 全量代码审计修复 → v1.5.1 水位断泵改按 waterState 判定），编译字节数以 `outputs/花房代码/GreenHouse_v1/README.md` 为准。
- 固件源码唯一真相源：`outputs/花房代码/GreenHouse_v1/`。

## 5. 凭据与隐私

- **文档里不落凭据与个人身份**：WiFi/UID/学号/手机号一律走 `config.h` 占位符或"见 E盘/素材/档案"，本仓库只写指针。巴法云 UID 私钥只存在于截图。
- `E盘/素材/巴法云配置/` 不可公开（含私钥截图）。

## 6. 知识库维护

- 每日日志 `.workbuddy/memory/YYYY-MM-DD.md` 追加；**只写"发生了什么 + 为什么"，稳定结论进 docs**。
- 权威文档只有一个：总入口 `docs/index.md`；几何看各 `交付说明_*.md`，进度看交接文档，日程看 30 天计划。同一事实不要在三个地方各写一遍。
- **文档里的路径一律以项目根为基准**（`outputs/…` / `docs/…` / `README.md`），不写 `../`——2026-10-18 把主题文档从 `outputs/` 迁到 `docs/` 时，正是这条规矩让 90% 的引用免于失效。
- 新增/改名交付物后，同步更新：`README.md` 目录表 + 交接文档第五节地图 + E 盘镜像。

## 7. 当前状态（只写指针，别在这里展开）

10 个打印件 STL 已交付（01b/02/03/04/06a/06b/06c/07/08/10）；整机示意 glb + 离线 HTML 已出；固件 **v1.5.1**（2026-10-20 AR10 全量代码审计修复，见 `docs/审计报告/AR10_*`）；硬件等快递（10/21±）；答辩 2026-11-16。
细节 → `docs/花房项目_AI工作交接文档_2026-10-18.md`。

## 8. 云端资料库映射（WorkBuddy 项目空间，2026-10-19 起）

改动云端文档 = 用 library 技能（doc 节点走 doc/entry.md 的编辑流程，drive 文件走替换流程），**不要只改本地不同步云**。本地（D 盘/git）仍为生产源，云版本改动完成后回推 git。

| 云端节点 | nodeId |
|---|---|
| README | 03Zob7ABODk4XklGx42W2z |
| AGENTS | Uyl87N8HyRPg1lHHcX0f58 |
| 花房项目_AI工作交接文档_2026-10-18 | ujykWO1B2R6prOFsKby2K3 |
| 花房30天执行计划 | 6nebaE9cxjrieJ1CPUsVrf |
| 花房接线规划表 | 1A7cOaJS6AWUV6rXcBZdH5 |
| 花房FinalProject方案书 | SIi2MIidfL00f50nmyknIt |
| index（docs 索引） | CxI35S4mNp7cJ49JAITtyv |
| AR02 审计报告 | qvuoCS3zOSCQjTVcVvPPHi |
| AR03 审计报告 | Z0EFzn3B4IO7j5r71NRtqx |
| AR04 审计报告 | HyrMCwtijUdV9odOLHrayF |
| GreenHouse_v1（drive 文件夹） | tv65GaSPuz0HScD9Br434i |
| AR05 打印件装配优化（2026-10-19 新增） | zE3xzi8p2keE6wyGq05G4b |
| AR06 土壤传感器支架v2（2026-10-20 补传） | C77BCddpEBCPvbH2yjLXIX |
| AR07 低水位保护落地（2026-10-20 补传） | thfLdpy0CR4dwUwNNJgqTE |
| AR01 代码审计修复（2026-10-20 补传） | 8q21c19wItzhdj0wMy5Inx |
| AR08 示意模型圆桶化（2026-10-20 补传） | FPTRDpWRSl4SsiDKDMtZcu |
| AR09 走线优化（2026-10-20 补传） | oSn3m0bkpunWAq1790WG6A |
| AR10 代码全面审计（2026-10-20 补传） | nQayAKJjse8vIBMPytgzXt |
| AR11 知识库全面审计（2026-10-20 补传） | IkIT5C4dvTcEONFoiSXLwC |

- 云端有一作废节点（标题带【作废勿用-内容实为AR06】，id `yxhN44PI5L0rUYkuP8R4BW`，无删除 API）——勿引用，等手动删除。
- AR01–AR11 报告已全数上云（AR01 本体在 `outputs/花房代码/`，其余在 `docs/审计报告/`）。

**云端有两个空间，别混：**

| spaceId | spaceName | 装什么 |
|---|---|---|
| `Hy2wV7oRfX7RRRIJcFEXYU` | 花房 | 主文档区：README、AGENTS、index、30 天计划、接线表、方案书、交接文档等（**本表上半部分的 nodeId 属于此空间**） |
| `TESQXngJ4tIC1hKd2ccd9p` | （AR 报告区） | AR01–AR11 审计报告 + GreenHouse_v1 drive 文件夹（**AR 系列的 nodeId 属于此空间**） |

> 上表 nodeId 未标空间的按所在空间对号入座：README–index 七项在「花房」空间，AR01–AR11 与 drive 在 AR 空间。

<!-- neat-freak: initialized at 2026-10-18 -->
