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
| **审计修 bug 必写报告** | `docs/审计报告/（AR序号_项目名_日期.md）`，序号项目内递增（**已到 AR35，下一个 AR36**；AR30 本地+E盘+GitHub 全面审计 / AR31 01b 阶梯槽 / AR32 03 插土针（已回退） / AR33 01b 感湿窗中间态（已被 AR35 推翻） / AR34 03 插土针加强（去斜撑版） / AR35 01b 定版裸露（**01b 现行口径**），AR10 代码审计 / AR11 知识库审计 / AR12 口径补漏 / AR13 云端销账 / AR14 硬件到货核对 / AR15 打包桶实测修订 / AR16–AR17 全量技术审计两轮 / AR18 全仓过时清理 / AR19 文档体系重组 / AR20 OLED 支架走线位修复 / AR21 DHT11 小座造型重做 / AR22 光敏电阻定位与模型 / AR23 按实测返修 04 屏架+继电器槽 / AR24 全模型可打印性审计 / AR25 底盘小件嵌槽 / AR26 模型脚本审计 / AR27 浮空面炒面 / AR28 01b 板槽 / AR29 04 屏槽换算 / AR30 本地+E盘+GitHub 全面审计 / AR31 01b 阶梯槽 / AR32 03 插土针（已回退） / AR33 01b 感湿窗（开窗被否），勿混用；AR01–AR09 已归档 `docs/审计报告/archive/`） |
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
7. 改完依次跑：`build_*.py` / `p10_tank_lid.py` → `check_base_fit.py` → `check_wires.py` → `audit.py` → `build_html.py` → `verify_html.js`。**改走线先跑 `check_wires.py`（3 秒）快迭代，确认 0 穿模再跑全链（AO 重烘焙约 7 分钟）。**

## 4. 环境与命令

```bash
PY="C:/Users/junbo/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
NODE="C:/Users/junbo/.workbuddy/binaries/node/versions/22.22.2-6/node.exe"
# 依赖：trimesh manifold3d numpy matplotlib scipy networkx rtree shapely
# HTML 验证：NODE_PATH=C:/Users/junbo/.workbuddy/binaries/node/workspace/node_modules $NODE verify_html.js
```

- Arduino：`outputs/.tools/arduino-cli/arduino-cli.exe`（1.5.2-rc.1）+ `esp32:esp32@2.0.18-arduino.5`（fqbn `esp32:esp32:esp32`）。编译缓存被强杀损坏时用 `--build-path` 换新目录，别怀疑代码。
- 固件版本：**v1.6**，双形态编译已验证（默认 **271.7KB/21%**，全开关 **1055KB/82%**，2026-11-09 复测）。⚠️ 全开关余量只剩 **≈230KB**，加 Web 页/传感器/OTA 前先估算体积。改动历史见 AR16–AR17、AR30。
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

- **周末可以打印**（2026-11-07 老师课件：实验室 C312/C313/C314 周末 9:00–20:30 开放；拓竹 X2D 在哪间待周一现场确认）。机时仍按 9~10h 预留、仍要留返工窗口。
- **现行 10 件**切片实测口径合计 **8h37m / 338g**（拓竹 X2D 0.4mm；**gcode/3mf 已于 2026-11-08 全删**，领导现场自行重切；耗时/耗材口径备查见 ）：底盘两片 5.0h + 其余八件 3.57h，按 9~10h 预留机时。
- **打印开始日 ≠ 死线当天**，且必须留返工窗口（首版 90% 要改尺寸）。
- ⛔ **02 水泵固定座已作废**（2026-10-24，泵自带吸盘直吸桶底）—— 打印清单见 `README.md` §三。
- **⛔ 切片由领导自己做（2026-11-08 定）**：AI **只交付 STL**——单件、**合并件也一样**（多件排一块板的合并模型也必须导出 `.stl`）。不要再跑 Bambu CLI 出 gcode/3mf，也不要把 gcode 当交付物。合并件给 STL 时附带摆放间距说明即可。
- **切片（Bambu Studio）是纯软件，不占打印机**，周末可做；**打印无人值守，占机器不占人**，与实验室其他任务不冲突。
- 改尺寸**只补打偏差件，不重打全套**（参数化脚本改顶部 `PARAMS` 重出 STL，见第 3 节红线 1）。
- 现行排期：**周一 11/09 19:00 到 C311 交打印**（拓竹 X2D 在 **C311**，C311 晚上也开放，2026-11-08 领导确认）。机时规则（2026-11-08 实测）：**不能过夜挂机；但 20:30 前开打的件打到完为止** → 当晚交 06c+五小件+水箱盖（3h25m，约 22:20 完）；底盘两片 5h 放不下单晚 → 分两晚（周二 06a / 周三 06b）或周六全天一次打完。细节 → `docs/花房4人分工方案_2026-10-20.md` §六 S2。

## 7. 当前状态（只写指针，别在这里展开）

- 3D：**11 件 STL 定稿**（10 件 + 12 LED 座；13 盖板 11-13 删除）；**已打 10/11**（+06a/12 于 11-12），**仅余 06b**（AR36 直口版）。装配校验链全绿（check_base_fit 实测过）。
- 固件：**v1.6**，`WATER_MS=2000`（2026-11-10 实测 32.1ml/s 定稿）；实机验证含五传感器点亮 + 继电器 on/off/t。
- 实验：**全部定稿（2026-11-12）**——8.1 ✅ / 8.2 ✅（32.1ml/s→WATER_MS=2000）/ 浮球常开型实测定稿（LEVEL_WET_CLOSED=true）/ 土壤标定 2372/1050（交叉验证吻合）→ **EN_WATER=1，闭环解锁（固件层就绪）**。⚠️ **整机未拼完：pigtail ×2 未到货**（强电回路未接通），到货 → 实机闭环验证 → 48h 连续运行。
- 文档：实验报告初稿已入库（`docs/报告/`）。
- 进度详情 → `docs/花房项目_AI工作交接文档_2026-10-18.md` + `docs/花房4人分工方案_2026-10-20.md`（v2）+ `docs/工作日志/`。


## 8. 云端资料库：**已停用**（2026-10-20 领导决定）

**不再做云端资料库同步。** 云端空间「花房」（`Hy2wV7oRfX7RRRIJcFEXYU`）已于 2026-10-20 由领导手动清空删除；AR 报告空间（`TESQXngJ4tIC1hKd2ccd9p`）的内容也一并作废。

- **唯一生产源 = 本地 D 盘 git 仓库**（`D:\Documents\workbuddydocument\2026-10-17-08-59-13`），E 盘课程目录镜像为第二副本。
- 改文档只改本地 + git commit，**不要再上传、不要调 library 技能写云端**。
- 原云端 nodeId 映射表（19 个节点）**已全部失效**，故整表删除，不再维护——避免日后误引用已不存在的节点。
- 停用前的历史映射（两个 spaceId、19 个 nodeId、AR08–AR11 的补传记录）留档在 `docs/审计报告/AR11_GreenHouse知识库全面审计_2026-10-20.md`，仅作历史查考，不作操作依据。
- 停用原因（原始问题，供理解决策背景）：云端主空间那批文档停留在 10-18/19 的旧版（固件 v1.1、9 个打印件、AR02–AR04），与本地已修正版脱节；而 `create_doc.py` 未暴露 `--node-block-id/--confirm-overwrite`，整篇覆盖需逐块 delete + insert（实测单节点读回 8 分钟未返回），维护成本高于收益 → 干脆清空，以本地 git 为准。
- **清空状态已确认（2026-10-20 15:35 复核）**：云端花房相关内容零残留，含我在"不同步"指令发出前误传的 README.md（`BUqqrRK4Roi6B84K0gkC04`）也已被删除。**云端不再是本项目任何信息的来源，别再引用。**

<!-- neat-freak: initialized at 2026-10-18 -->
