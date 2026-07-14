# API 诊断报告

## 测试结果

| API | 状态 | 错误 |
|-----|------|------|
| **豆包 (Ark)** | ⚠️ Key 有效，但模型不存在 | 404: `InvalidEndpointOrModel.NotFound` |
| **Kimi (Moonshot)** | ❌ Key 无效 | 401: `Invalid Authentication` |
| **SerpAPI** | ❌ 未配置 | — |
| **Bing Search** | ❌ 未配置 | — |

---

## 问题 1：豆包 API — 需要创建推理接入点

### 原因

豆包 Ark 平台使用**推理接入点（Endpoint）**机制。你的 API Key 已验证有效，但直接调用预置模型名（如 `doubao-pro-32k`）会返回 404，因为你还没有创建对应的接入点。

### 解决步骤（约 3 分钟）

1. 打开 https://console.volcengine.com/ark/
2. 登录后进入 **"在线推理" → "推理接入点"**
3. 点击 **"创建接入点"**
4. 选择模型（如 `Doubao-pro-32k`）
5. 创建完成后，复制 **接入点 ID**（格式如 `ep-20240714-xxxxx`）
6. 将 ID 填入 `.env`：
   ```bash
   DOUBAO_MODEL=ep-你的接入点ID
   ```

### 图示

```
豆包 Ark 控制台
  ├── 在线推理
  │     ├── 推理接入点 ← 点击这里
  │     │     ├── [创建接入点] ← 点这个按钮
  │     │     │     ├── 选择模型: Doubao-pro-32k
  │     │     │     ├── 接入点名称: 任意填写
  │     │     │     └── 创建
  │     │     └── ep-20240714-abcd1234 ← 复制这个 ID
```

---

## 问题 2：Kimi API — Key 无效

### 原因

Kimi API 返回 401 `Invalid Authentication`，说明当前的 API Key 无效或已过期。

### 解决步骤

1. 打开 https://platform.moonshot.cn/
2. 登录后进入 **"API Key 管理"**
3. 检查现有 Key 是否过期，或创建新 Key
4. 将新 Key 填入 `.env`：
   ```bash
   KIMI_API_KEY=sk-你的新Key
   ```

---

## 问题 3：搜索 API — 可选配置

### 当前方案

项目已配置 **LLM Fallback 降级策略**：
- **阶段 4（AI 搜索）**：当豆包 API 不可用时，使用 LLM 模拟搜索结果
- **阶段 6（舆情扫描）**：当搜索 API 不可用时，使用 LLM 生成舆情分析

这意味着**即使不配搜索 API，项目也能完整运行**，只是数据质量为 "degraded"（降级）。

### 如需真实搜索数据

**推荐：SerpAPI（百度支持）**

1. 打开 https://serpapi.com/
2. 用 Google 账号一键注册
3. 进入 Dashboard 复制 API Key
4. 填入 `.env`：
   ```bash
   SERPAPI_KEY=你的Key
   ```

**免费额度**：每月 100 次搜索

---

## 推荐行动顺序

| 优先级 | 行动 | 预期效果 |
|--------|------|----------|
| **P0** | 创建豆包推理接入点，更新 `DOUBAO_MODEL` | 阶段 4（AI 搜索）获得真实数据 |
| **P1** | 验证/更新 Kimi API Key | 阶段 1/6/7/9 的 LLM 推理更稳定 |
| **P2** | 注册 SerpAPI（可选） | 阶段 2（基建）和阶段 6（舆情）获得真实数据 |

---

## 临时方案：纯 LLM 模拟运行

如果你现在就想看到完整效果，我可以修改代码，让所有阶段都使用 LLM 模拟数据（不需要任何 API 配置）。这样你能立即看到完整的 HTML 报告效果，后续再接入真实 API。

**要启用临时方案吗？** 回复 "启用临时方案" 即可。
