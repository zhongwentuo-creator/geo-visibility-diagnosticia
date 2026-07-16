# V1.5 GitHub 发布结构

## 目标仓库

`https://github.com/zhongwentuo-creator/geo-visibility-diagnosticia`

远端 `main` 当前是平铺的 V1.0 引擎。V1.5 不应覆盖或移动 V1.0；发布时在根目录新增 `v1.5/`：

```text
geo-visibility-diagnosticia/
├── main.py                    # V1.0 引擎（保留）
├── config.py                  # V1.0 引擎（保留）
├── stages/ report/ utils/     # V1.0 引擎（保留）
├── .github/workflows/
│   └── geo-v15-ci.yml         # V1.5 质量门禁
├── .dockerignore              # 根构建上下文的敏感文件排除
└── v1.5/                      # 本目录发布后的内容
    ├── src/
    ├── tests/
    ├── docs/
    ├── Dockerfile
    ├── render.yaml
    └── requirements.txt
```

## 发布时需要同步的补齐项

1. 将本目录发布为远端的 `v1.5/`。
2. 将 `release-assets/geo-v15-ci.yml` 写入远端根目录 `.github/workflows/geo-v15-ci.yml`，以便 GitHub Actions 真正执行。
3. 将根 `.dockerignore` 补齐 `.env`、虚拟环境、输出与系统文件，避免 Docker 构建上下文携带本地敏感内容。
4. 更新远端根 README：保留 V1.0 CLI 用法，并增加 V1.5 Web 工作台入口与本地启动方式。
5. 让 `v1.5/Dockerfile` 以仓库根目录作为构建上下文，将根目录 V1.0 引擎复制到 `/app/engine`。

`.dockerignore.root` 是待放到远端根目录的最终内容；不要直接把 V1.5 的 `.dockerignore` 当作根构建上下文的规则。

## 不应提交

- `.env`、API Key、Token、证书
- `.venv/`、`__pycache__/`、`.pytest_cache/`
- `output/` 下的诊断报告与本地调试产物
- `.DS_Store`

## 发布前检查

```bash
python -m pytest -q
python -m py_compile src/api.py src/engine_adapter.py
node --check src/static/js/app.js
```

首次合并后，还应在 GitHub Actions 中完成一次 Docker build；获得公网 URL 后再完成真实 API Key、移动端和 24 小时稳定性验收。
