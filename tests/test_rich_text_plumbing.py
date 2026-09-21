import base64
import struct
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pyrogram import enums, raw, types
from pyrogram.parser import Parser
from pyrogram.methods.messages import edit_inline_text as module


INLINE_MESSAGE_ID = base64.urlsafe_b64encode(struct.pack("<iqq", 2, 123, 456)).decode().rstrip("=")


class FakeClient:
    link_preview_options = None
    parse_mode = None
    parser = Parser(None)


@pytest.fixture
def sent(monkeypatch):
    calls = {}

    async def invoke_inline(client, dc_id, query, business_connection_id):
        calls["dc_id"] = dc_id
        calls["query"] = query
        return True

    monkeypatch.setattr(module, "invoke_inline", invoke_inline)

    return calls


async def edit(**kwargs):
    return await module.EditInlineText.edit_inline_text(
        FakeClient(), INLINE_MESSAGE_ID, **kwargs
    )


@pytest.mark.asyncio
async def test_markdown_rich_text_becomes_a_rich_message(sent):
    await edit(rich_text="# Title\n\n**bold**")

    query = sent["query"]

    assert isinstance(query.rich_message, raw.types.InputRichMessageMarkdown)
    assert query.rich_message.markdown == "# Title\n\n**bold**"
    assert query.message == ""
    assert sent["dc_id"] == 2


@pytest.mark.asyncio
async def test_html_rich_text_becomes_a_rich_message(sent):
    await edit(rich_text="<h2>Title</h2>", rich_text_parse_mode=enums.ParseMode.HTML)

    assert isinstance(sent["query"].rich_message, raw.types.InputRichMessageHTML)


@pytest.mark.asyncio
async def test_an_input_rich_message_is_written_as_given(sent):
    await edit(rich_text=types.InputRichMessage(html="<p>x</p>"))

    assert isinstance(sent["query"].rich_message, raw.types.InputRichMessageHTML)


@pytest.mark.asyncio
async def test_plain_text_is_untouched(sent):
    await edit(text="plain **bold**")

    query = sent["query"]

    assert query.rich_message is None
    assert query.message == "plain bold"
    assert query.entities


@pytest.mark.asyncio
async def test_neither_text_nor_rich_text_raises(sent):
    with pytest.raises(ValueError):
        await edit()
