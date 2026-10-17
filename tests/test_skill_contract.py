from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / 'SKILL.md'


def text():
    return SKILL.read_text(encoding='utf-8')


def test_skill_has_valid_discoverable_frontmatter():
    t = text()
    assert t.startswith('---\nname: weixin-sticker\n')
    assert 'description: Use when' in t.split('---', 2)[1]


def test_skill_covers_core_output_modes():
    t = text()
    for term in ['表情/', '详情页横幅', '表情封面图', '聊天页图标', '240×240', '750×400', '50×50', '8–24']:
        assert term in t


def test_skill_has_generation_and_qa_contracts():
    t = text()
    for term in ['多格透明整图', '表情包切割.html', 'validate_pack.py', 'package_album.py', '240×240', '不超过 4 个字']:
        assert term in t


def test_skill_does_not_depend_on_private_conversation_context():
    t = text()
    for private_term in ['你这几天', '老婆', '快乐沃克', '水噜噜']:
        assert private_term not in t
