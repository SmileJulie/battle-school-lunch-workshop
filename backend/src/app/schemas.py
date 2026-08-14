from pydantic import BaseModel, Field


class School(BaseModel):
    officeCode: str
    schoolCode: str
    name: str
    officeName: str
    regionName: str
    schoolType: str


class SchoolSearchResponse(BaseModel):
    schools: list[School]
    hasMore: bool


class SchoolRef(BaseModel):
    officeCode: str
    schoolCode: str


class Meal(BaseModel):
    date: str
    mealType: str = Field(default="중식")
    dishes: list[str]
    calories: str | None = None
    nutrition: str | None = None
    origin: str | None = None
    servings: int | None = None


class MealSearchResponse(BaseModel):
    school: SchoolRef
    from_: str = Field(alias="from")
    to: str
    meals: list[Meal]

    model_config = {"populate_by_name": True}


class HealthResponse(BaseModel):
    status: str
