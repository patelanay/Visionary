import asyncio
import time
import pytest
from app.nlp.schema_models import MealIngestionPayload, FoodItem, Macronutrients
from app.nlp.llm_parser import meal_parser
from app.nlp.usda_client import usda_client

def test_pydantic_schema_structure():
    macros = Macronutrients(calories=165.0, protein_g=31.0, carbs_g=0.0, fats_g=3.6)
    food = FoodItem(item_name="Chicken Breast", quantity=6.0, unit="oz", macronutrients=macros, usda_fdc_id="171077")
    
    payload = MealIngestionPayload(
        meal_name="Post-Workout Meal",
        meal_type="Post-Workout",
        raw_audio_transcript="6 ounce chicken breast",
        food_items=[food],
        total_macronutrients=macros,
        confidence_score=0.99
    )

    dumped = payload.model_dump()
    assert dumped["food_items"][0]["item_name"] == "Chicken Breast"
    assert dumped["total_macronutrients"]["calories"] == 165.0

@pytest.mark.asyncio
async def test_llm_nlp_parsing_under_1500ms():
    start_time = time.time()
    transcript = "A handful of almonds and a 6-ounce chicken breast with brown rice"
    
    payload = await meal_parser.parse_unstructured_transcript(transcript)
    elapsed_ms = (time.time() - start_time) * 1000

    assert payload is not None
    assert len(payload.food_items) >= 2
    assert payload.total_macronutrients.calories > 0
    assert payload.total_macronutrients.protein_g > 0
    assert elapsed_ms < 1500.0, f"Latency {elapsed_ms}ms exceeded target <1500ms"

def test_usda_client_lookup():
    res = usda_client.fetch_macronutrients("chicken breast", 2.0)
    assert "macros" in res
    assert res["macros"].protein_g > 30.0

if __name__ == "__main__":
    asyncio.run(test_llm_nlp_parsing_under_1500ms())
    test_pydantic_schema_structure()
    test_usda_client_lookup()
    print("NLP Schema & USDA Integration Tests Passed Successfully!")
