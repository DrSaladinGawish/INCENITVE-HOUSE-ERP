from pydantic import BaseModel


class SubCategoryResponse(BaseModel):
    id: str
    name: str
    category_name: str

    model_config = {"from_attributes": True}


class CategoryResponse(BaseModel):
    id: str
    name: str
    sub_categories: list[SubCategoryResponse] = []

    model_config = {"from_attributes": True}


class SubCategoryCreate(BaseModel):
    id: str
    name: str


class CategoryCreate(BaseModel):
    id: str
    name: str
