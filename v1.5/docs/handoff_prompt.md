# GEO 可见度诊断师 V1.5 — 项目交接说明

## 一、项目背景

GEO 可见度诊断师是一个评估品牌在 AI 搜索平台（ChatGPT、豆包、Perplexity 等）中可见度的工具。
- **当前版本**：V1.5（FastAPI 后端 + 前端界面）
- **项目路径**：解压后的 `v1.5/` 目录
- **技术栈**：FastAPI 0.128.8 + 纯 HTML/JS 前端（Tailwind CSS CDN + DaisyUI CDN）
- **开发环境**：Python 3.9+

## 二、已完成的工作

### Phase 1：FastAPI 后端 ✅
- **文件**：`src/api.py`
- **功能**：
  - 8 阶段诊断流水线（用户画像 → 基建评估 → 竞品分析 → AI 搜索测试 → GEO 效果汇总 → 舆情扫描 → 综合总览 → AIVO 评分）
  - 模拟诊断端点（使用 `run_mock_diagnosis`）
  - 端点列表：
    - `GET /health` — 健康检查
    - `POST /diagnose` — 真实诊断
    - `POST /diagnose/mock` — 模拟诊断（前端当前使用）
    - `GET /diagnosis/{id}` — 获取诊断结果
    - `GET /stream/{id}` — SSE 流式输出
- **启动方式**：
  ```bash
  cd v1.5 && python -m uvicorn src.api:app --reload --port 8000
  ```

### Phase 2：前端界面 ✅
- **文件**：`src/static/index.html`、`css/style.css`、`js/app.js`
- **已实现**：
  - 对话式 UI（DaisyUI chat bubble 组件）
  - 品牌输入表单（品牌名、产品类型、官网、AI 引擎选择）
  - 底部快捷芯片（听力熊、小度、阿尔法蛋）
  - 模拟诊断流程（阶段卡片进度、报告卡片、AIVO 评分、维度条形图）
  - 帮助弹窗（DaisyUI modal）
  - 毛玻璃顶部导航和底部快捷栏

## 三、文件结构

```
v1.5/
├── docs/
│   ├── PRD.md              # V1.5 产品需求（详细功能定义）
│   ├── handoff_v1.5.md     # 原始交接文档（从 WorkBuddy 导入）
│   ├── plan.md             # 执行计划（阶段划分）
│   └── plan_v1.5_phase1.md # Phase 1 详细计划
├── desgn/
│   └── DESIGN.md           # 设计文档（UI/UX 规范）
├── src/
│   ├── api.py              # FastAPI 后端主文件
│   └── static/
│       ├── index.html      # 前端页面（单页应用）
│       ├── css/style.css   # 自定义样式 + DaisyUI 颜色覆盖
│       └── js/app.js       # 前端逻辑（模拟诊断、渲染、交互）
└── tests/                  # 测试目录（待补充）
```

## 四、关键注意事项（踩坑记录）

### 1. DaisyUI 颜色覆盖问题 ⚠️

DaisyUI 4 使用 OKLCH 颜色格式，`[data-theme="light"]` 中的 CSS 变量优先级高于 `:root`。

**问题**：直接设置 `:root { --s: #f1f5f9; }` 不生效，因为 DaisyUI 在 `html[data-theme="light"]` 中使用了 OKLCH 值。

**解决方案**：`style.css` 中使用了 `!important` 强制覆盖组件颜色：
```css
.chat-bubble-primary {
  background-color: #0EA5E9 !important;
  color: #ffffff !important;
}
.chat-bubble-secondary {
  background-color: #f1f5f9 !important;
  color: #334155 !important;
  border: 1px solid #e2e8f0 !important;
}
.btn-primary {
  background-color: #0EA5E9 !important;
  border-color: #0EA5E9 !important;
  color: #ffffff !important;
}
```

**如需修改主题色**：直接编辑 `style.css` 中这些硬编码的颜色值，不要使用 CSS 变量覆盖。

### 2. 前端文件只能通过本地服务器打开 ⚠️

直接双击 `index.html` 用 `file://` 协议打开可能导致：
- 浏览器安全策略限制 JS 模块加载
- CDN 资源（Tailwind、DaisyUI）加载失败

**正确方式**：
```bash
cd v1.5/src/static
python3 -m http.server 8080
# 浏览器访问 http://localhost:8080
```

### 3. 模拟诊断 vs 真实诊断 ⚠️

- 当前 `app.js` 中调用的是 `/diagnose/mock`（返回模拟数据）
- 后端 `api.py` 中已实现真实的 8 阶段流水线（`run_diagnosis` 函数），但前端尚未接入
- **下一步**：将前端 `fetch('/diagnose/mock')` 改为 `fetch('/diagnose')`

### 4. 帮助弹窗实现

- 使用 DaisyUI `<dialog>` 原生组件
- 点击右上角 ❓ 按钮触发
- 点击「知道了」或背景关闭

### 5. 阶段卡片动画

- 使用自定义 CSS 动画 `fadeInUp` 和 `pulse-soft`
- 阶段图标（⏳）使用 `stage-icon-running` 类添加脉冲动画
- 维度条形图使用 `dim-bar-fill` 类实现宽度过渡动画

## 五、下一步待办（节点 3 & 4）

### 节点 3：前端联通后端（未开始）

- [ ] 将前端 `app.js` 中的模拟数据调用替换为真实后端 API 调用
- [ ] 实现 SSE 流式输出（后端已支持 `GET /stream/{id}`，前端需适配）
- [ ] 处理后端返回的 8 阶段 JSON 数据并渲染到 UI
- [ ] 实现真实的用户输入表单提交（品牌名、产品类型、官网、AI 引擎）
- [ ] 添加加载状态和错误处理
- [ ] 配置 CORS（后端 `api.py` 中已设置 `allow_origins=["*"]`）

### 节点 4：部署（未开始）

- [ ] 选择部署方案（Render / Railway / Vercel + Fly.io 等）
- [ ] 配置生产环境依赖（requirements.txt）
- [ ] 配置域名和 HTTPS
- [ ] 环境变量管理（API 密钥、数据库连接等）

## 六、快速重启步骤

```bash
# 1. 进入项目目录
cd v1.5

# 2. 安装依赖（如未安装）
pip install fastapi uvicorn

# 3. 启动后端（终端 1）
python -m uvicorn src.api:app --reload --port 8000

# 4. 启动前端（终端 2）
cd src/static
python3 -m http.server 8080

# 5. 浏览器访问
# http://localhost:8080

# 6. 测试后端健康检查
curl http://localhost:8000/health
```

## 七、关键代码速查

### 后端入口
- `src/api.py` 第 1-20 行：FastAPI 应用实例和 CORS 配置
- `src/api.py` 第 100-150 行：`run_mock_diagnosis()` 模拟诊断函数
- `src/api.py` 第 50-98 行：`run_diagnosis()` 真实诊断函数（待前端接入）

### 前端入口
- `src/static/index.html`：完整的 DOM 结构，包含 chat bubble、表单、阶段卡片、报告卡片
- `src/static/js/app.js`：
  - `handleDiagnosis()` — 处理诊断按钮点击，调用后端 API
  - `renderStages()` — 渲染 8 个阶段卡片进度
  - `renderReport()` — 渲染 AIVO 评分和维度条形图
  - `renderStageUpdates()` — 动态更新阶段卡片状态

### 样式覆盖
- `src/static/css/style.css` 第 67 行起：DaisyUI 颜色强制覆盖（`!important`）
- `src/static/css/style.css` 第 8-25 行：自定义动画（fadeInUp、pulse-soft）

## 八、外部依赖

| 依赖 | 来源 | 用途 |
|------|------|------|
| Tailwind CSS 3.4 | CDN (`cdn.tailwindcss.com`) | 原子化 CSS 框架 |
| DaisyUI 4.x | CDN (`cdn.jsdelivr.net`) | UI 组件库（chat、badge、btn、progress） |
| Font Awesome | CDN (`cdnjs.cloudflare.com`) | 图标（⏳ 沙漏等） |
| Google Fonts (Inter) | CDN (`fonts.googleapis.com`) | 字体 |

> **注意**：所有前端依赖均为 CDN 引入，无需 npm 安装。如需离线使用，请下载对应 CDN 文件到本地。

## 九、参考资料

- `docs/PRD.md` — 完整产品需求定义
- `docs/handoff_v1.5.md` — 从 WorkBuddy 系统导入的原始交接文档
- `docs/plan.md` — 项目阶段划分和执行计划
- `desgn/DESIGN.md` — UI/UX 设计规范（配色、布局、组件）

---

**请另一个 AI 先阅读以上文档，然后按顺序阅读 `docs/PRD.md`、`docs/handoff_v1.5.md` 和 `desgn/DESIGN.md` 获取完整产品背景，再开始开发工作。**
