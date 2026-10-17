# 微信表情包制作（weixin-sticker）

根据主题制作微信**静态**表情专辑的 Codex Skill。它会规划 8–24 张表情，并制作详情页横幅、封面和聊天页图标；赞赏引导图与致谢图可选。内附单文件 HTML 切割工具，以及尺寸处理、校验和打包脚本。

## 安装

将仓库完整复制到 Codex 的 Skills 目录：

```bash
git clone https://github.com/zxd-666/weixin-sticker.git ~/.codex/skills/weixin-sticker
```

也可以下载仓库 ZIP，解压后把整个 `weixin-sticker` 文件夹放进 `~/.codex/skills/`。不要只复制 `SKILL.md`。其他支持同类 Skills 目录结构的 Agent，可使用自己的 Skills 目录。

图片处理脚本需要 Python 3 和 Pillow：

```bash
python3 -m pip install -r ~/.codex/skills/weixin-sticker/requirements.txt
```

图片创作还需要所用 Agent 具备图片生成能力；本仓库不包含生成模型或成品表情。

## 使用

在新对话中说：“用 `$weixin-sticker` 帮我做一套微信静态表情包”。Skill 会先询问主题、风格、张数、参考图，以及后续是否需要逐步确认。选择逐步确认时，按整组表情、其他素材、切割和赞赏图依次确认；选择直接完成时，Agent 会自行完成并交付 ZIP。

`assets/表情包切割.html` 可直接在本地浏览器打开，无需联网。它支持网格切割、智能拆分、调整裁切、删除单张，以及批量解析主题名。

交付素材的尺寸和规则见 [素材规格](references/wechat-album-spec.md)。正式上传前，请以微信表情开放平台当时的上传页为准。

## 开发与验证

```bash
python3 -m pip install -r requirements.txt pytest
python3 -m pytest -q tests
node --test tests/test_cutter_group.mjs
```

Node.js 只用于运行切割工具测试，实际使用切割 HTML 不需要 Node.js。

## 许可证

[MIT](LICENSE) © 2026 [zxd-666](https://github.com/zxd-666)。
