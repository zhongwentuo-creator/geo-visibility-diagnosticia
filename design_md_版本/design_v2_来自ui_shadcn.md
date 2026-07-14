# GEO 可见度诊断师 — UI 设计规范

> 本规范用于指导 GEO 可见度诊断报告的 HTML/CSS 实现，也可直接作为其他 AI 修改项目时的设计约束。
>
> 设计方向：以 shadcn/ui 的中性、语义化、可组合和可访问性原则为基础，保留诊断报告需要的数据密度与专业判断感。不要把页面做成紫色渐变 SaaS 仪表盘。

## 1. 设计目标

### 1.1 产品定位

GEO 可见度诊断师是一份帮助用户理解“品牌在 AI 搜索中表现如何、问题在哪里、下一步做什么”的诊断报告。

页面必须优先回答三个问题：

1. 当前总体表现如何？
2. 哪些证据支持这个判断？
3. 用户应该优先采取什么行动？

### 1.2 设计原则

| 原则 | 规则 |
|---|---|
| 语义优先 | 使用 `background`、`foreground`、`primary`、`muted`、`destructive` 等语义 token，不在组件中直接散落 Hex 值 |
| 中性基础 | 以 neutral / zinc 灰阶构成页面，品牌色只用于行动、选中、关键数据和焦点 |
| 证据优先 | 评分必须能回溯到维度、查询、样本或建议，不用装饰性图表代替解释 |
| 组合而非堆叠 | 卡片、表格、徽章、进度条等组件通过清晰层级组合，不给每个区块都套一层卡片 |
| 状态完整 | 设计默认、悬停、聚焦、选中、禁用、加载、空数据、错误和低置信度状态 |
| 克制动效 | 动效服务于状态变化和阅读顺序；支持 `prefers-reduced-motion` |
| 可读可扫 | 标题、数字、辅助说明和证据分层明确；不依赖颜色单独传达信息 |

### 1.3 明确舍弃

- 不使用品牌紫到蓝的全局渐变背景或渐变文字。
- 不使用每个 section 都 `hover` 上浮的卡片效果。
- 不使用没有语义的彩色 pill、装饰性光晕、玻璃拟态或大面积渐变。
- 不把所有指标都做成大数字；数字必须有单位、比较对象或解释。
- 不使用全大写标题；只有极少数 11–12px 的元数据标签可以使用宽字距。

## 2. 视觉基础

### 2.1 主题 token

采用 CSS 变量和语义化 token。组件只引用语义 token，不直接引用色值。默认主题为浅色，提供深色主题；深色主题只覆盖 token，不重写组件结构。

```css
:root {
  --radius: 0.625rem;

  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  --card: oklch(1 0 0);
  --card-foreground: oklch(0.145 0 0);
  --popover: oklch(1 0 0);
  --popover-foreground: oklch(0.145 0 0);

  --primary: oklch(0.205 0 0);
  --primary-foreground: oklch(0.985 0 0);
  --secondary: oklch(0.97 0 0);
  --secondary-foreground: oklch(0.205 0 0);
  --muted: oklch(0.97 0 0);
  --muted-foreground: oklch(0.556 0 0);
  --accent: oklch(0.97 0 0);
  --accent-foreground: oklch(0.205 0 0);

  --destructive: oklch(0.577 0.245 27.325);
  --border: oklch(0.922 0 0);
  --input: oklch(0.922 0 0);
  --ring: oklch(0.708 0 0);

  --chart-1: oklch(0.646 0.222 41.116);
  --chart-2: oklch(0.6 0.118 184.704);
  --chart-3: oklch(0.398 0.07 227.392);
  --chart-4: oklch(0.828 0.189 84.429);
  --chart-5: oklch(0.769 0.188 70.08);

  /* GEO 业务语义色：仅用于状态和评分，不作为装饰色 */
  --success: oklch(0.55 0.14 160);
  --success-foreground: oklch(0.28 0.08 160);
  --warning: oklch(0.75 0.15 85);
  --warning-foreground: oklch(0.35 0.09 65);
  --info: oklch(0.55 0.14 250);
  --info-foreground: oklch(0.3 0.08 250);
}

.dark {
  --background: oklch(0.145 0 0);
  --foreground: oklch(0.985 0 0);
  --card: oklch(0.205 0 0);
  --card-foreground: oklch(0.985 0 0);
  --popover: oklch(0.205 0 0);
  --popover-foreground: oklch(0.985 0 0);
  --primary: oklch(0.922 0 0);
  --primary-foreground: oklch(0.205 0 0);
  --secondary: oklch(0.269 0 0);
  --secondary-foreground: oklch(0.985 0 0);
  --muted: oklch(0.269 0 0);
  --muted-foreground: oklch(0.708 0 0);
  --accent: oklch(0.269 0 0);
  --accent-foreground: oklch(0.985 0 0);
  --border: oklch(1 0 0 / 10%);
  --input: oklch(1 0 0 / 15%);
  --ring: oklch(0.556 0 0);
}
```

### 2.2 Token 使用映射

| Token | 用途 |
|---|---|
| `background / foreground` | 页面底色与默认文字 |
| `card / card-foreground` | 必须抬升的摘要面板、重点区块 |
| `muted / muted-foreground` | 辅助说明、占位、低优先级信息 |
| `primary / primary-foreground` | 主行动、选中项、核心强调 |
| `secondary / secondary-foreground` | 次要行动和弱强调面 |
| `accent / accent-foreground` | 悬停、选中行、当前导航项 |
| `destructive` | 错误、严重风险、破坏性操作 |
| `border / input / ring` | 分隔线、输入框边界、键盘焦点 |
| `success / warning / info` | 诊断状态，必须同时配合文字或图标 |

### 2.3 圆角、阴影与边界

以一个 `--radius` 形成统一尺度，不给每个组件单独发明圆角：

```css
--radius-sm: calc(var(--radius) * 0.6);
--radius-md: calc(var(--radius) * 0.8);
--radius-lg: var(--radius);
--radius-xl: calc(var(--radius) * 1.4);
```

- 输入框、按钮、徽章：`radius-sm` 或 `radius-md`
- 卡片、摘要面板：`radius-lg`
- 弹层、抽屉：`radius-xl`
- 默认使用细边框和层级差，不使用厚重阴影。
- 只有悬浮层、弹窗、菜单可以使用明显阴影。
- 普通内容区不要通过 hover 上浮制造层级。

## 3. 字体与排版

```css
--font-sans: "Inter", "SF Pro Display", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
--font-mono: "SF Mono", "JetBrains Mono", "Fira Code", "Consolas", monospace;
```

| 层级 | 建议 | 规则 |
|---|---:|---|
| 报告标题 | 30–36px / 700 | 只出现一次，说明对象与报告类型 |
| 区块标题 | 18–20px / 600 | 使用 sentence case，不使用全大写 |
| 卡片标题 | 14–16px / 600 | 与说明文本保持清晰间距 |
| 核心数字 | 40–56px / 600 | 使用等宽数字，必须附标签和上下文 |
| 正文 | 14px / 400 | 行高 1.5–1.7，优先可读性 |
| 辅助信息 | 12–13px / 400 | 使用 `muted-foreground` |
| 元数据 | 11–12px / 500 | 只用于时间、来源、样本量等辅助信息 |

- 数字使用 `font-variant-numeric: tabular-nums`。
- 中文正文不强制使用等宽字体。
- 标题最大宽度控制在 20–24 个中文字符，避免长标题形成墙面。

## 4. 布局与信息架构

### 4.1 页面容器

- 最大宽度：`1120px`。
- 桌面端水平内边距：`24px`。
- 移动端水平内边距：`16px`。
- 页面区块间距：`24px`；同一区块内部使用 `8 / 12 / 16 / 24px` 间距尺度。
- 首屏优先放置：报告对象、生成时间、总体分数、结论和第一条行动建议。

### 4.2 页面分区

```text
报告头部
├── 报告对象 / 来源 / 生成时间
├── AIVO 总分 + 评级 + 置信度
└── 一句话结论

诊断摘要
├── 4 个维度指标
├── 关键发现
└── 首要风险

证据与分析
├── 用户画像与搜索意图
├── 基建评估
├── AI 搜索可见性
├── 竞品对标
└── 舆情健康度

行动计划
├── P0 / P1 / P2 建议
├── Quick Wins
└── 路线图与验收条件
```

### 4.3 版式规则

- 重点结论使用横向摘要面板，不把所有内容拆成相同大小的卡片。
- 同类指标使用网格，证据型数据使用表格或列表。
- 图表必须紧邻结论和数据来源，不能单独成为装饰区。
- 复杂表格移动端允许横向滚动，但首列和表头必须保持可理解。
- 当内容为空或置信度不足时，展示原因和下一步，不显示伪造的 0 分。

## 5. 组件规范

### 5.1 Report Header

报告头部不是营销 Hero，而是可信度入口，必须包含：

- 报告类型
- 诊断对象
- 数据来源
- 生成时间
- 总分、评级和评分范围
- 一句话结论

总分使用纯数字或紧凑的分数面板，不使用装饰性圆环。分数旁必须有“满分范围 / 评分等级 / 样本或置信度”中的至少两项。

### 5.2 Card

```text
Card
├── CardHeader
│   ├── CardTitle
│   └── CardDescription
├── CardContent
└── CardFooter（可选：来源、行动、更新时间）
```

- 只有内容需要独立阅读、对比或操作时才使用 Card。
- 不把整个页面的每一个 section 都包成 Card。
- Card 内部不混用多个无关主题。

### 5.3 Badge / Status

状态必须同时具备文字和颜色，必要时加图标；不能只靠红绿区分。

```css
.status {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  min-height: 1.5rem;
  padding: 0 0.5rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 500;
}

.status[data-tone="success"] { background: color-mix(in oklch, var(--success) 12%, transparent); color: var(--success-foreground); }
.status[data-tone="warning"] { background: color-mix(in oklch, var(--warning) 16%, transparent); color: var(--warning-foreground); }
.status[data-tone="destructive"] { background: color-mix(in oklch, var(--destructive) 12%, transparent); color: var(--destructive); }
```

评级文案统一为：`优秀`、`良好`、`中等`、`较差`、`差`。不要把不同组件中的评级颜色和文案做成多套规则。

### 5.4 Button

按钮只用于可执行动作，不把普通链接和状态标签伪装成按钮。

| 变体 | 用途 |
|---|---|
| Primary | 导出报告、查看行动计划等主行动，每个视图最多一个主要行动 |
| Secondary | 次要行动，如查看证据 |
| Outline | 需要边界但不抢主视觉的操作 |
| Ghost | 表格行操作、工具栏操作 |
| Destructive | 删除、清空或不可逆操作 |

每个按钮必须有 hover、focus-visible、disabled 和 loading 状态。图标按钮必须有可访问名称和 tooltip。

### 5.5 Progress / Score Bar

- 进度条表达“完成度、占比或评分”，不能同时承担多个含义。
- 轨道使用 `muted`，填充使用 `primary` 或对应状态色。
- 进度条旁显示数值和单位；不能只显示颜色变化。
- 不使用品牌渐变填充。
- 低置信度数据使用说明文字，不通过降低透明度伪装为低分。

### 5.6 Table / Data Table

- 表头使用 `muted` 或轻微背景对比，不使用全大写强制装饰。
- 数字列右对齐并启用等宽数字。
- 行 hover 使用 `accent`，不改变文字颜色到难以阅读。
- 排序、筛选、分页必须有当前状态和可访问名称。
- 表格下方说明数据来源、时间范围和样本量。

### 5.7 Chart

- 图表标题必须说明指标和时间/样本范围。
- 图例、坐标轴和数据标签优先使用文字，不依赖颜色识别。
- 同一图表最多使用 5 个语义色，避免彩虹色盘。
- 图表旁给出一句“如何解读”，让用户知道它支持什么判断。
- 无数据、加载失败和数据不足时必须有明确的空状态。

### 5.8 Alert / Empty / Error

每个数据模块至少定义以下状态：

```text
loading     加载中，显示骨架或进度，不显示虚假数据
ready       正常数据显示
empty       没有数据，解释原因和下一步
partial     数据不完整，显示覆盖范围
error       失败原因、重试动作和人工替代路径
```

## 6. 交互与动效

### 6.1 动效原则

- 首要动效是状态反馈，而不是页面装饰。
- 进入页面不对每个 section 做交错上浮；最多对首屏结论做一次淡入。
- 进度条填充可以使用 `300–600ms` 的宽度变化，但必须支持减少动效。
- 数字递增仅用于首次展示，不能影响用户快速读取最终值。
- 不使用弹跳、过度缓动、持续发光或自动循环动效。

```css
@media (prefers-reduced-motion: no-preference) {
  [data-motion="score"] { animation: score-in 360ms ease-out both; }
  [data-motion="progress"] { transition: width 480ms ease-out; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
  }
}
```

### 6.2 交互反馈

- 可点击元素必须有 hover 和 focus-visible。
- 操作完成后使用 toast、内联反馈或状态更新，不只改变颜色。
- 导出、重新计算等耗时操作显示进行中状态，并防止重复触发。
- 展开/收起内容时保留焦点位置，并更新可访问属性。

## 7. 可访问性

- 页面使用语义化的 `header`、`main`、`section`、`footer` 和正确标题层级。
- 键盘用户可以访问所有交互元素，焦点环必须可见：`outline: 2px solid var(--ring)`。
- 正文、按钮、表格和状态文字满足 WCAG 对比度要求。
- 颜色不是唯一的信息载体；评级必须有文字，图表必须有标签或说明。
- 触控目标最小约 `44 × 44px`。
- 表格、图表、图标按钮、折叠区和弹层提供辅助技术可读名称。
- 动效遵守 `prefers-reduced-motion`。
- 移动端不依赖 hover 才能获得关键信息。

## 8. 响应式规则

| 视口 | 规则 |
|---|---|
| `< 640px` | 单列；摘要指标 2 列；表格横向滚动；操作按钮尽量整行 |
| `640–1024px` | 2 列为主；复杂图表允许独占一行 |
| `> 1024px` | 最大宽度 1120px；摘要区可使用 4 列；证据区按内容使用 2–3 列 |

移动端特别规则：

- 总分字号降至 `40px` 左右，但不低于正文的可读层级。
- 首屏先显示结论，再显示分维度指标。
- 数据表不压缩到不可读；允许滚动并保持列名可辨识。
- 不把大量标签堆叠成连续彩色 pill。

## 9. 页面验收标准

### 9.1 视觉与结构

- [ ] 所有组件使用语义 token，不在组件内散落品牌 Hex 值。
- [ ] 首屏能在 5 秒内找到对象、总分、结论和第一条建议。
- [ ] 页面没有全局紫蓝渐变、装饰性光晕和无意义卡片悬浮。
- [ ] 标题层级、间距和圆角遵循统一尺度。
- [ ] 图表与结论、数据来源相邻出现。

### 9.2 交互与状态

- [ ] 所有按钮具备默认、hover、focus-visible、disabled、loading 状态。
- [ ] 数据模块具备 loading、ready、empty、partial、error 状态。
- [ ] 耗时操作不会重复提交，并能反馈进度或失败原因。
- [ ] 展开、筛选、排序和分页能被键盘操作。
- [ ] 减少动效设置生效后，页面仍然可读、可操作。

### 9.3 数据可信度

- [ ] 每个评分都有维度、范围、来源或样本说明。
- [ ] 低置信度或数据不足不会被渲染成确定性结论。
- [ ] 颜色、图标和文字对状态的表达保持一致。
- [ ] 建议按优先级、影响和执行条件排序，而不是只展示一串文案。

## 10. 实现约束

- 优先复用已有组件和数据结构；先改 token 和组件组合，再改页面结构。
- 使用 CSS variables 管理主题；浅色和深色主题只覆盖 token。
- HTML 报告可以借鉴 shadcn/ui 的组件命名和结构，但不要求引入 React、Tailwind 或 shadcn/ui 依赖。
- 如果项目确实使用 React/Tailwind，组件按 `Card / Badge / Button / Progress / Table / Alert` 等职责拆分，避免页面级巨型组件。
- 任何新颜色、新圆角或新阴影都必须先判断是否能复用现有 token。
- 不为了视觉改造修改后端评分逻辑或数据含义。

## 11. 交付给 AI Agent 的执行顺序

1. 读取项目现有结构、数据字段和运行命令。
2. 先建立 token 映射，清理散落颜色和尺寸。
3. 重构报告头部和诊断摘要，确保首屏任务成立。
4. 按组件职责整理表格、评分、图表、状态和行动计划。
5. 补齐 loading、empty、partial、error、focus 和 reduced-motion 状态。
6. 在桌面端和移动端分别预览，修复溢出、截断和操作可达性问题。
7. 按本文件第 9 节逐项验收，再提交最终代码。

## 12. 参考依据

- shadcn/ui 强调 open code、组合式组件和 AI 可读性；本规范将其转化为项目级设计约束。
- shadcn/ui 推荐使用 CSS variables 和语义化主题 token，并通过 `background/foreground`、`primary/primary-foreground` 等配对表达表面与内容关系。
- 圆角采用单一基础 `radius` 推导尺寸层级，而不是为每个组件独立定义。

参考：<https://ui.shadcn.com/docs>、<https://ui.shadcn.com/docs/theming>
