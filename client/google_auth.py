import asyncio
import json
import os

from fastmcp import Client, FastMCP
from fastmcp.client.auth import OAuth


def result_to_json(result):

    for c in getattr(result, "content", []) or []:
        if getattr(c, "type", None) == "json":
            return getattr(c, "data", None)
        if getattr(c, "type", None) == "text":
            import json

            try:
                return json.loads(getattr(c, "text", ""))
            except Exception:
                pass
    return None


async def main():
    oauth = OAuth(
        mcp_url="http://localhost:8005/mcp",
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ],
    )

    async with Client("http://localhost:8005/mcp", auth=oauth) as client:
        print("Authenticated with Google!")

        tools = await client.list_tools()
        print("Tools:", [t.name for t in tools])

        res_info = await client.call_tool("get_user_info")
        info = result_to_json(res_info) or {}
        print("User info:", info)
        print("Google user:", info.get("email"))
        print("Name:", info.get("name"))

        res_time = await client.call_tool("get_time")
        t = result_to_json(res_time) or {}
        print("Time:", t)

        await client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        if "Session termination failed: 404" in str(e):
            pass
        else:
            pass
