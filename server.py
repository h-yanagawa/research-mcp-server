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
def get_survey_pages():
    """Get survey pages"""
    return notion.databases.query(root_database_id)


@mcp.tool()
def get_survey_page(page_id: str):
    """Get survey page"""
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
def get_survey_page_property_definition():
    """Get property definition for survey page"""
    return notion.databases.retrieve(root_database_id)["properties"]


@mcp.tool()
def update_survey_page_property(page_id: str, updates: list[SetPageProperty], ctx: Context):
    """
    Update survey page property
    short_summaryは1行程度で記述する。
    URLはArxivのリンク、あるいは論文のリンクを記述ことが望ましい。
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
        elif type_ == "url":
            prop["url"] = update.url_value
            if update.url_title_value:
                prop["title"] = update.url_title_value
        else:
            ctx.warning(f"Property {update.property_name} is of type {type_}, which is not supported yet.")
            continue
    return {
        "result": notion.pages.update(page_id, properties=properties),
        "property_definitions": get_survey_page_property_definition()
    }


@mcp.tool()
def update_survey_page_body(page_id: str, body: str):
    """
    Update survey summary body
    論文は次の章立てでbodyへ要約する。JSONエスケープされたmarkdown形式で記述する。
    それぞれの章は3パラグラフ程度とする。
    # 論文タイトル
    ## 1. どのような研究か？
    ## 2. 先行研究に対する有用性？
    ## 3. 技術や手法の"キモ"はどこか？
    ## 4. どうやって有効だと検証した？
    ## 5. 議論はあるか？
    """
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
def create_new_survey_page(title: str, body: Optional[str] = None, short_summary: Optional[str] = None):
    """
    Create new survey page
    実行する前に、get_survey_pagesで既存のページが存在しないか確認すること。

    short_summaryは1行程度で記述する。
    titleは論文のタイトルを記述する。
    論文は次の章立てで要約しbodyに記述する。JSONエスケープされたMarkdown形式で記述する。
    それぞれの章は3パラグラフ程度とする。

    # 論文タイトル
    ## 1. どのような研究か？
    ## 2. 先行研究に対する有用性？
    ## 3. 技術や手法の"キモ"はどこか？
    ## 4. どうやって有効だと検証した？
    ## 5. 議論はあるか？
    """
    new_page = notion.pages.create(parent={"database_id": root_database_id}, properties={
        "Title": {
            "title": [{
                "type": "text",
                "text": {
                    "content": title
                }
            }]
        },
        "Summary": {
            "rich_text": [{
                "type": "text",
                "text": {
                    "content": short_summary or "",
                }
            }]
        }
    })
    update_survey_page_body(new_page["id"], body or "")
    return new_page


if __name__ == '__main__':
    mcp.run()
