# 从注册 GitHub 到用 Agent 提交代码 · 零基础操作手册

**版本** v1.0　·　**日期** 2026-10-20　·　**读者** 花房项目组员（零基础）

- 本文是 HTML 版的 Markdown 镜像：`docs/GitHub与Agent提交代码_零基础手册_2026-10-20.html`（HTML 版排版更好、可直接打印；本文便于在编辑器里搜索与批注）
- 配套：`docs/花房4人分工方案_2026-10-20.md`（分工）· `AGENTS.md`（项目红线）

**读完这份你要能做到的事**

1. 有一个能用的 GitHub 账号（含 2FA，不会被锁）
2. 电脑上装好 Git，第一次克隆时浏览器点一下授权就完成登录
3. 每次干活走固定五步：同步 → 开自己分支 → 改文件 → 让 Agent 提交 → 推上去开 PR
4. 看得懂 9 种常见报错，自己能修
5. 不会把学号、手机号、密钥、私钥截图推到公开仓库

**三个不需要**

- 不需要手工造 token —— Git for Windows 自带凭据管理器，浏览器授权即可
- 不需要学全部 Git —— 只用 7 条命令，其余交给 Agent
- 不需要命令行基础 —— 所有命令都是复制粘贴，位置固定

---

## 目录

0. [零、先选路线：你该走哪条](#零先选路线你该走哪条)
1. [一、注册 GitHub 账号（约 10 分钟）](#一注册-github-账号约-10-分钟)
2. [二、安装 Git for Windows（约 8 分钟）](#二安装-git-for-windows约-8-分钟)
3. [三、建仓库、拉组员进来（约 8 分钟）](#三建仓库拉组员进来约-8-分钟)
4. [四、首次克隆（约 5 分钟，只需做一次）](#四首次克隆约-5-分钟只需做一次)
5. [五、日常五步：每次干活都走这条](#五日常五步每次干活都走这条)
6. [六、用 Agent 提交代码](#六用-agent-提交代码)
7. [七、提交前安全检查（不许踩的红线）](#七提交前安全检查不许踩的红线)
8. [八、9 种常见报错速查](#八9-种常见报错速查)
9. [九、四个人的分支怎么命名](#九四个人的分支怎么命名)
10. [十、一页速查（建议打印贴显示器旁）](#十一页速查建议打印贴显示器旁)
11. [十一、macOS 用户看这里](#十一macos-用户看这里)

---

## 零、先选路线：你该走哪条

全篇讲的是**两条并行路线，不是二选一学一套，而是按活选**。先答三个问题：

1. 你要交的东西**需要在本机跑起来**吗？（编译固件、跑 Python 重出 STL、执行脚本）→ 是，走 **Git 路线**（第二、四、五章）
2. 单个文件**超过 1 MB** 吗？（STL、PPT、PDF、视频、手机原图）→ 是，走 **Git 路线**
3. 以上都不涉及，只是改文本（Markdown、代码、短报告、小图）→ **连接器路线**够用（§6.5），本机可以不装 Git

| 对照项 | Git 路线 | 连接器路线 |
|---|---|---|
| 要装什么 | Git for Windows + 本机 clone | 只连 WorkBuddy 的 GitHub 连接器 |
| 单文件上限 | 仓库单文件 100 MB（再大需 LFS） | **1 MB** |
| 合并保护 | 有：`git pull` 时冲突当场报错 | **无：后写的整份覆盖先写的** |
| 多文件一次提交 | 可以，`git add` 多个文件一个 commit | 不可以，一次一个文件一个 commit |
| 出问题怎么查 | `git status` / `git log`，记录都在本地 | 只能看网页上的 commit 记录 |
| 适合谁 | R1 固件、R2 上云代码、R3 打印参数 | R4 文档、报告、小图 |

**混用三条规矩**（同一个仓库里两种人同时干活，必须守）：

1. **同一个文件不要两条路线交替改**——连接器没有合并保护，最后一次写入会把 Git 那边的内容整份盖掉
2. 走 Git 的人开工前照旧 `git pull`；走连接器的人开工前先读 sha（见 §6.5）
3. 谁的文件谁改，要动别人的文件先在群里说一句

### 最短一句话（配置完成后，两条路线各一句）

| 路线 | 一句话 | 能覆盖的范围 |
|---|---|---|
| 连接器 | `把 D:\GreenHouse\报告.md 提到 r4-docs-1021 分支，开 PR，先别合并` | 单个文本文件，≤1 MB |
| Git | `把当前改动提交并推上去` | 多个文件、任意大小、自动带历史 |

**让"一句话"成立的前提是三件固定好的事**，缺一件 Agent 就得多问一句：

1. **固定仓库**：Agent 已绑定这个仓库，不用每次报 owner/repo
2. **固定分支规则**：`角色-模块-日期`（见第九节），它自己能算出来
3. **固定目录结构**：谁的文件在哪个目录下，它不用猜

---

## 一、注册 GitHub 账号（约 10 分钟）

注册是唯一一次需要小心填的地方——用户名会出现在所有提交记录里，改起来麻烦。

### A1　打开官网，点注册

浏览器访问 `https://github.com`，点右上角 **Sign up**。

> **注意｜国内网络提示**
>
> github.com 在国内可能间歇性打不开或很慢。若页面一直转圈：换手机热点试一次；或在同一个网络下重试几次（多数是瞬时问题）。**不要在打不开的页面上反复点注册**，容易注册出半成品账号。

### A2　填邮箱、密码、用户名

依次填三项，然后点 **Create account**：

- **Email**：用你能长期收到的邮箱（QQ 邮箱、163 都行）
- **Password**：至少 15 个字符，或至少 8 个字符且含数字和小写字母
- **Username**：只能用字母、数字、单个连字符，不能有空格和中文。建议统一格式，例如 `junbo-dt`、`dt1-r2-li`

> **禁止｜用户名不要填学号**
>
> 用户名会永久出现在每一次提交记录、每一个 PR 里，等于把学号公开挂在网上。**用"名字缩写 + 项目"就够了**，例如 `dt1-wang`。

### A3　完成人机验证 + 邮箱验证码

网页会让你做一个拼图/旋转类验证，通过后去邮箱收 6 位或 8 位验证码，填进去。

注册完会问你 "How many team members"、"Student or teacher" 这类问卷，**全部可以跳过或随便选**，不影响使用。最后选 **Free** 计划。

### A4　开启双因素认证 2FA（必须做，否则以后会被锁号）

GitHub 从 2023 年 3 月起，对**所有贡献代码的账号**强制要求 2FA。不开启的话，会先收到通知，进入 45 天注册期，超期后账号会被限制访问。

操作路径，一步一步点：

1. 右上角点头像 → **Settings**
2. 左侧栏找到 **Password and authentication**（在 Access 分组里）
3. 点 **Enable two-factor authentication**
4. 页面出现二维码 → 用手机上的验证器 App 扫码
5. 把 App 里显示的 6 位数字填进网页 → 继续
6. 页面给出 **16 个恢复码** → 点 **Download** 存下来，放到电脑以外的地方（手机相册、U 盘都行）

> **提示｜手机上装什么 App**
>
> 任意 TOTP 验证器都行：Microsoft Authenticator、Google Authenticator、1Password 都可以。**不要只依赖短信**——短信在多数国家可用但安全性较弱，GitHub 官方推荐验证器 App 作为主要方式。

> **禁止｜那 16 个恢复码比密码还重要**
>
> 手机丢了、换手机没迁移，就靠恢复码登录。丢了恢复码又丢了手机，账号恢复需要向 GitHub 提交所有权证明，要等几个工作日。**现在就存，别等。**



---

## 二、安装 Git for Windows（约 8 分钟）

> **提示｜Mac 用户跳过本章**
>
> 本章及第四章的终端操作是 Windows 专属。macOS 的等价做法（装 Git、认证、路径、行尾）集中在**第十一节**，其余章节命令通用。

### B1　下载安装包

访问 `https://git-scm.com/download/win`，下载 **64-bit Git for Windows Setup**。

不要下 Portable 便携版——它不带凭据管理器，登录会变麻烦。

### B2　安装：一路 Next，只有一处要注意

安装向导选项很多，全部保持默认即可。唯一建议看一眼的是 **Configuring the line ending conversions** 这一步：

- 选 **Checkout Windows-style, commit Unix-style line endings**（默认项）

> **注意｜为什么提这个**
>
> Windows 和 Mac/Linux 的换行符不一样。选默认项，Git 会自动转换，你在 Windows 上正常编辑，提交出去的是标准格式。选错了以后每个文件都会显示"整份都被改过"，diff 全是红绿一片。

### B3　验证装好了

在桌面或任意文件夹空白处 **右键 → Show more options → Git Bash Here**（Win11 要先点"显示更多选项"），会弹出一个黑底终端。

输入下面这行，回车：

```bash
git --version
```

看到类似 `git version 2.5x.x.windows.1` 就成功了。

### B4　配置身份（三行命令，各敲一次，永久生效）

在同一个 Git Bash 窗口里，逐行复制粘贴、每行回车：

```bash
git config --global user.name "你的昵称"
git config --global user.email "你的noreply邮箱"
git config --global core.quotepath false
```

三条分别的作用：

| 命令                     | 作用                                   |
| ---------------------- | ------------------------------------ |
| `user.name`            | 提交记录里显示的署名，建议和分工角色对应，如 `R2-Li`       |
| `user.email`           | 提交记录里的邮箱，**必须用 noreply 地址**，见下方说明    |
| `core.quotepath false` | 让中文文件名正常显示，否则会变成 `\344\270\255` 这种乱码 |

> **禁止｜noreply 邮箱怎么拿（重要）**
>
> 网页右上角头像 → **Settings** → 左侧 **Emails** → 勾选 **Keep my email addresses private**。页面上会显示你的专属地址，形如：
>
> ```
> 12345678+你的用户名@users.noreply.github.com
> ```
>
> 把这个地址填进上面的 `user.email`。**直接用真实邮箱的后果**：每次提交都会把真实邮箱永久写进公开的提交记录里，爬虫会抓走。

---

## 三、建仓库、拉组员进来（约 8 分钟）

由**组长**（R1）一个人操作，组员等邀请邮件即可。

### C1　新建仓库

1. 右上角 **+** → **New repository**
2. **Repository name**：填 `greenhouse-project`（小写、连字符）
3. **Description**：一行中文说明，如 `智能花房养护站 - IPW 期末项目`
4. 选 **Private**（私有）
5. 勾选 **Add a README file**
6. **Add .gitignore** 先选 None（我们后面自己写，见第七节）
7. **License** 选 None
8. 点 **Create repository**

> **提示｜为什么用私有库，不建组织**
>
> 私有库 + 邀请 3 个协作者，功能上完全够用，还少一层账号体系。组织（Organization）适合需要分权限、长期多人维护的场景，对一个课程项目是多余负担。

### C2　把 3 位组员加成协作者

1. 进入刚建好的仓库页面
2. 点上方 **Settings**（不是头像里的那个 Settings，是仓库自己的）
3. 左侧 **Collaborators**（在 Access 分组）
4. 点绿色 **Add people**
5. 输入组员的**用户名或注册邮箱** → 从下拉里选中 → **Add**
6. 重复三次，把三个人都加上

### C3　组员接受邀请

组员会收到 GitHub 邮件（标题含 **invitation**），点邮件里的 **View invitation** → 网页上点 **Accept invitation**。

没收到邮件：让组长在 Collaborators 页面看该组员状态是否还是 **Pending invite**，是的话点旁边的重新发送；也可以让组员直接打开邮件里的链接在浏览器登录后接受。

### C4　拿到克隆地址

仓库首页 → 绿色 **Code** 按钮 → 复制 **HTTPS** 那一栏的地址，形如：

```
https://github.com/你的用户名/greenhouse-project.git
```

### C5　只拿链接，怎么把文件下载下来

不需要装 git，三种方式按需求选：

| 想要什么 | 怎么做 | 注意 |
|---|---|---|
| **单个文件** | 打开该文件页面 → 右上角的下载图标（Download raw file），或点 **Raw** 后右键另存 | 私有库必须先登录且有权限 |
| **整个仓库当前版本** | 绿色 **Code** → **Download ZIP** → 解压 | 压缩包**不含 git 历史**，也没有 `.git` 目录，改完无法提交 |
| **一份成品交给老师** | 同上 ZIP | 对方只要收文件，不需要任何账号 |

有 git 环境时，命令行等价写法：

```bash
curl -L -o repo.zip https://github.com/owner/repo/archive/refs/heads/main.zip
```

**三条容易判断错的地方：**

1. **链接本身不含权限。** 私有库把链接给谁，谁也得先被加成 collaborator 并登录，否则打开是 404——不是链接错，是没权限。
2. **ZIP 里没有 `.git`。** 下载来的是"当前快照"，改完没法提交；要改就得 clone 或走连接器路线。
3. **用 Git LFS 存的大文件在 ZIP 里只有指针。** 需要装 `git lfs` 才能取到真文件，下载的 ZIP 里那是个几十字节的文本。

---

## 四、首次克隆（约 5 分钟，只需做一次）

### D1　建一个固定的本地文件夹

建议建在 `D:\GreenHouse`（不要放桌面，不要放中文路径，不要放 OneDrive 同步目录）。

> **注意｜路径三条禁忌**
>
> ① 含中文（容易出现各种编码报错）② 含空格 ③ 在 OneDrive / 坚果云里（同步冲突会把 `.git` 目录搞坏）。

### D2　在文件夹里打开 Git Bash

进入 `D:\GreenHouse`，在空白处右键 → **Show more options** → **Git Bash Here**。

### D3　克隆仓库

```bash
git clone https://github.com/你的用户名/greenhouse-project.git
```

回车后会弹出浏览器窗口，让你登录 GitHub——这就是凭据管理器在工作。

### D4　浏览器里点授权

1. 弹出的窗口里点 **Continue** / 选择 **Sign in with your browser**
2. 输入 GitHub 账号密码 → 输入 2FA 的 6 位验证码
3. 页面问是否授权 **Git Credential Manager** → 点 **Authorize**
4. 看到 **Authentication complete** 就可以关掉浏览器

回到终端，应该看到：

```
Cloning into 'greenhouse-project'...
remote: Enumerating objects: 5, done.
...（若干行）...
Resolving deltas: 100% (2/2), done.
```

> **完成｜到这里，认证已经永久搞定**
>
> 凭据存在 Windows 凭据管理器里，以后 push 都不会再让你登录。**整个流程不需要手工创建 token，也不要把密码或 token 贴给任何 AI 助手。**

> **注意｜浏览器没弹出来怎么办**
>
> 在 Git Bash 里敲一次：
>
> ```bash
> git config --global credential.helper manager
> ```
>
> 然后再 `git push` 任意内容触发弹窗。仍然不弹，就手动打开 **控制面板 → 用户帐户 → 凭据管理器 → Windows 凭据**，删掉所有 `git:https://github.com` 条目后重试。

---

## 五、日常五步：每次干活都走这条

这一节是全文最该背下来的部分。**无论你改的是代码、文档还是图片，流程完全一样。**

```
① 同步 main  →  ② 开自己分支  →  ③ 改文件  →  ④ 让 Agent 提交  →  ⑤ 推送 + 开 PR
```

### E1　先切回主干、拉最新代码

```bash
cd /d/GreenHouse/greenhouse-project
git switch main
git pull
```

第一条是进入仓库目录（`/d/` 在 Git Bash 里代表 D 盘）。第二条切到 main 分支。第三条把别人的最新改动拉下来。

> **注意｜不先 pull 就开分支，是最常见的操作失误**
>
> 你在旧版本上改了两小时，推的时候才发现别人也改过同一文件，白干。每天开工第一件事就是这三行。

### E2　开一条属于你自己的分支

```bash
git switch -c r2-cloud-1021
```

分支名规则见第九节：`角色-模块-日期`。这条命令会新建分支并切过去，**你之后的改动都在自己的副本上，不会影响任何人的 main**。

如果你的 Git 版本较老，`git switch -c` 可能不认，换成 `git checkout -b r2-cloud-1021`，效果一样。

### E3　改文件（正常用编辑器）

用 VS Code、记事本、Word 都行，正常改。改完保存即可，不用在终端做任何操作。

### E4　让 Agent 帮你提交（见第六节）

不用自己背 commit 命令，把活交给 WorkBuddy 或豆包工作。

### E5　推送到 GitHub

```bash
git push -u origin r2-cloud-1021
```

第一次推这个分支要带 `-u origin 分支名`，Git 会记住对应关系；以后同一条分支上再推，直接 `git push` 就行。

### E6　在网页上开 PR，请组长合并

1. 推送成功后，打开仓库网页
2. 页面顶部会出现一条黄色横条，右边是绿色按钮 **Compare & pull request** → 点它
3. **Title** 填清做了什么，如 `[R2] 打通 MQTT 上行与远程浇水`
4. 下方大框写细节：改了什么、怎么验证的、有没有遗留问题
5. 点绿色 **Create pull request**
6. 把链接发到群里，请组长合并

组长合并时点 **Merge pull request** → **Confirm merge** → 再点 **Delete branch**（分支合完就没用了，删掉保持干净）。

> **提示｜合完之后你自己还得同步一次**
>
> 下一次开工前回到 E1 的三行命令（`git switch main` + `git pull`），把合并进主干的内容拉回本地，否则你的本地还是旧的。

---

## 六、用 Agent 提交代码

两个工具都能干这件事，纪律完全一样。先记住三条铁律，再看具体怎么点。

> **提示｜工具配置（2026-10-20 晚更新）**
>
> **现状**：三人已装 WorkBuddy 并连上 GitHub（你 + 两位组员），第四位跟上即可——四人统一一个工具，出问题时互相能接话，比混装两套工具好排查。
>
> **但连接器不等于本机 Git。** WorkBuddy 的 GitHub 连接器走 API：能建分支、改仓库里的文件、直接开 PR，但它碰不到你电脑上的文件夹；本机 `git push` 用的是安装 Git 时带的凭据管理器。这是两套东西，按活分路线：
>
> - **只交文档、图片、报告、PPT** → 连接器直连就够，本机可以不装 Git，本文第二、四章跳过；
> - **要跑代码、编译固件、重出 STL** → 必须本地 clone + `git push`，第五章照走。
>
> 两条路线最后都落到「同一条分支 + 同一个 PR」，所以四个人用不同路线也不冲突。

### 6.1　三条铁律（写在最前面，因为它比操作步骤重要）

> **禁止｜铁律一：先看清单，再点同意**
>
> Agent 提交前必须先把「将要提交哪些文件、共几个、有没有可疑文件」列给你看，**你亲口确认后才允许 commit / push**。没给清单就直接推的，一律叫停。

> **禁止｜铁律二：禁止三条危险命令**
>
> `git push -f`（强推，会覆盖别人）、`git reset --hard`（丢弃所有本地改动）、`rm` / `del`（删文件）。**任何一条出现，立刻停手**，改让人工判断。

> **禁止｜铁律三：密码、token、密钥永远不进对话**
>
> 不要把 GitHub 密码、token、WiFi 密码贴进任何 AI 对话框。Agent 只需要能跑 git，不需要知道你的账号密码——凭据管理器已经在系统层面处理了。

### 6.2　WorkBuddy：直接说人话

#### F1　打开 WorkBuddy，选中这个项目文件夹

把工作目录指到 `D:\GreenHouse\greenhouse-project`，这样它能直接读写仓库里的文件、直接执行 git 命令。

#### F2　粘贴这段指令（照抄，只改括号里的）

```text
我在 D:\GreenHouse\greenhouse-project 这个仓库里，
当前分支是 r2-cloud-1021。

请按顺序做：
1. 先执行 git status，把「将要提交的文件清单」列给我看，
   包括新增/修改/删除三类，一个都别漏。
2. 如果有 .env、config.h、docs/private/、任何 .key/.pem、
   或者大于 50MB 的文件，单独标红提醒我。
3. 等我回复「同意」之后，再执行 git add 和 git commit，
   提交信息用：feat(r2): 打通 MQTT 上行与远程浇水
4. commit 完先别 push，把提交结果给我看，我再让你推。
```

这段的关键是第 4 条——把 push 和 commit 拆成两步，中间留一个人工确认点。

#### F3　按它的清单逐条看，然后回「同意」

看三件事：**有没有你不认识的文件**、**有没有上面第 2 条点名的敏感文件**、**改动数量对不对**（你只改了 2 个文件，它列出 15 个，说明有别的程序在写文件，要查）。

确认无误就回：`同意，提交并推送`。

### 6.3　豆包工作：工作模式 + 授权操作电脑

> **提示｜先说清产品名**
>
> 我核实了一下：字节在 **2026-08-25** 把原来的"办公任务模式"升级成独立产品，叫 **豆包工作**（不是"豆包办公"）。下载豆包电脑版即可使用，新用户有 30 天订阅。**界面按钮名随版本变化**，下面写的是动作要点，你按实际界面对应着点。

#### F4　切到「工作」模式，把项目文件夹加进来

打开豆包桌面版，在对话/工作之间切到 **工作模式**，用 **添加本地文件夹**（或新建项目）把 `D:\GreenHouse\greenhouse-project` 加进去。

#### F5　发同一个任务，等它申请「操作电脑」授权

把 F2 那段指令原样粘进去。因为它要在终端里敲 git，会弹出一个 **操作本地电脑** 的授权请求——点允许。

它会自己打开终端执行，你在旁边看着就行，**随时可以暂停或接管**。

#### F6　同样在「列出清单」那一步停下来确认

纪律和 WorkBuddy 一模一样：清单没出来不给同意，push 前再看一眼。

> **注意｜豆包工作用不了的时候**
>
> 订阅到期后部分能力会受限。这时候两个选择：换回 WorkBuddy，或者直接手动敲 6.4 的四行命令——**手动路径永远可用，不依赖任何订阅**。

### 6.4　手动兜底：Agent 不可用时就敲这四行

```bash
git status                          # 先看清单，逐条核对
git add -A                          # 把所有改动加入暂存
git commit -m "feat(r2): 打通 MQTT 上行与远程浇水"
git push                            # 分支已带 -u 过，直接推
```

提交信息格式统一用 `类型(角色): 中文说明`。类型取 feat（新功能）/ fix（修问题）/ docs（文档）/ chore（杂务）。

---

### 6.5　连接器路线：本机不装 Git 也能交一次改动

如果你已经装了 Git 并 clone 过仓库，走第五章就行，不必走这条——**两条路线可以并存于同一个仓库**，只是同一个文件别交替改（见第零节）。

适用：Markdown、报告、代码文本、小尺寸图片，**单文件 ≤1 MB**。

六个动作都在对话里说，不用记命令：

1. **先读现状**：让它读 main 上目标文件的内容和 sha
2. **建分支**：从 main 开一条你自己的分支
3. **写入**：把本地文件内容写到该分支，带上第 1 步的 sha
4. **开 PR**：标题标角色，正文写清改了哪几段
5. **请组长合并**：组长在对话里说"合并这个 PR"，或去网页点 Merge
6. **同步本地**：若你本地也留了一份副本，手动覆盖成仓库最新版（纯连接器用户没有本地仓库，可跳过）

四条硬限制（来自 GitHub Contents API 的公开约束，不是推测）：

| 限制 | 具体表现 | 影响谁 |
|---|---|---|
| 单文件 1 MB 上限 | Contents API 只接受 ≤1MB 的文件 | STL、PPT、PDF、视频、大图**全部走不通**，必须本机 Git |
| 更新必须带 sha | 改已有文件要先读它的 blob sha，缺了报 422 | 读了要马上写，中间被别人改过就得重读 |
| 一次一个文件 | 一次请求 = 一个文件 = 一个 commit | 改 10 个文件会生成 10 个提交，PR 很难看 |
| 无自动合并 | 两人基于同一旧版本改同一文件时，后写的覆盖先写的 | **按文件分工，不改别人的文件** |

对话模板（照抄，只改路径与标题）：

```text
仓库：owner/greenhouse-project

请按顺序：
1. 读 main 分支上 docs/报告.md 的内容和 sha，把 sha 报给我。
2. 从 main 新建分支 r4-docs-1021。
3. 用我本地这份文件的内容更新该分支上的 docs/报告.md，
   带上第 1 步的 sha。
4. 基于 r4-docs-1021 开 PR，标题「[R4] 报告第三节补数据」，
   正文写：改了哪几段、为什么改。
5. 开完把 PR 链接给我，先别合并。
```

第 1 步与第 3 步之间不要隔太久——sha 一旦过期，写入会失败，得重新读一遍。

---

## 七、提交前安全检查（不许踩的红线）

这一节是给我们这个项目量身写的——花房仓库里确实存在不能公开的东西。

### 7.1　绝对不能进仓库的东西

| 东西                                   | 为什么                                      | 正确做法                                 |
| ------------------------------------ | ---------------------------------------- | ------------------------------------ |
| 真实姓名、学号、手机号                          | 会永久留在提交历史里，爬虫会抓。我们的 `docs/private/` 就是这类 | 整个目录写进 .gitignore，只在本地留              |
| `config.h` 里的真实 WiFi 密码 / 巴法云 UID    | 公开后别人能直接连你的设备、发指令                        | 仓库里只放占位符版本，真值另存 `config.local.h` 并忽略 |
| 巴法云控制台截图（含私钥）                        | 截图里的 UID 就是凭证                            | 素材目录整体忽略，或截图前打码                      |
| GitHub 密码 / token / 任何 `.key` `.pem` | 等于把门钥匙贴门上                                | 永不入库，永不发群里，永不贴给 AI                   |
| 大视频（>50MB 的 mp4）                     | 超过 100MB 会被 GitHub 直接拒收，且历史里删不干净         | 写进 .gitignore，视频放网盘/群文件              |

### 7.2　.gitignore 模板（仓库根目录新建这个文件）

```gitignore
# ---- 密钥与私有信息 ----
.env
.env.*
config.local.h
docs/private/
素材/巴法云配置/
*.key
*.pem

# ---- 大文件 ----
*.mp4
*.mov
*.zip

# ---- 系统垃圾 ----
Thumbs.db
desktop.ini
.DS_Store

# ---- Python / 临时 ----
__pycache__/
*.pyc
~$*
```


> **注意｜注意：`config.h` 本身不要整体忽略**
>
> 我们仓库里的 `config.h` 是**占位符版本**，是给别人编译用的，必须留在库里。要忽略的是你填了真值的那份副本——所以约定叫 `config.local.h`，只忽略它。

### 7.3　每次提交前，30 秒自查五条

- [ ] 清单里有没有 `docs/private/` 开头的路径
- [ ] 有没有截图文件名带"配置""控制台""UID"字样
- [ ] 有没有 `.env`、`.key`、`.pem`
- [ ] 有没有单个超过 50MB 的文件
- [ ] commit 信息里有没有出现学号或手机号

五条全过，才点同意。

### 7.4　万一已经推上去了

> **禁止｜顺序不能颠倒**
>
> 1. **先作废凭证**：如果是密码/UID 泄露，立刻去对应平台改密码、重置 UID。**文件删了但凭证还有效，等于没删。**
> 2. 再清文件：`git rm --cached 文件名` → 提交 → 推送（这只让文件不再被追踪）
> 3. 如果文件已经在历史里、且仓库是公开的：把仓库改私有，然后找组长处理历史（需要重写历史，属于高阶操作，不要自己动手）

---

## 八、9 种常见报错速查

| 报错原文（关键片段） | 意思 | 怎么办 |
|---|---|---|
| `fatal: not a git repository` | 当前终端不在仓库目录里 | 敲 `cd /d/GreenHouse/greenhouse-project` 再试 |
| `Please tell me who you are`<br>`Author identity unknown` | 没配署名，Git 不知道这次提交算谁的 | 回到 B4，把那两条 `git config --global user.name / user.email` 敲一遍 |
| `Authentication failed`<br>或一直弹窗要求登录 | 缓存的凭据过期或错了 | 控制面板 → 用户帐户 → 凭据管理器 → Windows 凭据 → 删掉所有 `git:https://github.com` 条目 → 重试 push |
| `Updates were rejected because the remote contains work that you do not have locally` | 别人比你先推了，你本地落后 | `git pull --rebase` 然后重新 push |
| `! [rejected] ... (non-fast-forward)` | 同上，本地和远端分叉了 | 同上。**不要用 `git push -f` 解决** |
| `warning: LF will be replaced by CRLF` | 换行符提示，只是警告 | 不用管，不影响提交 |
| push 成功但网页上没有 **Compare & pull request** 按钮 | 你可能推到了 main，而不是自己的分支 | 敲 `git branch --show-current` 看当前分支名，是 `main` 就说明推错地方了 |
| `remote: error: File xxx is 105.00 MB; this exceeds GitHub's file size limit of 100.00 MB` | 文件太大，GitHub 拒收 | 把该文件加进 .gitignore，再 `git rm --cached 文件名`，重新提交 |
| 中文文件名显示成 `"\344\270\255\346\226\207"` | Git 在转义非 ASCII 文件名 | `git config --global core.quotepath false` |

---

## 九、四个人的分支怎么命名

对应 `docs/花房4人分工方案_2026-10-20.md` 里的角色划分，一人一条主线分支，别混。

| 角色 | 分支命名 | 干什么活 |
|---|---|---|
| **R1** 系统负责人 | `r1-firmware` | 固件、标定参数、集成联调 |
| **R2** 上云与数据 | `r2-cloud` | MQTT、小程序、数据导出 |
| **R3** 结构与打印 | `r3-print` | 切片参数、打印日志、试装偏差 |
| **R4** 文档与影像 | `r4-docs` | 报告、PPT、素材索引 |

同一个人同一模块改好几轮，就在后面加日期：`r2-cloud-1021`、`r2-cloud-1028`。合并后旧分支删掉，下次再从最新 main 开新的。

> **提示｜为什么一人一条分支，而不是每次一个功能分支**
>
> 功能分支更规范，但对零基础的同学来说分支太多会乱。一人一条、按日期递进，够用且好记；等大家熟练了再升级成"一个任务一条分支"。

---

## 十、一页速查（建议打印贴显示器旁）

| 场景 | 命令 / 动作 |
|---|---|
| 每天开工 | `cd /d/GreenHouse/greenhouse-project`<br>`git switch main`<br>`git pull` |
| 开今天的分支 | `git switch -c r2-cloud-1021` |
| 改完让 Agent 提交 | 粘贴 F2 那段指令 → 看清单 → 回「同意」 |
| 推送 | `git push -u origin r2-cloud-1021` |
| 开 PR | 网页 → 黄色横条 **Compare & pull request** → 填标题 → **Create pull request** → 发群 |
| 组长合并 | **Merge pull request** → **Confirm merge** → **Delete branch** |
| 完全不靠 Agent | `git status` → `git add -A` → `git commit -m "feat(r2): 说明"` → `git push` |

**三条不许破的规矩**

| # | 规矩 |
|---|---|
| 1 | 提交前必须看文件清单，确认后才同意 |
| 2 | 永不用 `git push -f`、`git reset --hard`、删文件命令 |
| 3 | 密码 / token / 学号 / 私钥截图，永不进仓库、永不贴给 AI |

---

## 十一、macOS 用户看这里

这一章替代第**二**章（装 Git）和第四章的终端部分。其余章节的命令与 Windows 完全一样：注册、建库、日常五步、Agent、报错表都能直接照做。

### M1　打开终端

- Spotlight（⌘ + 空格）→ 输入 `Terminal` 或 `终端` → 回车
- 或在 Finder 里：右键文件夹 → **服务** → **新建位于文件夹位置的终端窗口**
- 路径形如 `/Users/你的用户名/GreenHouse`，不是 `D:\`。进目录用 `cd ~/GreenHouse/greenhouse-project`

### M2　装 Git：先跑一次 `git --version`

Mac 自带 git，但第一次执行会弹窗要求安装 **Xcode Command Line Tools**，点"安装"等几分钟，跑完再执行一次 `git --version`，看到版本号就算好了。这是 Mac 上最常见的"卡住点"，不是出错。

不想等系统弹窗，也可以装 Homebrew 后 `brew install git`（国内网络慢可换镜像源）。

### M3　认证：三选一（Mac 和 Windows 最大的区别）

GitHub 已取消用账号密码做 Git 认证。Windows 上靠 Git 自带的凭据管理器解决，**Mac 自带的 git 没有这个能力**，必须选下面一种：

| 方案 | 怎么做 | 适合 |
|---|---|---|
| **GCM（推荐）** | `brew install --cask git-credential-manager`，之后 push 弹浏览器授权 | 有 Homebrew，想要和 Windows 一样的"点一下就完事" |
| **GitHub CLI** | `brew install gh` → `gh auth login` → 选 HTTPS → 问是否用 GitHub 凭据认证选 **Y** → 浏览器授权 | 想一条命令搞定，还能用 `gh auth status` 自查 |
| **PAT + 钥匙串** | 建 token，再 `git config --global credential.helper osxkeychain`；push 时用户名填 GitHub 用户名、密码粘 token | 没装 Homebrew |

**PAT 怎么建**（只有第三种方案需要）：头像 → **Settings** → **Developer settings** → **Personal access tokens** → **Fine-grained tokens** → Generate new token → 选仓库 → Repository permissions 里把 **Contents 设为 Read and write**（`git push` 需要的就这一条）→ 设过期日 → 生成后立刻复制，只显示一次。

> **禁止｜token 等同密码**
>
> 不写进任何文件、不贴给 AI、不写进 remote URL（写进 URL 会以明文躺在 `.git/config` 里）。只粘到终端提示的密码位置。

**Mac 上的最短落地顺序**（从最省事往下排）：

| 顺序 | 做什么 | 一句话提交什么时候能用 |
|---|---|---|
| 1 | 只交文档 → **走连接器**，零安装 | 立刻能用，模板里的路径换成 `/Users/…` |
| 2 | 要交代码 → `brew install gh` + `gh auth login`（一条命令配完，还能 `gh auth status` 自查） | 配完立刻 |
| 3 | 有 Homebrew 但不想装 gh → 装 GCM | 配完立刻 |
| 4 | 没 Homebrew、或 brew 装不上（国内网络） → PAT + osxkeychain | 建完 token 后 |

**第 2 档怎么交给 Agent 做**（复制下面这段，粘给 Agent 即可）：

```text
检查本机环境：执行 brew --version 和 gh --version，把结果告我。
缺 Homebrew 就先装 Homebrew；缺 gh 就执行 brew install gh。
装好后执行：
  gh auth login --hostname github.com --git-protocol https --web
把终端里出现的一次性代码（one-time code）原样转述给我，
之后停下来等我在浏览器里完成登录和 2FA 授权，不要自己猜结果。
我授权完成后，你再执行 gh auth status 确认登录状态，
并执行 git config --get credential.https://github.com.helper
告诉我 gh 是否已经接管 git 凭据。
```

两点说明：

- **浏览器那一步必须本人做**（要输密码 + 2FA），Agent 代不了；它能做的是装、跑命令、念代码、验结果。
- `gh auth login` 成功后会自动把 gh 配成 git 的凭据辅助，**之后 `git push` 不用再登录**——这就是它比 PAT 省事的地方。

### M4　三条 Mac 独有注意点

1. **行尾**：Mac 是 LF，Windows 是 CRLF。不统一的话，同一文件两边来回改会显示"整份都变了"。执行 `git config --global core.autocrlf input`（Mac 默认值，确认一下），并在仓库根加 `.gitattributes`，写一行 `* text=auto`。
2. **文件名大小写**：macOS 磁盘默认不区分大小写，把 `readme.md` 改成 `README.md`，git 会认为文件没变。改名必须用 `git mv readme.md README.md`。
3. **不要放 iCloud 云盘或桌面同步目录**：等同于 Windows 放 OneDrive，同步冲突会破坏 `.git` 目录。用 `~/Dev/greenhouse-project` 这类纯本地路径。
4. **首次权限弹窗**：Mac 上第一次让 Agent 操作终端或读写项目文件夹时，系统会弹"允许访问 / 自动化"授权——**必须点允许**，否则命令跑不起来（这一步只在第一次出现，一次授权长期有效）。

### M5　凭据出问题怎么清

Windows 是"控制面板 → 凭据管理器 → Windows 凭据"；Mac 换成**钥匙串访问**：Spotlight 搜 `Keychain Access` → 搜索 `github.com` → 删掉那条"互联网密码"。

命令行版：执行 `git credential-osxkeychain erase`，然后依次输入 `host=github.com`、`protocol=https`，连按两次回车，无任何输出即成功。

### M6　两条补充

- Finder 里看不到 `.git` 目录是正常的，按 **⌘ + Shift + .** 显示隐藏文件
- WorkBuddy 有 macOS 客户端，连接器路线与 Windows 一致；**只走连接器路线的 Mac 用户连 git 都不用装**，1MB 限制与操作系统无关

---

## 附：写这份手册时核实过的事实

- Git for Windows 自带 Git Credential Manager（GCM），「不必手动创建并存储 personal access token，GCM 会代为管理身份验证，包括 2FA」，凭据存入 Windows 凭据管理器，至少需 Git 2.29 以上版本（GitHub 官方文档）。**所以本文全流程不含手工造 token 的步骤。**
- GitHub 自 2023 年 3 月起要求所有在 GitHub.com 上贡献代码的用户启用 2FA；未在 45 天注册期加 7 天宽限内启用，将无法访问。官方推荐 TOTP App 为主要方式（GitHub 官方文档）。
- 「豆包工作」于 2026-08-25 正式发布，由原"办公任务模式"升级为独立产品，官方描述其「获得用户授权后可操作本地电脑及浏览器」；豆包电脑版内可直接使用，新用户 30 天订阅（央广网、腾讯新闻等公开报道）。**界面按钮名随版本变化，本文按动作要点描述。**
- 私有仓库的分支保护规则在不同套餐下可见性不一致，本文未把"禁止直推 main"写成必做步骤，改为靠约定 + PR 流程约束。
- **macOS 认证**：GitHub 已移除 Git 操作的口令认证，macOS 自带的 git 只提供 `osxkeychain` 辅助（存的是密码/令牌），因此需另装 GCM、或用 GitHub CLI 登录、或手工建 PAT；官方文档同时说明「更新 macOS 钥匙串凭据」仅适用于手动配置 PAT 的用户，并推荐改用 SSH 或 GCM。

---

本手册不含任何真实账号、密钥或个人信息；示例中的用户名、邮箱、分支名均为占位。
