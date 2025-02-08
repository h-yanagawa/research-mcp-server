# server.py
import json
import os
from typing import Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Context
from notion_client import Client
from pydantic import BaseModel, Field

from research_mcp.data.notion_ops import SetPageProperty

load_dotenv(verbose=True)

notion = Client(auth=os.environ["NOTION_TOKEN"])
root_database_id = os.environ["NOTION_ROOT_DATABASE_ID"]

# Create an MCP server
mcp = FastMCP("Research MCP Server")


@mcp.prompt()
def survey() -> str:
    return f"""
あなたは論文のサーベイを行い、サーベイ結果をNotionに整理する役割を担う。

サーベイ情報は `{root_database_id}` のデータベースで管理される。
"""


def get_first_code_block(block_id: str):
    children = notion.blocks.children.list(block_id)
    for child in children["results"]:
        if child["type"] == "code":
            captions = child["code"]["caption"]
            for caption in captions:
                if caption["plain_text"] == "AI Generated":
                    return child

    empty_code_block = {
        "object": "block",
        "type": "code",
        "code": {
            "caption": [
                {
                    "type": "text",
                    "text": {
                        "content": "AI Generated",
                    },
                }
            ],
            "rich_text": [{
                "type": "text",
                "text": {
                    "content": "",
                }
            }],
            "language": "markdown"
        }
    }
    ret = notion.blocks.children.append(block_id, children=[empty_code_block])

    return ret["results"][0]


@mcp.tool()
def get_survey_summaries():
    """Get survey summaries"""
    return notion.databases.query(root_database_id)


@mcp.tool()
def get_survey_summary(page_id: str):
    """Get survey summary"""
    page = notion.pages.retrieve(page_id)
    parent = notion.blocks.retrieve(page_id)
    children = notion.blocks.children.list(page_id)
    body = ""
    for child in children["results"]:
        if child["type"] == "code":
            body = child["code"]["rich_text"][0]["plain_text"]
            break
    return json.dumps({"parent": parent, "properties": page["properties"], "body": body}, ensure_ascii=False)


@mcp.tool()
def get_property_definition():
    """Get property definition for survey summary"""
    return notion.databases.retrieve(root_database_id)["properties"]


@mcp.tool()
def update_survey_summary_property(page_id: str, updates: list[SetPageProperty], ctx: Context):
    """
    Update survey summary property
    To know definition of properties, use `get_property_definition` tool in advance.
    """
    parent = notion.pages.retrieve(page_id)
    properties = parent["properties"]
    for update in updates:
        update.assert_type_and_value()
        if update.property_name not in properties:
            ctx.warning(f"Property {update.property_name} not found, skipping")
            continue
        prop = properties[update.property_name]
        if prop["type"] != update.type:
            ctx.warning(f"Property {update.property_name} is not of type {update.type}")
            continue
        type_ = prop["type"]
        if type_ == "number":
            prop[update.type] = float(update.number_value)
        elif type_ == "date":
            prop[update.type] = {"start": update.date_value}
        elif type_ == "rich_text":
            prop[update.type] = [{"type": "text", "text": {"content": update.rich_text_value}}]
        elif type_ == "select":
            prop[update.type] = {"id": update.selection_value}
        elif type_ == "multi_select":
            prop[update.type] = [{"id": v} for v in update.multi_select_values]
        elif type_ == "status":
            prop[update.type] = {"id": update.status_value}
        else:
            ctx.warning(f"Property {update.property_name} is of type {type_}, which is not supported yet.")
            continue
    return notion.pages.update(page_id, properties=properties)


@mcp.tool()
def update_survey_summary_block(page_id: str, body: str):
    code_block = get_first_code_block(page_id)
    notion.blocks.update(code_block["id"], code={
        "rich_text": [{
            "type": "text",
            "text": {
                "content": body,
            }
        }],
        "language": "markdown"
    })
    return f"Survey page body of {page_id} updated"

@mcp.tool()
def create_new_survey_summary(title: str, body: Optional[str] = None):
    new_page = notion.pages.create(parent={"database_id": root_database_id}, properties={
        "Title": {
            "title": [{
                "type": "text",
                "text": {
                    "content": title
                }
            }]
        }
    })
    update_survey_summary_block(new_page["id"], body or "")
    return new_page

