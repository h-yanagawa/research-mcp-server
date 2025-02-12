from typing import Optional

from pydantic import BaseModel, Field

class SetPageProperty(BaseModel):
    property_name: str = Field(..., title="Property Name")
    type: str = Field(..., title="Type")
    rich_text_value: Optional[str] = Field(None, title="Rich text value. It must be a plain text. Only for rich_text.")
    number_value: Optional[float] = Field(None, title="Number property value, Only for number.")
    selection_value: Optional[str] = Field(None, title="Selection property value. It must be an id. Only for select.")
    multi_select_values: Optional[list[str]] = Field(None, title="Multi select property Value. they must be ids. Only for multi_select.")
    status_value: Optional[str] = Field(None, title="Status property value. It must be an id. Only for status.")
    date_value: Optional[str] = Field(None, title="Date Value, Only for date.")
    url_title_value: Optional[str] = Field(None, title="URL Title, Only for url.")
    url_value: Optional[str] = Field(None, title="URL Value, Only for url.")

    def assert_type_and_value(self):
        if self.type == "rich_text" and self.rich_text_value is None:
            raise ValueError("Rich text value is required for rich_text type")
        if self.type == "number" and self.number_value is None:
            raise ValueError("Number value is required for number type")
        if self.type == "select" and self.selection_value is None:
            raise ValueError("Selection value is required for select type")
        if self.type == "multi_select" and self.multi_select_values is None:
            raise ValueError("Multi select values are required for multi_select type")
        if self.type == "status" and self.status_value is None:
            raise ValueError("Status value is required for status type")
        if self.type == "date" and self.date_value is None:
            raise ValueError("Date value is required for date type")
        if self.type == "url" and self.url_value is None:
            raise ValueError("URL value is required for url type")
