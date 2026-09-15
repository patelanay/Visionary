import requests
from typing import Dict, Any, Optional
from app.config import settings
from app.nlp.schema_models import Macronutrients

class USDAClient:
    """
    USDA FoodData Central REST Client.
    Queries official USDA database for nutrient profiles (Protein, Carbs, Fats, Calories).
    Provides intelligent fallback database for rapid offline development.
    """
    BASE_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

    # Pre-calculated offline USDA database fallback (per standard serving / piece / cup)
    FALLBACK_DATABASE = {
        "ribeye": {"calories": 650.0, "protein": 62.0, "carbs": 0.0, "fats": 45.0, "unit": "8 oz steak"},
        "steak": {"calories": 550.0, "protein": 54.0, "carbs": 0.0, "fats": 35.0, "unit": "8 oz steak"},
        "beef": {"calories": 450.0, "protein": 46.0, "carbs": 0.0, "fats": 28.0, "unit": "6 oz"},
        "ground beef": {"calories": 400.0, "protein": 40.0, "carbs": 0.0, "fats": 26.0, "unit": "6 oz"},
        "chicken": {"calories": 240.0, "protein": 45.0, "carbs": 0.0, "fats": 5.0, "unit": "5 oz breast"},
        "chicken breast": {"calories": 240.0, "protein": 45.0, "carbs": 0.0, "fats": 5.0, "unit": "5 oz breast"},
        "broccoli": {"calories": 55.0, "protein": 3.7, "carbs": 11.2, "fats": 0.6, "unit": "1 cup"},
        "baked potato": {"calories": 161.0, "protein": 4.3, "carbs": 36.6, "fats": 0.2, "unit": "1 medium"},
        "potato": {"calories": 161.0, "protein": 4.3, "carbs": 36.6, "fats": 0.2, "unit": "1 medium"},
        "sweet potato": {"calories": 112.0, "protein": 2.0, "carbs": 26.0, "fats": 0.1, "unit": "1 medium"},
        "almond": {"calories": 164.0, "protein": 6.0, "carbs": 6.0, "fats": 14.0, "unit": "1 oz"},
        "almonds": {"calories": 164.0, "protein": 6.0, "carbs": 6.0, "fats": 14.0, "unit": "1 oz"},
        "egg": {"calories": 72.0, "protein": 6.3, "carbs": 0.4, "fats": 4.8, "unit": "1 large"},
        "eggs": {"calories": 144.0, "protein": 12.6, "carbs": 0.8, "fats": 9.6, "unit": "2 large"},
        "scrambled eggs": {"calories": 180.0, "protein": 12.0, "carbs": 2.0, "fats": 14.0, "unit": "2 eggs"},
        "avocado": {"calories": 240.0, "protein": 3.0, "carbs": 12.0, "fats": 22.0, "unit": "1 whole"},
        "avocado toast": {"calories": 290.0, "protein": 8.0, "carbs": 30.0, "fats": 16.0, "unit": "1 slice"},
        "toast": {"calories": 80.0, "protein": 3.0, "carbs": 14.0, "fats": 1.0, "unit": "1 slice"},
        "salmon": {"calories": 280.0, "protein": 34.0, "carbs": 0.0, "fats": 15.0, "unit": "5 oz fillet"},
        "tuna": {"calories": 180.0, "protein": 39.0, "carbs": 0.0, "fats": 1.0, "unit": "1 can"},
        "rice": {"calories": 205.0, "protein": 4.3, "carbs": 45.0, "fats": 0.4, "unit": "1 cup cooked"},
        "brown rice": {"calories": 216.0, "protein": 5.0, "carbs": 45.0, "fats": 1.8, "unit": "1 cup cooked"},
        "white rice": {"calories": 205.0, "protein": 4.3, "carbs": 45.0, "fats": 0.4, "unit": "1 cup cooked"},
        "protein shake": {"calories": 180.0, "protein": 30.0, "carbs": 5.0, "fats": 2.5, "unit": "1 scoop"},
        "whey": {"calories": 120.0, "protein": 24.0, "carbs": 2.0, "fats": 1.5, "unit": "1 scoop"},
        "greek yogurt": {"calories": 130.0, "protein": 17.0, "carbs": 6.0, "fats": 4.0, "unit": "1 cup"},
        "yogurt": {"calories": 150.0, "protein": 8.0, "carbs": 12.0, "fats": 8.0, "unit": "1 cup"},
        "banana": {"calories": 105.0, "protein": 1.3, "carbs": 27.0, "fats": 0.3, "unit": "1 medium"},
        "apple": {"calories": 95.0, "protein": 0.5, "carbs": 25.0, "fats": 0.3, "unit": "1 medium"},
        "oatmeal": {"calories": 150.0, "protein": 5.0, "carbs": 27.0, "fats": 2.5, "unit": "0.5 cup dry"},
        "oats": {"calories": 150.0, "protein": 5.0, "carbs": 27.0, "fats": 2.5, "unit": "0.5 cup dry"},
        "pasta": {"calories": 220.0, "protein": 8.0, "carbs": 43.0, "fats": 1.3, "unit": "1 cup cooked"},
        "peanut butter": {"calories": 190.0, "protein": 8.0, "carbs": 7.0, "fats": 16.0, "unit": "2 tbsp"}
    }

    def __init__(self):
        self.api_key = settings.USDA_API_KEY or "DEMO_KEY"

    def fetch_macronutrients(self, food_name: str, quantity: float = 1.0) -> Dict[str, Any]:
        """
        Fetches macronutrient breakdown from USDA API with automatic fallback.
        """
        clean_name = food_name.lower().strip()

        # Try Live USDA API if key is present or using DEMO_KEY
        if self.api_key:
            try:
                params = {
                    "api_key": self.api_key,
                    "query": clean_name,
                    "pageSize": 1,
                    "dataType": ["Survey (FNDDS)", "Foundation"]
                }
                res = requests.get(self.BASE_URL, params=params, timeout=1.2)
                if res.status_code == 200:
                    data = res.json()
                    foods = data.get("foods", [])
                    if foods:
                        food = foods[0]
                        fdc_id = str(food.get("fdcId", ""))
                        nutrients = food.get("foodNutrients", [])

                        cals = self._extract_nutrient(nutrients, ["Energy", "ENERGY"], 100.0)
                        prot = self._extract_nutrient(nutrients, ["Protein", "PROTEIN"], 0.0)
                        carbs = self._extract_nutrient(nutrients, ["Carbohydrate, by difference"], 0.0)
                        fats = self._extract_nutrient(nutrients, ["Total lipid (fat)"], 0.0)

                        factor = max(0.5, quantity)
                        return {
                            "fdc_id": fdc_id,
                            "macros": Macronutrients(
                                calories=round(cals * factor, 1),
                                protein_g=round(prot * factor, 1),
                                carbs_g=round(carbs * factor, 1),
                                fats_g=round(fats * factor, 1)
                            )
                        }
            except Exception as e:
                pass

        # Fallback to local USDA database table
        matched = None
        for key in self.FALLBACK_DATABASE:
            if key in clean_name or clean_name in key:
                matched = self.FALLBACK_DATABASE[key]
                break

        if not matched:
            matched = {"calories": 150.0, "protein": 10.0, "carbs": 15.0, "fats": 5.0, "unit": "1 serving"}

        factor = max(0.5, quantity)
        return {
            "fdc_id": "usda_fallback_matched",
            "macros": Macronutrients(
                calories=round(matched["calories"] * factor, 1),
                protein_g=round(matched["protein"] * factor, 1),
                carbs_g=round(matched["carbs"] * factor, 1),
                fats_g=round(matched["fats"] * factor, 1)
            )
        }

    def _extract_nutrient(self, nutrients: list, names: list, default: float) -> float:
        for n in nutrients:
            name = n.get("nutrientName", "")
            if any(k.lower() in name.lower() for k in names):
                return float(n.get("value", default))
        return default

usda_client = USDAClient()
