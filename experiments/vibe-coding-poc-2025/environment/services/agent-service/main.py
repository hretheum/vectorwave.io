# Agent Service - MONOLITHIC VERSION for Task B
# This 800-line file needs refactoring into separate modules
# Current structure violates SRP, has high coupling, and is hard to test

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
import httpx
import asyncio
from datetime import datetime
from crewai import Agent, Task, Crew
from langchain.tools import BaseTool

app = FastAPI(title="Agent Service - Monolithic")

# ============= LINES 1-200: AGENT INITIALIZATION =============

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RECIPE_SERVICE_URL = os.getenv("RECIPE_SERVICE_URL", "http://recipe-service:8000")

# Agent configuration (hardcoded, should be configurable)
AGENT_CONFIG = {
    "recipe_specialist": {
        "role": "Recipe Specialist",
        "goal": "Find and recommend recipes based on user preferences",
        "backstory": "You are a culinary expert with deep knowledge of recipes",
        "verbose": True,
        "allow_delegation": False
    },
    "price_analyst": {
        "role": "Price Analyst",
        "goal": "Calculate costs and find best prices for ingredients",
        "backstory": "You are an expert at finding the best grocery deals",
        "verbose": True,
        "allow_delegation": False
    },
    "shopping_assistant": {
        "role": "Shopping Assistant",
        "goal": "Create optimized shopping lists",
        "backstory": "You help people shop efficiently",
        "verbose": True,
        "allow_delegation": False
    }
}

# Global agent instances (bad practice, should use dependency injection)
recipe_agent = None
price_agent = None
shopping_agent = None

def initialize_agents():
    """Initialize all agents - called on startup"""
    global recipe_agent, price_agent, shopping_agent
    
    # Recipe Specialist Agent
    recipe_agent = Agent(
        role=AGENT_CONFIG["recipe_specialist"]["role"],
        goal=AGENT_CONFIG["recipe_specialist"]["goal"],
        backstory=AGENT_CONFIG["recipe_specialist"]["backstory"],
        verbose=AGENT_CONFIG["recipe_specialist"]["verbose"],
        allow_delegation=AGENT_CONFIG["recipe_specialist"]["allow_delegation"],
        tools=[RecipeSearchTool(), DietaryFilterTool()]
    )
    
    # Price Analyst Agent
    price_agent = Agent(
        role=AGENT_CONFIG["price_analyst"]["role"],
        goal=AGENT_CONFIG["price_analyst"]["goal"],
        backstory=AGENT_CONFIG["price_analyst"]["backstory"],
        verbose=AGENT_CONFIG["price_analyst"]["verbose"],
        allow_delegation=AGENT_CONFIG["price_analyst"]["allow_delegation"],
        tools=[PriceComparisonTool(), BudgetOptimizerTool()]
    )
    
    # Shopping Assistant Agent
    shopping_agent = Agent(
        role=AGENT_CONFIG["shopping_assistant"]["role"],
        goal=AGENT_CONFIG["shopping_assistant"]["goal"],
        backstory=AGENT_CONFIG["shopping_assistant"]["backstory"],
        verbose=AGENT_CONFIG["shopping_assistant"]["verbose"],
        allow_delegation=AGENT_CONFIG["shopping_assistant"]["allow_delegation"],
        tools=[ShoppingListTool(), StoreOptimizerTool()]
    )

# ============= LINES 201-400: TOOL DEFINITIONS =============
class RecipeSearchTool(BaseTool):
    """Tool for searching recipes"""
    name = "recipe_search"
    description = "Search for recipes based on ingredients and preferences"
    
    def _run(self, query: str) -> str:
        """Execute recipe search"""
        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{RECIPE_SERVICE_URL}/recipes/search",
                    json={"query": query}
                )
                return json.dumps(response.json())
        except Exception as e:
            return f"Error searching recipes: {str(e)}"
    
    async def _arun(self, query: str) -> str:
        """Async version - not implemented"""
        raise NotImplementedError

class DietaryFilterTool(BaseTool):
    """Tool for filtering by dietary restrictions"""
    name = "dietary_filter"
    description = "Filter recipes by dietary restrictions"
    
    def _run(self, restrictions: str) -> str:
        """Apply dietary filters"""
        # Simplified implementation
        return json.dumps({
            "filtered": True,
            "restrictions": restrictions.split(",")
        })
    
    async def _arun(self, restrictions: str) -> str:
        raise NotImplementedError

class PriceComparisonTool(BaseTool):
    """Tool for comparing prices across stores"""
    name = "price_comparison"
    description = "Compare ingredient prices across different stores"
    
    def _run(self, ingredients: str) -> str:
        """Compare prices"""
        # Mock implementation - should call price service
        ingredient_list = ingredients.split(",")
        prices = {}
        for ingredient in ingredient_list:
            prices[ingredient] = {
                "walmart": 2.99,
                "kroger": 3.49,
                "whole_foods": 4.99
            }
        return json.dumps(prices)
    
    async def _arun(self, ingredients: str) -> str:
        raise NotImplementedError

class BudgetOptimizerTool(BaseTool):
    """Tool for optimizing shopping budget"""
    name = "budget_optimizer"
    description = "Optimize shopping list for budget"
    
    def _run(self, budget: str) -> str:
        """Optimize for budget"""
        return json.dumps({
            "optimized": True,
            "budget": float(budget),
            "savings": 15.50
        })
    
    async def _arun(self, budget: str) -> str:
        raise NotImplementedError

class ShoppingListTool(BaseTool):
    """Tool for creating shopping lists"""
    name = "shopping_list"
    description = "Create optimized shopping list"
    
    def _run(self, items: str) -> str:
        """Create shopping list"""
        return json.dumps({
            "list": items.split(","),
            "organized_by_aisle": True
        })
    
    async def _arun(self, items: str) -> str:
        raise NotImplementedError

class StoreOptimizerTool(BaseTool):
    """Tool for optimizing store selection"""
    name = "store_optimizer"
    description = "Find best stores for shopping"
    
    def _run(self, location: str) -> str:
        """Optimize store selection"""
        return json.dumps({
            "recommended_stores": ["Walmart", "Kroger"],
            "estimated_savings": 20.00
        })
    
    async def _arun(self, location: str) -> str:
        raise NotImplementedError
# ============= LINES 401-600: COORDINATION LOGIC =============

class AgentCoordinator:
    """Handles coordination between multiple agents - tightly coupled"""
    
    def __init__(self):
        self.recipe_agent = recipe_agent
        self.price_agent = price_agent
        self.shopping_agent = shopping_agent
        self.execution_history = []
    
    async def execute_recipe_workflow(self, user_query: str) -> Dict[str, Any]:
        """Execute full recipe workflow - monolithic method doing too much"""
        
        # Step 1: Recipe Search (Sequential - could be parallel)
        recipe_task = Task(
            description=f"Find recipes for: {user_query}",
            agent=self.recipe_agent
        )
        
        recipe_crew = Crew(
            agents=[self.recipe_agent],
            tasks=[recipe_task],
            verbose=True
        )
        
        recipe_result = recipe_crew.kickoff()
        
        # Step 2: Price Analysis (Depends on recipe result)
        if recipe_result:
            price_task = Task(
                description=f"Analyze prices for ingredients: {recipe_result}",
                agent=self.price_agent
            )
            
            price_crew = Crew(
                agents=[self.price_agent],
                tasks=[price_task],
                verbose=True
            )
            
            price_result = price_crew.kickoff()
        else:
            price_result = None
        
        # Step 3: Shopping List (Depends on both previous results)
        if recipe_result and price_result:
            shopping_task = Task(
                description=f"Create shopping list based on: {recipe_result} with prices: {price_result}",
                agent=self.shopping_agent
            )
            
            shopping_crew = Crew(
                agents=[self.shopping_agent],
                tasks=[shopping_task],
                verbose=True
            )
            
            shopping_result = shopping_crew.kickoff()
        else:
            shopping_result = None
        
        # Aggregate results (complex logic mixed with coordination)
        final_result = {
            "query": user_query,
            "recipes": self._parse_recipe_result(recipe_result),
            "prices": self._parse_price_result(price_result),
            "shopping_list": self._parse_shopping_result(shopping_result),
            "timestamp": datetime.now().isoformat(),
            "execution_time": self._calculate_execution_time()
        }
        
        # Store in history (side effect in coordination logic)
        self.execution_history.append(final_result)
        
        # Send metrics (another responsibility mixed in)
        self._send_metrics(final_result)
        
        return final_result
    
    def _parse_recipe_result(self, result: Any) -> List[Dict]:
        """Parse recipe results - should be in separate parser"""
        if not result:
            return []
        try:
            # Complex parsing logic
            if isinstance(result, str):
                data = json.loads(result)
            else:
                data = result
            
            recipes = []
            # More parsing logic...
            return recipes
        except Exception as e:
            print(f"Error parsing recipe result: {e}")
            return []
    
    def _parse_price_result(self, result: Any) -> Dict:
        """Parse price results - should be in separate parser"""
        if not result:
            return {}
        try:
            # Complex parsing logic
            return {}
        except Exception as e:
            print(f"Error parsing price result: {e}")
            return {}
    
    def _parse_shopping_result(self, result: Any) -> List:
        """Parse shopping results - should be in separate parser"""
        if not result:
            return []
        try:
            # Complex parsing logic
            return []
        except Exception as e:
            print(f"Error parsing shopping result: {e}")
            return []
    
    def _calculate_execution_time(self) -> float:
        """Calculate execution time - metric logic mixed with coordination"""
        # Should be in separate metrics module
        return 0.0
    
    def _send_metrics(self, result: Dict) -> None:
        """Send metrics to monitoring - another responsibility"""
        # Should be in separate metrics service
        pass

# Global coordinator instance (bad practice)
coordinator = AgentCoordinator()
# ============= LINES 601-800: API ENDPOINTS =============

class QueryRequest(BaseModel):
    query: str
    preferences: Optional[Dict[str, Any]] = {}
    budget: Optional[float] = None

class QueryResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup"""
    initialize_agents()
    print("Agents initialized successfully")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    agent_status = {
        "recipe_agent": recipe_agent is not None,
        "price_agent": price_agent is not None,
        "shopping_agent": shopping_agent is not None
    }
    
    return {
        "status": "healthy" if all(agent_status.values()) else "unhealthy",
        "service": "agent-service",
        "agents": agent_status,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Main endpoint for processing queries - doing too much"""
    try:
        # Validation logic (should be separate)
        if not request.query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        if len(request.query) > 500:
            raise HTTPException(status_code=400, detail="Query too long")
        
        # Check agent availability (should be middleware)
        if not all([recipe_agent, price_agent, shopping_agent]):
            raise HTTPException(status_code=503, detail="Agents not initialized")
        
        # Execute workflow (all logic in one place)
        result = await coordinator.execute_recipe_workflow(request.query)
        
        # Post-processing (should be separate)
        if request.budget:
            result = apply_budget_filter(result, request.budget)
        
        if request.preferences:
            result = apply_preferences(result, request.preferences)
        
        # Analytics tracking (another responsibility)
        track_query_analytics(request, result)
        
        return QueryResponse(
            success=True,
            data=result
        )
        
    except Exception as e:
        # Error handling (should use proper error handler)
        print(f"Error processing query: {e}")
        return QueryResponse(
            success=False,
            data={},
            error=str(e)
        )

@app.get("/agents/status")
async def get_agent_status():
    """Get detailed agent status - exposing internals"""
    return {
        "recipe_agent": {
            "initialized": recipe_agent is not None,
            "config": AGENT_CONFIG["recipe_specialist"]
        },
        "price_agent": {
            "initialized": price_agent is not None,
            "config": AGENT_CONFIG["price_analyst"]
        },
        "shopping_agent": {
            "initialized": shopping_agent is not None,
            "config": AGENT_CONFIG["shopping_assistant"]
        }
    }

@app.post("/agents/reset")
async def reset_agents():
    """Reset all agents - dangerous endpoint"""
    global recipe_agent, price_agent, shopping_agent
    recipe_agent = None
    price_agent = None
    shopping_agent = None
    initialize_agents()
    return {"message": "Agents reset successfully"}

# Helper functions mixed with API logic (should be separate)

def apply_budget_filter(result: Dict, budget: float) -> Dict:
    """Apply budget filtering to results"""
    # Complex filtering logic that should be in a separate module
    filtered_result = result.copy()
    # ... filtering logic ...
    return filtered_result

def apply_preferences(result: Dict, preferences: Dict) -> Dict:
    """Apply user preferences to results"""
    # Complex preference logic that should be in a separate module
    filtered_result = result.copy()
    # ... preference logic ...
    return filtered_result

def track_query_analytics(request: QueryRequest, result: Dict) -> None:
    """Track analytics for queries"""
    # Analytics logic that should be in a separate service
    analytics_data = {
        "query": request.query,
        "timestamp": datetime.now().isoformat(),
        "result_count": len(result.get("recipes", [])),
        "has_budget": request.budget is not None
    }
    # Send to analytics service...
    print(f"Analytics tracked: {analytics_data}")

# More helper functions that don't belong here...

def validate_recipe_data(data: Dict) -> bool:
    """Validate recipe data structure"""
    required_fields = ["id", "name", "ingredients"]
    return all(field in data for field in required_fields)

def calculate_total_cost(prices: Dict) -> float:
    """Calculate total cost from prices"""
    total = 0.0
    for item, store_prices in prices.items():
        if isinstance(store_prices, dict):
            total += min(store_prices.values())
    return total

# END OF MONOLITHIC FILE - 800+ lines
# This file violates:
# - Single Responsibility Principle (multiple responsibilities)
# - Open/Closed Principle (hard to extend)
# - Dependency Inversion (concrete dependencies)
# - High coupling, low cohesion
# - Difficult to test individual components
# - No clear separation of concerns