import kbooks
from kbooks import parse_command, parse_call_page, search_store


def page(text):
    return f'<html><body><div class="contents-area"><p>{text}</p></div></body></html>'


def test_watch_default_store():
    c = parse_command("123")
    assert (c.kind, c.store, c.number) == ("watch", "キャラ館", 123)


def test_watch_fullwidth_and_store():
    c = parse_command("同人館　１２３")
    assert (c.kind, c.store, c.number) == ("watch", "同人館", 123)


def test_watch_no_space():
    c = parse_command("乙女館45")
    assert (c.kind, c.store, c.number) == ("watch", "乙女館", 45)


def test_unknown_store_is_still_watch():
    c = parse_command("存在しない館 10")
    assert c.kind == "watch" and c.store not in kbooks.STORE_URLS


def test_stop_status_help():
    assert parse_command("停止").kind == "stop"
    assert parse_command("STOP").kind == "stop"
    assert parse_command("状況").kind == "status"
    assert parse_command("ヘルプ").kind == "help"


def test_search():
    c = parse_command("呪術廻戦のアクスタ")
    assert c.kind == "search"
    assert search_store(c.query) == "1. キャラ館プラス（ジャンプ館）"
    assert search_store("stray kids トレカ") == "10. 1F:K-POP館"
    assert search_store("よくわからない") is None


def test_page_plain_number():
    s = parse_call_page(page("123"))
    assert s.number == 123 and not s.preparing


def test_page_with_suffix_and_fullwidth():
    assert parse_call_page(page("現在の呼び出し番号 １２３番")).number == 123


def test_page_preparing():
    s = parse_call_page(page("準備中"))
    assert s.preparing and s.number is None


def test_page_missing():
    assert parse_call_page("<html></html>").number is None


def test_decode_sjis():
    body = page("準備中").encode("cp932")
    assert "準備中" in kbooks.decode_html(body, None)
