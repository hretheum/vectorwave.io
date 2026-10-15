# Recipe Service - Starting Code for Task A
# Current implementation WITHOUT rating system

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import asyncpg
import os
from datetime import datetime

app = FastAPI(title="Recipe Service")

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")

class Recipe(BaseModel):
    id: str
    name: str
    ingredients: List[str]
    instructions: List[str]
    prep_time: int
    difficulty: str
    created_at: datetime

class RecipeSearch(BaseModel):
    query: str
    dietary_restrictions: Optional[List[str]] = []
    max_prep_time: Optional[int] = None

# Existing endpoints
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "recipe-service"}

@app.get("/recipes/{recipe_id}")
async def get_recipe(recipe_id: str):
    """Get a single recipe by ID"""
    # Simplified implementation
    return {
        "id": recipe_id,
        "name": "Pasta Carbonara",
        "ingredients": ["pasta", "eggs", "bacon", "parmesan"],
        "instructions": ["Cook pasta", "Fry bacon", "Mix eggs", "Combine"],
        "prep_time": 20,
        "difficulty": "easy",
        "created_at": datetime.now()
    }

@app.post("/recipes/search")
async def search_recipes(search: RecipeSearch):
    """Search for recipes"""
    # Simplified implementation
    return {
        "results": [
            {
                "id": "recipe_001",
                "name": "Pasta Carbonara",
                "prep_time": 20,
                "difficulty": "easy"
            }
        ],
        "total": 1
    }

# TODO: Task A - Add Rating System
# Requirements:
# 1. POST /recipes/{id}/rating endpoint
# 2. Rating model (1-5 with half-star precision)
# 3. Store ratings in PostgreSQL
# 4. Calculate average ratings
# 5. Handle user sessions for anonymous ratings
# 6. Update existing rating if user re-rates
# 7. Minimum 3 ratings before showing average
# 8. Add rating info to GET /recipes/{id} response