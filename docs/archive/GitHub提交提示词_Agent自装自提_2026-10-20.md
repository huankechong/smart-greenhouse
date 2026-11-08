# 一句话提示词 · 让 WorkBuddy 自己装 Git 并用 git 提交到 GitHub

**日期** 2026-10-20　·　**适用** Windows + WorkBuddy　·　**认证方式** Git Credential Manager 浏览器授权（不落 token 明文）

---

## 一、直接复制这段（主提示词）

> 请你检查这台电脑是否具备用 git 向 GitHub 提交代码的完整条件，缺什么就自己装/自己补，然后帮我把当前目录的改动提交并推送到 GitHub。
>
> 依次执行：
>
> 1. **查 Git**：`git --version`。若提示不是命令，用 `winget install --id Git.Git -e` 安装，装完重开终端再验证。
> 2. **查身份**：`git config --global user.name` 和 `git config --global user.email`。若为空，用 `git config --global user.name "<我的GitHub用户名>"` 和 `git config --global user.email "<我的GitHub noreply 邮箱>"` 补上（GitHub 设置页 Emails 里的 `ID+用户名@users.noreply.github.com`）。**不要编造**，缺失就问我。
> 3. **查凭据**：先 `git ls-remote origin` 试一次。通了就跳过认证这步；不通则跑 `git credential-manager github login`（或 `git-credential-manager github login`），它会弹浏览器让我点授权，**不要让我手动贴 token**，也**不要把 token 写进任何文件**。
> 4. **看状态**：`git status` + `git diff --stat` 告诉我改了什么，**先给我看再动手**。
> 5. **提交**：`git add <明确的文件>`（不要 `git add .` 盲扫），`git commit -m "<中文说明>"`，然后 `git push origin <当前分支>`。
> 6. **自检**：push 后跑 `git status` 和 `git log --oneline -3`，把结果贴给我；失败了把报错原文和原因一起说，不要重试超过 2 次。

---

## 二、为什么是这六条（每条对应一个实测过的坑）

| 步骤       | 对应的真实问题（2026-10-20 实测）                                                                                                  |
| -------- | ----------------------------------------------------------------------------------------------------------------------- |
| 1 查 Git  | 本机已有 2.55.0（`C:\Program Files\Git` 与 WorkBuddy PortableGit 两份），**无需重装**；但换台新机器就得先装                                      |
| 2 查身份    | **全局 user.name/email 为空**，只有当前仓库有 local 配置。在 `/tmp` 空仓库 `git commit` 直接报 `Author identity unknown` —— 这是最常见的"AI 提交失败"真因 |
| 3 查凭据    | GCM 已授权账号 `huankechong`，`ls-remote` 与 `push --dry-run` 均通过。**token 已在 Windows 凭据管理器里，不需要也不该再贴一次**                       |
| 4 先看状态   | 本仓库当前就有 4 个已改文件 + 3 个未跟踪文件，盲 `git add .` 容易把不该入库的混进去                                                                    |
| 5 明确 add | `.gitignore` 已排除 `docs/private/`、`output/`、`.workbuddy/`、`outputs/素材/_敏感_不入库/截图备份_*/`（含个人信息），靠 ignore 兜底但不等于安全                     |
| 6 自检     | `git push` 成功≠你要的文件都上去了，必须读回 `git log` 核对 sha 和说明                                                                       |

---

## 三、三个变体

### 变体 A：装 GitHub CLI（要开 PR / 建仓库时才需要）

> 在上面第 1 步之后加一步：`winget install --id GitHub.cli -e`，然后 `gh auth login`（选 GitHub.com → HTTPS → 浏览器授权）。装完用 `gh repo create` 建私有仓库、`gh pr create` 开 PR。**注意：本机已有 GCM 认证，`gh` 是锦上添花，不是必需。**

### 变体 B：走 SSH（不想每次依赖 Windows 凭据管理器时）

> 用 `ssh-keygen -t ed25519 -C "你的GitHub邮箱"` 生成密钥，把公钥贴到 GitHub → Settings → SSH and GPG keys，然后 `git remote set-url origin git@github.com:用户名/仓库名.git`，之后 push 免密。**私钥只留在本机，绝不进仓库。**

### 变体 C：CI / 脚本里用（不弹浏览器）

> 读环境变量 `GITHUB_TOKEN`，用 `git -c http.extraheader="Authorization: Bearer $GITHUB_TOKEN" push`。**token 只从环境变量读，绝不硬编码进脚本或配置。**

---

## 四、安全红线（写进任何提交任务都别破）

- 不编造用户名、邮箱、token；缺什么问，别猜
- token / 私钥 / 学号 / 手机号 / 住址 一律不写进仓库文件
- 含个人信息的目录（`docs/private/`、`output/`、截图备份）不入库
- 提交前先给 `git status` 摘要，**得到确认再 commit**
- 大文件（STL / PDF / 视频）超过 100 MB 提醒用 LFS
- push 失败最多重试 2 次，报错原文 + 原因一起报，不静默吞掉

---

## 五、现状速查（2026-10-20 实测，本机已就绪）

```
git            2.55.0.windows.3   C:\Program Files\Git + WorkBuddy PortableGit
remote         https://github.com/huankechong/smart-greenhouse.git
branch         main（与 origin/main 同步，最新 d10c113）
credential     Git Credential Manager 2.9.0，已授权 huankechong
git config     global user.name     = huankechong                            ← 已补
git config     global user.email    = huankechong@users.noreply.github.com   ← 已补
gh CLI         未安装（当前不需要）
ssh 密钥       无（当前走 HTTPS，不需要）
```

**补齐验证（22:50 实测）**：新建空仓库 `git init` → `git commit` 成功，作者正确回读为  
`huankechong <huankechong@users.noreply.github.com>`，不再报 `Author identity unknown`。

---

## 六、给 Agent 的补充约束（实测后追加）

1. **提交身份已全局配好，不要重复 `git config`**——尤其不要用 `git config --local` 覆盖，写成 local 反而会让新仓库继承不到。
2. **仓库根目录 = `D:/Documents/workbuddydocument/2026-10-17-08-59-13`**，一切路径以它为基准（`docs/…` / `outputs/…`），不要写 `../`。
3. **`.gitignore` 已排除**：`docs/private/`、`output/`、`.workbuddy/`、`outputs/素材/_敏感_不入库/截图备份_*/`、`outputs/素材/_敏感_不入库/截图整理_*/`（含个人信息的目录）。`git add` 时仍要显式列文件，不要 `git add .`。
4. **不要用 `gh`**：本机认证由 GCM 接管，`gh` 未安装；`git push` 即可。
5. **不要重装 Git**：已装两份，版本 2.55.0。
6. **提交前必看 `git status`**：当前工作区常有别人/自己未提交的改动，盲提交会带进不该入库的文件。
7. **提交信息写中文**，格式：`<类型>: <一句话说明>`，例如 `docs: 补 GitHub 提交提示词文档`。
8. **push 后必须回读** `git log --oneline -3` 与 `git status`，把 sha 报给领导。
