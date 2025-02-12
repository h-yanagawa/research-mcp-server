import json
from typing import Optional

from llama_index.core.tools.tool_spec.base import BaseToolSpec
from notion_client import Client
from pydantic import Field

from research_mcp.data.notion_ops import SetPageProperty
from research_mcp.data.rmcp_server_config import RMCPServerConfig
from research_mcp.utils.rmcp_context import IRMCPContext, DebugRMCPContext


class NotionToolSpec(BaseToolSpec):
    """
    """

    spec_functions = [
        "get_survey_summaries",
        "get_survey_summary",
        "get_property_definition",
        "create_new_survey_summary",
        "update_survey_summary_block",
        "update_survey_summary_property",
    ]

    def __init__(self, config: RMCPServerConfig):
        self._config = config
        self._notion = Client(auth=config.notion_token)
        self._root_database_id = config.notion_root_database_id
        self._ctx = DebugRMCPContext()

    def get_survey_summaries(self):
        """Get survey summaries"""
        return self._notion.databases.query(self._root_database_id)

    def get_survey_summary(self, page_id: str = Field(..., description="The page id")):
        """Get survey summary"""
        notion = self._notion
        page = notion.pages.retrieve(page_id)
        parent = notion.blocks.retrieve(page_id)
        children = notion.blocks.children.list(page_id)
        body = ""
        for child in children["results"]:
            if child["type"] == "code":
                body = child["code"]["rich_text"][0]["plain_text"]
                break
        return json.dumps({"parent": parent, "properties": page["properties"], "body": body}, ensure_ascii=False)

    def get_property_definition(self):
        """Get property definition for survey summary"""
        return self._notion.databases.retrieve(self._root_database_id)["properties"]

    def create_new_survey_summary(self, title: str, body: Optional[str] = None, short_summary: Optional[str] = None):
        new_page = self._notion.pages.create(parent={"database_id": self._root_database_id}, properties={
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
        self.update_survey_summary_block(new_page["id"], body or "")
        return new_page

    def update_survey_summary_block(self, page_id: str, body: str):
        code_block = self._get_first_code_block(page_id)
        self._notion.blocks.update(code_block["id"], code={
            "rich_text": [{
                "type": "text",
                "text": {
                    "content": body,
                }
            }],
            "language": "markdown"
        })
        return f"Survey page body of {page_id} updated"

    def update_survey_summary_property(self, page_id: str, updates: list[SetPageProperty]):
        """
        Update survey summary property
        To know definition of properties, use `get_property_definition` tool in advance.
        """
        ctx = self._ctx
        notion = self._notion
        parent = notion.pages.retrieve(page_id)
        properties = parent["properties"]
        updates = [SetPageProperty(**update) for update in updates]


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

    def _get_first_code_block(self, block_id: str):
        children = self._notion.blocks.children.list(block_id)
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
        ret = self._notion.blocks.children.append(block_id, children=[empty_code_block])
        return ret["results"][0]