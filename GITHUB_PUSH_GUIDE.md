# GitHub 推送指南

## 步骤 1：在 GitHub 创建仓库

1. 打开 https://github.com/new
2. 仓库名称：`geo-visibility-diagnostician`
3. 描述：`GEO Visibility Diagnostician — AI-powered brand diagnosis tool for Generative Engine Optimization`
4. 可见性：Public（推荐）或 Private
5. **不要**勾选 "Initialize this repository with a README"（我们已有 README）
6. 点击 **Create repository**

## 步骤 2：推送本地代码

在终端执行：

```bash
cd /Users/zhongwentuo/Desktop/WenTuo_kimi/WorkBuddy_Dify/GEO可见度诊断师

# 设置你的 GitHub 用户名和邮箱（如果还没设置）
git config user.name "Your GitHub Username"
git config user.email "your.email@example.com"

# 添加远程仓库（替换 YOUR_USERNAME 为你的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/geo-visibility-diagnostician.git

# 推送
git branch -M main
git push -u origin main
```

## 步骤 3：验证

打开 `https://github.com/YOUR_USERNAME/geo-visibility-diagnostician`

确认：
- [ ] README.md 显示正常（英文）
- [ ] LICENSE 文件可见
- [ ] docs/ 目录中有 PRD.md、IMPLEMENTATION.md 等
- [ ] 没有 .env 文件（敏感信息）
- [ ] 没有 venv/ 目录

## 步骤 4：设置仓库信息（可选）

在 GitHub 仓库页面：
- Settings → About → 添加 Topics: `geo`, `ai-search`, `vibe-coding`, `brand-diagnosis`, `mcp`, `langgraph`
- Settings → General → 勾选 "Issues" 和 "Discussions"
- 上传一个封面图（可选）

## 推送后

完成推送后，V1.0 就正式发布了！接下来可以：
1. 创建 Release Tag: `v1.0.0`
2. 安装 Kimi Work Skill（下一步）
3. 开始 V2.0 开发
