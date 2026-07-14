# GEO 可见度诊断师 — 设计规范 (Design System)

> 本规范定义 GEO 可见度诊断师 HTML 报告的独特视觉风格，确保与竞品形成差异化。
>
> 核心理念："品牌体检报告" — 专业、数据密集、科技感，而非通用 SaaS 说明文档。

---

## 1. 设计哲学

### 定位差异

| 竞品风格 | 我们的风格 | 差异点 |
|----------|-----------|--------|
| 浅灰白底 + 绿/橙/红评分 | 深色底 + 品牌紫/蓝评分 | 第一眼识别度 |
| 卡片式大留白 | 紧凑数据行 + 分区对比 | 信息密度 |
| 通用圆角徽章 | 进度条 + 数字高亮 | 数据驱动感 |
| 静态表格 | 动态进度 + 状态徽章 | 可执行感 |
| 系统字体 | 阅读字体 + 数据字体 | 专业度 |

### 设计关键词

**专业 · 数据 · 科技 · 可执行**

---

## 2. 色彩体系

### 2.1 主色调（品牌色）

| 色名 | Hex | 用途 |
|------|-----|------|
| 品牌主色 | `#6366F1` | 主标题、核心高亮、进度条填充 |
| 品牌副色 | `#8B5CF6` | 辅助高亮、链接 hover、次要数据 |
| 品牌渐变 | `#6366F1 → #8B5CF6` | 大分数、AIVO 总分、进度条渐变 |
| 品牌亮 | `#A78BFA` | 轻量高亮、hover 状态 |
| 品牌暗 | `#4338CA` | 深色背景上的高亮 |

### 2.2 评分色（替代 Tailwind 默认色）

| 等级 | 前景色 | 背景色 | 区别于竞品 |
|------|--------|--------|-----------|
| 优秀 | `#10B981` | `#064E3B` |  Emerald 深色版，不扎眼 |
| 良好 | `#34D399` | `#065F46` |  更柔和的绿 |
| 中等 | `#FBBF24` | `#78350F` |  琥珀色，区别于土黄 |
| 较差 | `#F87171` | `#7F1D1D` |  柔和红，不刺眼 |
| 差 | `#EF4444` | `#7F1D1D` |  标准红 |

**关键变化**：用深色背景色（深绿/深琥珀/深红）替代浅白底，让评分标签更有质感。

### 2.3 背景色

| 色名 | Hex | 用途 |
|------|-----|------|
| 页面底色 | `#0F172A` | 全局深色背景 |
| 卡片底色 | `#1E293B` | 卡片/区块背景 |
| 卡片悬停 | `#334155` | 卡片 hover 状态 |
| 分割底色 | `#0B1120` | 交替行/分隔区域 |
| 数据行底色 | `#1E293B` | 表格行背景 |
| 数据行交替 | `#0F172A` | 表格交替行 |

### 2.4 文字色

| 色名 | Hex | 用途 |
|------|-----|------|
| 主文字 | `#F1F5F9` | 标题、正文 |
| 次文字 | `#94A3B8` | 描述、辅助信息 |
|  muted | `#64748B` | 时间戳、次要标签 |
| 高亮文字 | `#6366F1` | 核心数据、链接 |

---

## 3. 字体系统

### 3.1 字体栈

```css
/* 数据字体：等宽，数字对齐 */
--font-data: "SF Mono", "Fira Code", "JetBrains Mono", "Consolas", monospace;

/* 阅读字体：中文优化 */
--font-body: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans SC", sans-serif;

/* 标题字体：无衬线 */
--font-heading: "Inter", "SF Pro Display", "PingFang SC", sans-serif;
```

### 3.2 字号层级

| 层级 | 大小 | 字重 | 用途 | 字体 |
|------|------|------|------|------|
| 品牌名 | 36px | 700 | 封面品牌名 | heading |
| 页面标题 | 28px | 700 | 各 section 标题 | heading |
| 分数大 | 56px | 700 | AIVO 总分 | data |
| 分数中 | 32px | 600 | 维度评分 | data |
| 分数小 | 20px | 600 | 子项评分 | data |
| 正文 | 13px | 400 | 描述、说明 | body |
| 标签 | 11px | 500 | 徽章、标签 | body |
| 数据 | 14px | 500 | 表格数据、指标 | data |

**关键变化**：分数用等宽字体（数据感），正文用系统字体（可读性）。

---

## 4. 布局系统

### 4.1 容器

- 最大宽度：1100px（紧凑，不是 1200px）
- 两侧留白：20px（移动端 16px）
- Section 间距：16px（紧凑，不是 24px）

### 4.2 卡片规格

| 属性 | 值 | 说明 |
|------|-----|------|
| 圆角 | 8px | 更小更锐利（不是 12px） |
| 阴影 | `0 1px 2px rgba(0,0,0,0.3)` | 微弱阴影，不浮出 |
| 边框 | `1px solid #334155` | 细边框，比阴影更重要 |
| 内边距 | 20px | 紧凑 |

### 4.3 网格系统

- 3 列：KPI 卡片、竞品卡片、用户画像
- 2 列：亮点/风险并排、基建详情
- 全宽：搜索矩阵、表格、时间轴

---

## 5. 组件规范

### 5.1 AIVO 总分（封面核心）

```
┌────────────────────────────┐
│  [品牌名]  GEO 可见度诊断   │
│                            │
│        ┌─────────┐         │
│        │   79    │  ← 56px 等宽数字
│        │  AIVO   │  ← 品牌渐变文字
│        └─────────┘         │
│      [中等] 标签           │
└────────────────────────────┘
```

- 数字：56px，等宽字体，品牌渐变色
- 去掉圆环图（太像通用工具），用纯数字 + 标签
- 背景：品牌渐变底纹（微弱），不是白底

### 5.2 评分标签（Badge）

```css
.badge {
  padding: 3px 10px;
  border-radius: 4px;   /* 更小圆角 */
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.3px;
}
.badge-excellent { background: #064E3B; color: #10B981; border: 1px solid #065F46; }
.badge-good      { background: #065F46; color: #34D399; border: 1px solid #047857; }
.badge-medium    { background: #78350F; color: #FBBF24; border: 1px solid #92400E; }
.badge-poor      { background: #7F1D1D; color: #F87171; border: 1px solid #991B1B; }
.badge-bad       { background: #7F1D1D; color: #EF4444; border: 1px solid #991B1B; }
```

**关键变化**：深色背景 + 边框，更有质感。

### 5.3 进度条（Bar Chart）

```css
.bar-track {
  height: 18px;  /* 更细 */
  background: #1E293B;
  border-radius: 3px;  /* 更锐利 */
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  border-radius: 3px;
  /* 品牌渐变 */
  background: linear-gradient(90deg, #6366F1, #8B5CF6);
  /* 内阴影文字效果 */
  text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}
```

**关键变化**：用品牌紫/蓝渐变替代单色填充，进度条更有识别度。

### 5.4 表格

```css
table {
  font-size: 13px;
  border-collapse: collapse;
  width: 100%;
}

/* 交替行 */
tbody tr:nth-child(even) { background: #0F172A; }
tbody tr:nth-child(odd)  { background: #1E293B; }

/* 悬停 */
tbody tr:hover { background: #334155; }

/* 表头 */
th {
  background: #0F172A;
  color: #64748B;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 10px 12px;
}

/* 数据单元 */
td {
  padding: 10px 12px;
  border-bottom: 1px solid #1E293B;
  color: #F1F5F9;
}
```

**关键变化**：深色交替行、无竖向边框，更紧凑。

### 5.5 搜索矩阵卡片

```css
.query-card {
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 12px;
  border: 1px solid transparent;
  transition: border-color 0.2s;
}

/* 已提及 + 首段 */
.query-card.first-paragraph {
  background: #064E3B;
  border-color: #10B981;
  color: #10B981;
}

/* 已提及 */
.query-card.mentioned {
  background: #065F46;
  border-color: #34D399;
  color: #34D399;
}

/* 未提及 */
.query-card.not-mentioned {
  background: #7F1D1D;
  border-color: #EF4444;
  color: #F87171;
}
```

---

## 6. 动画与交互

### 6.1 数字递增动画（AIVO 分数）

```css
@keyframes countUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
.score-number {
  animation: countUp 0.6s ease-out forwards;
}
```

### 6.2 进度条填充动画

```css
@keyframes fillBar {
  from { width: 0; }
  to   { width: var(--target-width); }
}
.bar-fill {
  animation: fillBar 1s ease-out forwards;
}
```

### 6.3 卡片入场动画

```css
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
section {
  animation: fadeInUp 0.4s ease-out forwards;
}
/* 交错延迟 */
section:nth-child(2) { animation-delay: 0.1s; }
section:nth-child(3) { animation-delay: 0.2s; }
/* ... */
```

### 6.4 悬停效果

```css
section {
  transition: border-color 0.2s, transform 0.2s;
}
section:hover {
  border-color: #6366F1;
  transform: translateY(-2px);
}
```

---

## 7. 页面结构

### 7.1 页面分区（从上到下）

```
┌─────────────────────────────────┐
│ ① 封面区                          │  ← 品牌名 + AIVO 总分 + 日期
├─────────────────────────────────┤
│ ② 执行摘要                        │  ← 一句话诊断 + 4 维度 KPI + 亮点/风险
├─────────────────────────────────┤
│ ③ 用户画像                        │  ← 3 列人群卡片 + 搜索意图标签
├─────────────────────────────────┤
│ ④ 基建评估                        │  ← 2 列：进度条 + 雷达图 + 媒体矩阵表
├─────────────────────────────────┤
│ ⑤ 竞品对标                        │  ← 条形对比 + 竞品卡片
├─────────────────────────────────┤
│ ⑥ AI 搜索可见性                   │  ← 3 个 KPI 大数字 + 搜索矩阵
├─────────────────────────────────┤
│ ⑦ 舆情健康度                      │  ← 负面率 + 饼图 + Top 问题列表
├─────────────────────────────────┤
│ ⑧ 优化建议                        │  ← 优先级行动 + Quick Wins + 路线图
├─────────────────────────────────┤
│ ⑨ 页脚                            │  ← 生成时间 + 免责声明
└─────────────────────────────────┘
```

### 7.2 关键变化

1. **去掉圆环图**：用纯数字 + 渐变标签替代（更简洁、更有数据感）
2. **雷达图保留**：但改为深色主题 + 品牌色填充
3. **饼图改为环形图**：更现代，中心可放数字
4. **时间轴改为卡片列表**：更有层次

---

## 8. 响应式

### 断点

| 断点 | 行为 |
|------|------|
| < 768px | 单列、紧凑字号、KPI 卡片 2 列 |
| 768-1024px | 2 列为主、中等字号 |
| > 1024px | 全 3 列、标准字号 |

### 移动端特殊处理

- 封面总分：36px 字号（等宽）
- 表格：横向滚动，不折行
- 搜索矩阵：单列，卡片高度统一
- 进度条：标签在上、条在下

---

## 9. 实现路径

### 9.1 修改优先级

| 优先级 | 修改项 | 工作量 | 效果 |
|--------|--------|--------|------|
| P0 | 深色背景 + 品牌色体系 | 1h | 最大差异化 |
| P0 | 字体栈（等宽数据字体） | 30min | 专业感 |
| P1 | 卡片样式（圆角、边框、阴影） | 30min | 质感提升 |
| P1 | 评分标签（深色背景版） | 20min | 识别度 |
| P1 | 进度条（品牌渐变） | 20min | 统一感 |
| P2 | 数字递增动画 | 30min | 高级感 |
| P2 | 卡片入场动画 | 20min | 高级感 |
| P3 | 饼图改环形图 | 40min | 现代感 |
| P3 | 去掉圆环图 | 10min | 简洁感 |

### 9.2 文件修改清单

- `report/template.html` — 核心样式 + 结构
- `stages/s8_aivo_score.py` — 确保颜色数据传递（如需要）
- 无需修改后端逻辑，纯前端样式变化

---

## 10. 竞品对比

### 当前设计 vs 竞品 vs 新设计

| 维度 | 竞品 A（通用 SaaS） | 竞品 B（数据分析） | 当前设计 | 新设计 |
|------|-------------------|-------------------|----------|--------|
| 背景色 | 浅灰白底 | 浅灰白底 | 浅灰白底 | **深色底** |
| 主色 | 绿色/蓝色 | 橙色 | 绿色 | **品牌紫/蓝** |
| 卡片风格 | 大圆角 + 强阴影 | 扁平 | 大圆角 + 阴影 | **小圆角 + 细边框** |
| 字体 | 系统字体 | 系统字体 | 系统字体 | **等宽数据字体 + 阅读字体** |
| 信息密度 | 低 | 中 | 中 | **高** |
| 动画 | 无 | 无 | 无 | **数字递增 + 入场动画** |
| 第一眼 | "又一个工具" | "数据分析" | "通用报告" | **"品牌诊断报告"** |

---

*本文档供前端开发和 AI Agent 在修改 HTML 模板时参考。修改后需更新 `MEMORY.md` 中的设计变更记录。*
