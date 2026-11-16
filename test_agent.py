import asyncio
from pathlib import Path

from mistralai import agents

import main


async def check_tools() -> None:
    files = await main.ugot_list_files()
    assert any("README.md" in f for f in files), files
    content = await main.ugot_read_file("config.yaml")
    assert "prawy: 85" in content, content
    hits = await main.ugot_search_files("motory")
    assert hits and "config.yaml" in hits[0], hits
    try:
        await main.ugot_read_file("../../etc/passwd")
        raise AssertionError("path escape allowed")
    except agents.ToolError:
        pass
    print("tools OK")


async def check_scripted() -> None:
    test_agent = main.agent.override(
        model=agents.testing.ScriptedModel(
            [
                agents.testing.call("ugot_list_files"),
                agents.testing.reply("Są tu README.md i config.yaml."),
            ]
        )
    )
    async with agents.local_runtime():
        state = await test_agent.run("Co masz w plikach?")
    assert isinstance(state, agents.Completed), state
    print("scripted turn OK:", state.text)


asyncio.run(check_tools())
asyncio.run(check_scripted())
