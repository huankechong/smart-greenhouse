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
| **审计修 bug 必写报告** | `docs/审计报告/（AR序号_项目名_日期.md）`，序号项目内递增（**已到 AR39，下一个 AR40**；AR01–AR09 已归档 `docs/审计报告/archive/`）。**完整清单与各报告摘要 → `docs/index.md` §三**（含被推翻/回退项的演进链，如 AR33 已被 AR35 推翻、AR32 已回退） |
| **改动后同步 E 盘** | `E:\Documents\BU\第一学期\Introduction to Project Work\花房项目\`，cp 完必须 `ls` 验证（有首拷未落盘的前科）。**E 盘按人类可读名分桶、不沿用仓库的 `outputs/` 目录名**，对照表见下方「E 盘分桶对照」 |
| **删/移文件先问** | 包括"已被取代"的 STL——先标注"勿打印"，等领导明确说要删再删 |
| **大文档整份重建** | 多处改动时重写源文件再落盘，不要逐处 find/replace（换行符 CRLF/LF 和中文路径会坑你） |
| **URL 必须实测** | 写进交付物的链接先 WebFetch 验证 |
| **改完必须验证** | 跑校验脚本、读回文件、实开 HTML；没验证的不算完成 |

## 3. 3D 建模专项红线（踩过的坑都在这里）

0. **实测尺寸优先于商品页标注** —— 2026-10-23 实测教训：1L 打包桶商品页标"上径 136"，实测只有 124（136 是含提手凸缘的最大外径），
   差 12mm 若照原样打印，盖子套不住桶。**凡有到货实测值的零件，先回写参数再打印**；商品页数据只作初值。
1. **一切几何由参数化脚本生成**（`outputs/3D打印件/花房3D_*/  *.py`），禁止手改 STL。改尺寸 = 改脚本顶部 `PARAMS`/`P`。
2. **布尔运算一律 `engine="manifold"`**，否则非流形 / 破面。
3. **坐标必须从参数反算，不许凭几何直觉拍**。历史事故：OLED 屏盒子朝向按局部 Y 当厚度（屏面看不见）、管夹坐标按 `ring_y=8` 算（实际 12，水管穿歪 4mm）、传感器板槽封底（板进不了土）。
4. **"看出来对不对"不算验证**。必须用：布尔求交体积、逐顶点算半径 vs 盆壁、截面面积反算理论值、射线遮挡采样。
   - ❌ 不要用 `mesh.contains()`（STL 射线法不可靠）
   - ❌ 不要用 `Path.section().to_planar()` 判断点在实体内（它会换坐标系）→ 用 **1mm 探针盒布尔求交**
   - ❌ 不要把 `trimesh.util.concatenate` 放进网格搜索内循环（会直接跑死，先预合并）
5. **薄板 + 圆形容器的配合**（盆沿夹爪、弦高、锥度）必须逐顶点验，cm 级件在 mm 级公差下肉眼完全不可靠。
6. **改板厚/槽深时用"从顶面加深"而不是"挪槽底"**——槽底绝对高度不变，装配里所有件都不用重摆。
7. 改完依次跑：`build_*.py` / `p10_tank_lid.py` / `p12_led_plug.py` → `check_base_fit.py` → `check_wires.py` → `audit.py`。**旧 `build_html.py` 展示管线已退役，不再作为交付链步骤**；现行展示只认 `outputs/3D打印件/整机场景/智能花园_3D.html`。改走线先跑 `check_wires.py`（3 秒）快迭代，确认 0 穿模再跑全链（AO 重烘焙约 7 分钟，仅旧装配校验需要）。

## 4. 环境与命令

```bash
PY="C:/Users/junbo/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
NODE="C:/Users/junbo/.workbuddy/binaries/node/versions/22.22.2-6/node.exe"
# 依赖：trimesh manifold3d numpy matplotlib scipy networkx rtree shapely
# HTML 验证：NODE_PATH=C:/Users/junbo/.workbuddy/binaries/node/workspace/node_modules $NODE verify_html.js
```

- Arduino：`outputs/.tools/arduino-cli/arduino-cli.exe`（1.5.2-rc.1）+ **`esp32:esp32@3.3.12`**（fqbn `esp32:esp32:esp32`）。编译缓存被强杀损坏时用 `--build-path` 换新目录，别怀疑代码。
- 固件版本：**v1.9**（7 开关全开，最新编译 **1,122,800B / 85%**，余量 15%）。参数以源码为准：标定 **1855/857**、阈值 **15%**、自动 **2s**/手动 **2s**、I2C **100kHz**。⚠️ 加 OTA/TLS 前先估算体积。

### 4.0 core 3.x 的三个坑（2026-11-22 实机踩过，必看）

1. **U8g2 必须显式传 SCL/SDA**：`U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE, 22, 21)`。不传时 `u8g2.begin()` 内部 `Wire.begin()` 会重置引脚配置 → **屏幕能 ACK（I2C 扫描可读到 0x3C）但全黑**。
2. **I2C 只能 100kHz**：`Wire.setClock(400000)` 下屏同样"能 ACK 但黑屏"。已回退 100k，勿再优化。
3. **库安装位置是 `C:/Users/junbo/Documents/Arduino/libraries`**（不是 `Arduino15/libraries`，后者 arduino-cli 不识别）。四个库：PubSubClient 2.8 / U8g2 2.36.19 / DHT_sensor_library 1.4.7 / Adafruit_Unified_Sensor 1.1.15。库被删时可从 `Arduino15/staging/libraries/*.zip` 直接解压恢复。
4. **不要再尝试装 2.0.x core**：`esp32:esp32` 索引里 2.x 最后一版是 2.0.17，2.0.18 不存在；`arduino:esp32 2.0.18-arduino.5` 是 **Arduino 官方包**（只有 nano_nora 板），不是本项目用的 `esp32:esp32`。**正确做法 = 留在 3.3.12 上做上面两条适配**（11-22 已实测通过：屏幕亮、五通道、MQTT 正常）。
5. **编译/烧录前必查 `config.h` 是否为真值**：该文件被 git 跟踪，提交前要改回占位符——若改回后忘了恢复，编译出的固件 WiFi/MQTT 全断（表现为 `MQTT rc=5`，白排查半小时）。
- 固件源码唯一真相源：`outputs/代码/花房代码/GreenHouse_v1/`；继电器/水泵联调用 `RelayPumpTest/`（测完必须烧回主固件）。

### 4.1 Git 提交到 GitHub（本机已就绪，2026-10-20 实测）

- Git **2.55.0.windows.3** 已装两份：`C:\Program Files\Git`（系统）+ WorkBuddy 自带 PortableGit（`where git` 首位）。**不要重装**。
- 认证走 **Git Credential Manager 2.9.0**（`D:/Appdata/WorkBuddy/resources/vendor/PortableGit/mingw64/bin/git-credential-manager.exe`），全局 `credential.helper` 指向它，已授权账号 `huankechong`；token 在 Windows 凭据管理器，**仓库里不落盘**。
- 远程 `https://github.com/huankechong/smart-greenhouse.git`，分支 `main`。
- 提交身份**已全局配好**（2026-10-20 补齐）：`user.name=huankechong`、`user.email=huankechong@users.noreply.github.com`。**不要再 `git config --local` 覆盖**，写 local 会让新仓库继承不到。
- **`gh` CLI 已装并已认证**（v2.103.2，2026-11-10 核实；旧记录"未装"作废）：`gh auth status` → 账号 `huankechong`，scopes `gist/read:org/repo/workflow`。SSH 密钥仍无 → 走 https。
- 提交前必看 `git status`；`git add` 显式列文件，**不要 `git add .`**（`.gitignore` 已排除 `docs/private/`、`output/`、`.workbuddy/`、截图备份等含个人信息目录）。
- 提交信息写中文，格式 `<类型>: <一句话说明>`；push 后回读 `git log --oneline -3` + `git status`。
- 组员提交操作 → `docs/GitHub与Agent提交代码_零基础手册_2026-10-20.md`（唯一版本）。

#### 4.1.1 ⛔ 一律走 PR，不直推 main（2026-11-10 领导定，长期规则）

`protect-main` ruleset（2026-11-07 建立，`gh api repos/…/rules/branches/main` 可查）要求：main 上**任何改动必须经 PR，且至少 1 个 approving review**；禁删除分支、禁强推；合并方式 squash / merge / rebase 均可。

```bash
git checkout -b <type>/<简述>-<MMDD>      # 例：fix/01b-slot-1110
git add <显式文件>                         # 不用 git add .
git commit -m "<类型>: <说明>"
git push -u origin <branch>
gh pr create --base main --head <branch> --title "<标题>" --body "<要点>"
# 合并：① 优先让组员 approve（真 review 记录，答辩可当协作证据）
#       ② 无人可审时用 owner bypass：gh pr merge <num> --squash --admin
```

- **不要再 `git push origin main`**。2026-11-10 那次直推被 admin bypass 放行（回显 `Bypassed rule violations`），虽成功但**不留 PR / review 记录**，与规则意图不符——这是最后一次例外。
- 分支用完即删：`git push origin --delete <branch>`，仓库长期只留 `main`。
- **分支与 PR 标题的命名规则（2026-11-10 补，起因 #7–#12 四个 PR 漏前缀被领导点名）**：
  分支名 = `r{角色}-{模块}-{MMDD}`（如 `r2-cloud-1021`）；PR 标题 = `<类型>: [R{角色}] <说明>`。
  留痕目的是答辩「这块谁做的」秒答——AI 建分支时必须按角色代入（领导操作 = R1）。
  已合并 PR 的标题可事后补前缀：`gh api -X PATCH repos/…/pulls/{n} -f title="…"`（分支名无法改，只约束新建）。

## 5. 凭据与隐私

- **文档里不落凭据与个人身份**：WiFi/UID/学号/手机号一律走 `config.h` 占位符或"见 E盘/素材/档案"，本仓库只写指针。巴法云 UID 私钥只存在于截图。
- `E盘/素材/巴法云配置/` 不可公开（含私钥截图）。

## 6. 知识库维护

- 每日日志 `.workbuddy/memory/YYYY-MM-DD.md` 追加；**只写"发生了什么 + 为什么"，稳定结论进 docs**。
- 权威文档只有一个：总入口 `docs/index.md`；几何看各 `交付说明_*.md`，进度看交接文档，排期/任务看分工方案 v2（含附录·任务底稿）。同一事实不要在三个地方各写一遍。
- **文档里的路径一律以项目根为基准**（`outputs/…` / `docs/…` / `README.md`），不写 `../`——2026-10-18 把主题文档从 `outputs/` 迁到 `docs/` 时，正是这条规矩让 90% 的引用免于失效。
- 新增/改名交付物后，同步更新：`README.md` 目录表 + 交接文档第五节地图 + E 盘镜像。
- **E 盘分桶对照**（E 盘按人类可读名组织，**不叫 `outputs/`**，核对镜像前先照这张表拼路径，否则会误判"文件缺失"）：

| 仓库路径 | E 盘落位 |
|---|---|
| `README.md` / `AGENTS.md` | 根目录同名 |
| `docs/**`（含 archive） | `docs/**`（同名同构） |
| `outputs/3D打印件/**` | `3D打印件/**`（同名同构，2026-11-08 起两边同构） |
| `outputs/代码/**` | `代码/**`（同名同构；AR01 报告已归档 `docs/审计报告/archive/`） |
| `outputs/素材/**` | `素材/**`（同名同构；**`_敏感_不入库/` 只存在于本机，绝不入库也绝不拷 E 盘公开区**） |
| `docs/private/*`（邮件模板） | `docs/private/*`（同名同构） |
| `outputs/素材/邮件成品/`（申请单 docx/pdf/html 成品） | `素材/邮件成品/`（同名同构；.md 模板在 docs/private/） |
| `outputs/接线图生成器/` | **不镜像**（脚本 + 16 张 `_lead_*.png` 调试中间图，均可再生）；交付物 2 张 PNG 已归位 `docs/操作手册/接线图导出/` |

- **判定"文件缺失"必须做内容级校验**（md5 或去行尾后比对），不能只靠 `[ -e ]` 存在性判断——仓库与 E 盘目录名不同，逐路径 `[ -e ]` 必然误报。AR12 第四节记了这个教训。

## 6.5 3D 打印排期约束（硬规则，别再排错）

- **周末可以打印**（实验室周末 9:00–20:30 开放）。机时按 9~10h 预留、留返工窗口。
- **现行 10 个生产 STL**（01b/03/04/06a/06b/06c/07/10/11/12；06c 实物 ×2）。`8h37m / 338.1g` 是不含 12 的历史切片基线；12 LED 座现场另切。公差测试块不是交付件。**gcode/3mf 已删**，领导现场用 STL 重切。
- **打印开始日 ≠ 死线当天**，且必须留返工窗口（首版 90% 要改尺寸）。
- ⛔ **02 水泵固定座已作废**（2026-10-24，泵自带吸盘直吸桶底）—— 打印清单见 `README.md` §三。
- **⛔ 切片由领导自己做（2026-11-08 定）**：AI **只交付 STL**——单件、**合并件也一样**（多件排一块板的合并模型也必须导出 `.stl`）。不要再跑 Bambu CLI 出 gcode/3mf，也不要把 gcode 当交付物。合并件给 STL 时附带摆放间距说明即可。
- **切片（Bambu Studio）是纯软件，不占打印机**，周末可做；**打印无人值守，占机器不占人**，与实验室其他任务不冲突。
- 改尺寸**只补打偏差件，不重打全套**（参数化脚本改顶部 `PARAMS` 重出 STL，见第 3 节红线 1）。
- 排期细节 → `docs/花房4人分工方案_2026-10-20.md` §六。

## 7. 当前状态（只写指针，别在这里展开）

- 3D：**现役 10 件 STL**（~~08 扎线座 11-19 废弃删除~~，改扎带；02/13 早废）；**10/10 全部完成**（06a 于 11-12 晚开打、11-13 打完，AR36 直口版；06b 排水槽版 11-13 晚重打约 01:00 完，11-12 无槽版作废）。
- 固件：**v1.9**（详见 §4 版本行；参数以源码为准：标定 1855/857、阈值 **15%**、自动 **2s ≈64ml** / 手动 2s、7 开关全开）。实机验证链：五传感器点亮 + 继电器 on/off/t + 11-18 四路复验（水位极性三测翻转定稿）+ 11-19 起 48h 运行 + 11-22 全通道复验（含屏幕点亮）。
- 实验：**全部定稿**——8.1/8.2 ✅（32.1ml/s 实测；浇水时长历经 2s→1s→0.5s→**2s 定稿**，历史值勿引用）；浮球 `LEVEL_WET_CLOSED=false` 定稿；土壤标定 **1855/857**（11-19 三轮修订：真干土/完全浸没端点，旧 2372/1050 已被推翻）；`EN_WATER=1` 实机闭环已跑通（11-13，S1-9.3 视频 86.7s 在库）。**48h 测试已执行并导出全量**（11-19 21:57 起表 → 11-22 18:00 导出，累计约 68h、跨 3 次重启、最长单段连续 53.12h）：本地 LittleFS CSV **24,537 条**在库（`outputs/素材/素材整理_2026-11-22/48h全量.csv`）；前 **14.93h 土壤有效**（中位 76%），11-20 12:00 起因**面包板 GND 轨接触不良**读数锁死 100%，其余通道全程有效；四条发现见 AR39 §九。
- 文档：~~实验报告初稿已入库（`docs/报告/`）~~ **2026-11-22 报告全部删除（领导决断）**——套模板三次事故后止损；git 历史可恢复（最近完整版 = 11-14 v4，commit b07827e）；模板原件在 `C:/Users/junbo/Downloads/Report_Template.docx`。
- 进度详情 → `docs/花房项目_AI工作交接文档_2026-10-18.md` + `docs/花房4人分工方案_2026-10-20.md`（v2）+ `docs/工作日志/`。


## 7.5 事故预防五律（2026-11-16 复盘 27 项返工沉淀；正文 → `docs/审计报告/AR37_*`）

1. **一手律**——实物状态只认领导口述；三态不跳级；PR 无授权不合。
2. **单写者律**——重做成本高的目录同时只一会话写；`reset --hard` 前必 stash/dry-run。
3. **编码律**——中文路径比对：bytes + decode(utf-8) + NFC；禁 text=True；CRLF 文件禁单态 replace。
4. **护栏律**——批量动文件先 dry-run + 白名单断言再执行；清目录跑到不动点。
5. **双验律**——几何必探针验，图形必 audit+目检双轨；验证盲区即时写进脚本。

## 8. 云端资料库：**已停用**（2026-10-20 领导决定）

- 唯一生产源 = 本地 D 盘 git 仓库；E 盘课程目录镜像为第二副本。改文档只改本地 + git commit，**不再上传、不调 library 技能**。
- 原云端空间已清空删除，nodeId 映射全部失效，别再引用。停用原因与历史留档：`docs/审计报告/AR11_GreenHouse知识库全面审计_2026-10-20.md`。

<!-- neat-freak: initialized at 2026-10-18 -->
