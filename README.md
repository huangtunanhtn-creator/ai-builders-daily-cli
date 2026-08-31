# AI Builders Daily CLI

把《AI Builders 日报》内容 JSON 渲染成：

- 钉钉文档报纸版 **JSONML**（居中大字报头、双栏正文、红色栏目名、浅纸色金句 callout）
- 本地可阅读的双栏 **HTML** 报纸

并支持一键覆写钉钉文档、生成小Q 提醒短消息。

## 安装

```bash
npm install -g ai-builders-daily-cli
```

依赖：Node.js ≥ 18、Python 3。

## 快速开始

```bash
# 1. 从示例生成一份内容 JSON
ai-builders-daily init content.json

# 2. 校验
ai-builders-daily validate content.json

# 3. 渲染 JSONML（给钉钉文档用）
ai-builders-daily render jsonml content.json -o /tmp/newspaper.json

# 4. 渲染 HTML（本地归档）
ai-builders-daily render html content.json -o outputs/2026-08-31.html
```

## 内容 JSON 格式

见 [`examples/content.example.json`](examples/content.example.json) 和 [`src/schema.json`](src/schema.json)。

字段说明：

| 字段 | 说明 |
|---|---|
| `masthead` | 报名 |
| `dateline` | 日期行，如 `2026年8月31日 星期一` |
| `stats` | 统计行，如 `12 位 builder · 24 条动态 · 0 期播客` |
| `headline` | 头条：标题、导语、正文段落、链接 |
| `sections` | 分版块短讯栏目 |
| `features` | 深度长文/播客，通常 0 或 1 条 |
| `quotes` | 今日金句 1–3 句 |
| `colophon` | 报尾 |

## 发布到钉钉文档

```bash
ai-builders-daily publish \
  --content content.json \
  --node o14dA3GK8gdADMzmHEprXA6lW9ekBD76 \
  --title "2026-08-31"
```

要求本地已安装并登录 `dws`（钉钉 Workspace CLI）。命令会自动：

1. 渲染 JSONML 到临时文件
2. 以 `--mode overwrite --yes` 覆写钉钉文档
3. 更新文档标题

发布后务必回读校验：

```bash
dws doc read --node o14dA3GK8gdADMzmHEprXA6lW9ekBD76
dws doc read --node o14dA3GK8gdADMzmHEprXA6lW9ekBD76 --content-format jsonml
```

## 生成小Q 提醒短消息

```bash
ai-builders-daily im-message content.json --doc-url https://alidoc.dingtalk.com/...
```

输出控制在 300 字以内，可直接复制到 `qoder_delegate_to_im` 使用。`delegate_to_im` 对长文本会截断，因此必须用短消息，不要塞全文。

## 完整日报工作流

```bash
# 0. 用你自己的素材脚本（如 prepare-digest.js）生成 content.json

# 1. 渲染与发布
ai-builders-daily publish --content content.json --node <NODE_ID> --title "$(date +%F)"

# 2. 生成本地 HTML 归档
ai-builders-daily render html content.json -o "outputs/ai-builders-daily-$(date +%F).html"

# 3. 复制短消息到 IM 工具
ai-builders-daily im-message content.json --doc-url <DOC_URL>
```

## 设计原则

- **只渲染，不联网**：CLI 不访问 X、不搜网页、不调 API。所有内容来自你提供的内容 JSON。
- **链接必填**：每条内容必须带原始 URL，校验会强制检查。
- **JSONML 严格对齐钉钉 schema**：`a` 节点子元素按 `span[data-type=text] > span[data-type=leaf]` 嵌套，`table` 分栏保留 `sr:true`，报头居中保留 `jc:center`。

## License

MIT
