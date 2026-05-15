from app.router_protocol import parse_dispatches


def test_parse_json_single_dispatch():
    dispatches = parse_dispatches('{"to":"research","message":"Find sources"}')

    assert len(dispatches) == 1
    assert dispatches[0].to == "research"
    assert dispatches[0].message == "Find sources"


def test_parse_json_multiple_dispatches():
    dispatches = parse_dispatches(
        '[{"to":"research","message":"Find sources"},{"to":"writer","message":"Draft reply"}]'
    )

    assert [item.to for item in dispatches] == ["research", "writer"]


def test_parse_line_dispatches():
    dispatches = parse_dispatches("@research: Find sources\n@writer: Draft reply")

    assert [item.to for item in dispatches] == ["research", "writer"]
    assert dispatches[1].message == "Draft reply"


def test_parse_json_code_fence():
    dispatches = parse_dispatches('```json\n{"to":"research","message":"Find sources"}\n```')

    assert len(dispatches) == 1
    assert dispatches[0].to == "research"
