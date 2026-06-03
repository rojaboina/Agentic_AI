"""LangChain + Groq LLM integration for AI Nutrition Coach."""
import os
from typing import Optional, Dict, Any, List
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
import json


class NutritionCoach:
    """AI Nutrition Coach powered by Groq and LangChain."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.1-8b-instant"):
        """Initialize the nutrition coach."""
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.llm = None
        self.error = None
        
        if self.api_key:
            self._initialize_llm()
        else:
            self.error = "GROQ_API_KEY environment variable not set"
    
    def _initialize_llm(self):
        """Initialize LangChain LLM and chains."""
        try:
            self.llm = ChatGroq(
                temperature=0.7,
                groq_api_key=self.api_key,
                model_name=self.model,
                max_tokens=1024
            )
            
            # Create prompt template for nutrition insights
            self.insight_template = PromptTemplate(
                input_variables=["daily_totals", "goals", "meal_breakdown"],
                template="""You are a helpful nutrition advisor. Based on the user's daily nutrition data, provide a 2-3 sentence personalized insight about their nutrition.

Daily Totals:
- Calories: {daily_totals}

Goals:
- {goals}

Meal Breakdown:
- {meal_breakdown}

Provide encouraging, balanced feedback. If macros are imbalanced, suggest adjustments. Mention if they're on track with their calorie goal."""
            )
            
            # Create prompt template for chat
            self.chat_template = PromptTemplate(
                input_variables=["context", "user_question"],
                template="""You are a friendly and knowledgeable nutrition coach. You have access to the user's nutrition data and can provide personalized advice.

Nutrition Context:
{context}

User Question: {user_question}

Important guidelines:
- Base your suggestions on the provided nutrition data
- Be encouraging and non-judgmental
- Avoid extreme diet recommendations
- Include a disclaimer that you're not a doctor or nutritionist
- If you don't have enough information, say so
- Provide practical, actionable advice

Response:"""
            )
            
            self.error = None
        except Exception as e:
            self.error = f"Failed to initialize Groq: {str(e)}"
            self.llm = None
    
    def is_available(self) -> bool:
        """Check if LLM is available."""
        return self.llm is not None and self.error is None
    
    def get_error_message(self) -> Optional[str]:
        """Get error message if any."""
        return self.error
    
    def generate_nutrition_insight(self, daily_totals: Dict[str, float], 
                                   goals: Dict[str, float], 
                                   meal_breakdown: Dict[str, Dict[str, float]]) -> str:
        """Generate personalized nutrition insight using LangChain."""
        if not self.is_available():
            return "AI insights unavailable. Please add your Groq API key."
        
        try:
            # Format data for template
            totals_str = ", ".join([f"{k.capitalize()}: {v:.0f}" for k, v in daily_totals.items()])
            goals_str = ", ".join([f"{k.capitalize()}: {v:.0f}" for k, v in goals.items()])
            
            meal_str = ", ".join([
                f"{meal}: {data['calories']:.0f} cal ({data['protein']:.0f}g protein)"
                for meal, data in meal_breakdown.items() if data['count'] > 0
            ])
            
            # Create chain and invoke
            chain = self.insight_template | self.llm
            response = chain.invoke({
                "daily_totals": totals_str,
                "goals": goals_str,
                "meal_breakdown": meal_str or "No meals logged yet"
            })
            
            return response.content if hasattr(response, 'content') else str(response)
        
        except Exception as e:
            return f"Error generating insight: {str(e)}"
    
    def chat(self, user_message: str, nutrition_context: Dict[str, Any]) -> str:
        """Chat with the nutrition coach."""
        if not self.is_available():
            return "AI coach unavailable. Please add your Groq API key."
        
        try:
            # Format context for the coach
            context_str = self._format_context(nutrition_context)
            
            # Create chain and invoke
            chain = self.chat_template | self.llm
            response = chain.invoke({
                "context": context_str,
                "user_question": user_message
            })
            
            return response.content if hasattr(response, 'content') else str(response)
        
        except Exception as e:
            return f"Error in chat: {str(e)}"
    
    def _format_context(self, nutrition_context: Dict[str, Any]) -> str:
        """Format nutrition context for LLM."""
        context_parts = []
        
        if 'daily_totals' in nutrition_context:
            totals = nutrition_context['daily_totals']
            context_parts.append(f"Today's Consumption: {totals['calories']:.0f} cal, "
                               f"{totals['protein']:.0f}g protein, {totals['carbs']:.0f}g carbs, "
                               f"{totals['fats']:.0f}g fats")
        
        if 'goals' in nutrition_context:
            goals = nutrition_context['goals']
            context_parts.append(f"Daily Goals: {goals['calorie_goal']} cal, "
                               f"{goals['protein_goal']}g protein, {goals['carbs_goal']}g carbs, "
                               f"{goals['fats_goal']}g fats")
        
        if 'remaining' in nutrition_context:
            remaining = nutrition_context['remaining']
            context_parts.append(f"Remaining: {remaining['calories']:.0f} cal, "
                               f"{remaining['protein']:.0f}g protein, {remaining['carbs']:.0f}g carbs")
        
        if 'most_logged_foods' in nutrition_context:
            foods = nutrition_context['most_logged_foods']
            if foods:
                food_str = ", ".join([f"{name} ({count}x)" for name, count in foods[:5]])
                context_parts.append(f"Most Logged Foods This Week: {food_str}")
        
        if 'meal_breakdown' in nutrition_context:
            breakdown = nutrition_context['meal_breakdown']
            meals = [f"{meal}: {data['calories']:.0f} cal" 
                    for meal, data in breakdown.items() if data['count'] > 0]
            if meals:
                context_parts.append(f"Meals Logged: {', '.join(meals)}")
        
        return "\n".join(context_parts) if context_parts else "No nutrition data available yet."
