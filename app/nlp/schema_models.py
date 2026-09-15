from pydantic import BaseModel, Field
from typing import List, Optional

class Macronutrients(BaseModel):
    calories: float = Field(description="Total energy in kilocalories (kcal)", ge=0)
    protein_g: float = Field(description="Protein content in grams", ge=0)
    carbs_g: float = Field(description="Carbohydrate content in grams", ge=0)
    fats_g: float = Field(description="Total fats content in grams", ge=0)
    fiber_g: Optional[float] = Field(default=0.0, description="Dietary fiber content in grams", ge=0)

class FoodItem(BaseModel):
    item_name: str = Field(description="Name of the food item (e.g., chicken breast, almonds, brown rice)")
    quantity: float = Field(description="Numeric quantity consumed (e.g., 6, 1, 200)", gt=0)
    unit: str = Field(description="Unit of measurement (e.g., oz, grams, cup, serving, piece)")
    macronutrients: Macronutrients = Field(description="Detailed macronutrient profile for this item")
    usda_fdc_id: Optional[str] = Field(default=None, description="USDA FoodData Central ID if matched")

class MealIngestionPayload(BaseModel):
    meal_name: str = Field(description="Descriptive title for the meal (e.g., Post-Workout Protein Shake & Almonds)")
    meal_type: str = Field(description="Category of meal: Breakfast, Lunch, Dinner, Snack, or Post-Workout")
    raw_audio_transcript: str = Field(description="Original transcribed natural language speech")
    food_items: List[FoodItem] = Field(description="List of parsed food items and quantities")
    total_macronutrients: Macronutrients = Field(description="Aggregated macronutrient totals for the entire meal")
    confidence_score: float = Field(default=0.98, description="Pydantic validation confidence score", ge=0, le=1.0)
