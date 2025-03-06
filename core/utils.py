import logging
from openai import OpenAI
import pandas as pd

from django.conf import settings
from .models import Restaurant, Reservation
from datetime import datetime
import json
from typing import Dict, List, Any
import os
from django.db.models import Q
from .services import RestaurantCatalogService, ReservationService, RecommendationService, LocationService
import requests

# Set up logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# OpenAI function definitions
OPENAI_FUNCTIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_restaurants",
            "description": "Search for restaurants based on various criteria",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location to search for restaurants"
                    },
                    "cuisine_type": {
                        "type": "string",
                        "description": "Type of cuisine"
                    },
                    "price_range": {
                        "type": "string",
                        "enum": ["$", "$$", "$$$", "$$$$"],
                        "description": "Price range for restaurants"
                    },
                    "dietary_restrictions": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of dietary restrictions"
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Check restaurant availability for a specific date and time",
            "parameters": {
                "type": "object",
                "properties": {
                    "restaurant_id": {
                        "type": "integer",
                        "description": "ID of the restaurant"
                    },
                    "date": {
                        "type": "string",
                        "format": "date",
                        "description": "Date for the reservation (YYYY-MM-DD)"
                    },
                    "time": {
                        "type": "string",
                        "format": "time",
                        "description": "Time for the reservation (HH:MM)"
                    },
                    "party_size": {
                        "type": "integer",
                        "description": "Number of people"
                    }
                },
                "required": ["restaurant_id", "date", "time", "party_size"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "make_reservation",
            "description": "Make a restaurant reservation",
            "parameters": {
                "type": "object",
                "properties": {
                    "restaurant_id": {
                        "type": "integer",
                        "description": "ID of the restaurant"
                    },
                    "date": {
                        "type": "string",
                        "format": "date",
                        "description": "Date for the reservation (YYYY-MM-DD)"
                    },
                    "time": {
                        "type": "string",
                        "format": "time",
                        "description": "Time for the reservation (HH:MM)"
                    },
                    "party_size": {
                        "type": "integer",
                        "description": "Number of people"
                    },
                    "special_requests": {
                        "type": "string",
                        "description": "Any special requests for the reservation"
                    }
                },
                "required": ["restaurant_id", "date", "time", "party_size"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_restaurants",
            "description": "Get personalized restaurant recommendations",
            "parameters": {
                "type": "object",
                "properties": {
                    "occasion": {
                        "type": "string",
                        "description": "Type of occasion (e.g., date, business, casual, family)",
                        "enum": ["date", "business", "casual", "family", "celebration"]
                    },
                    "cuisine_preferences": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Preferred types of cuisine"
                    },
                    "dietary_restrictions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Dietary restrictions"
                    },
                    "price_range": {
                        "type": "string",
                        "enum": ["$", "$$", "$$$", "$$$$"],
                        "description": "Preferred price range"
                    },
                    "location": {
                        "type": "string",
                        "description": "Preferred location"
                    }
                },
                "required": ["occasion"]
            }
        }
    }
]

# Function removed as per user request

class RestaurantAI:

    def __init__(self):
        try:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API key is not set")
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            raise

    def process_user_input(self, user_input, user=None, csv_file_path=None):
        """Process user input and return appropriate response using OpenAI function calling"""
        if csv_file_path:
            import_restaurants_from_csv(csv_file_path)

        """Process user input and return appropriate response using OpenAI function calling"""
        try:
            if not user_input:
                return "I didn't receive any input. How can I help you?"

            logger.info(f"Processing user input: {user_input}")
            
            # Create the messages list with system message for better context
            messages = [
                {"role": "system", "content": "You are an expert restaurant recommender. Help users find the perfect restaurant by considering their preferences, occasion, and needs. Be conversational and provide detailed, personalized recommendations."},
                {"role": "user", "content": user_input}
            ]

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-0125",  # Using the latest model version
                messages=messages,
                tools=OPENAI_FUNCTIONS,
                tool_choice="auto"
            )

            logger.info("Received response from OpenAI")
            response_message = response.choices[0].message

            if response_message.tool_calls:
                tool_call = response_message.tool_calls[0]
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                logger.info(f"Function called: {function_name} with args: {function_args}")
                
                if function_name == "search_restaurants":
                    return self._handle_restaurant_search(function_args)
                elif function_name == "check_availability":
                    return self._handle_availability_check(function_args)
                elif function_name == "make_reservation":
                    if not user:
                        return "To make a reservation, please log in first. However, I can still help you find restaurants and check availability!"
                    return self._handle_reservation(function_args, user)
                elif function_name == "recommend_restaurants":
                    return self._handle_restaurant_recommendations(function_args)
            
            # Ensure we always return a string
            if not response_message.content:
                return "I understand your request. How else can I help you?"
                
            return response_message.content

        except Exception as e:
            logger.error(f"Error in process_user_input: {str(e)}", exc_info=True)
            return "I apologize, but I encountered an error processing your request. Please try again or rephrase your question."

    def _handle_restaurant_search(self, args):
        """Handle restaurant search based on provided criteria"""
        try:
            query = Restaurant.objects.all()

            # Make cuisine type search case-insensitive and partial match
            if "cuisine_type" in args and args["cuisine_type"]:
                query = query.filter(cuisine_type__icontains=args["cuisine_type"])
            
            # Location is stored in the address field, make it case-insensitive and partial match
            if "location" in args and args["location"]:
                query = query.filter(address__icontains=args["location"])
            
            if "price_range" in args and args["price_range"]:
                query = query.filter(price_range=args["price_range"])
            
            if "dietary_restrictions" in args and args["dietary_restrictions"]:
                for restriction in args["dietary_restrictions"]:
                    query = query.filter(dietary_options__contains=[restriction])

            restaurants = query[:5]  # Limit to top 5 results
            
            if not restaurants:
                # Auto-populate restaurants from OpenAI when no results found
                try:
                    new_restaurants = self._populate_restaurants_from_ai(args)
                    if new_restaurants:
                        return self._format_restaurant_results(new_restaurants)
                except Exception as e:
                    logger.error(f"Error auto-populating restaurants: {str(e)}")
            
            return self._format_restaurant_results(restaurants)

        except Exception as e:
            logger.error(f"Error in _handle_restaurant_search: {str(e)}", exc_info=True)
            return "Sorry, I encountered an error while searching for restaurants."

    def _populate_restaurants_from_ai(self, search_args):
        """Populate restaurant data using OpenAI when no results found"""
        try:
            # Create a prompt for OpenAI to generate restaurant data
            prompt = f"Generate 5 realistic restaurant entries for {search_args.get('cuisine_type', 'various')} cuisine "
            prompt += f"in {search_args.get('location', 'the area')}. Include name, address, price range ($-$$$$), "
            prompt += "rating (1-5), cuisine type, and dietary options. Format as JSON."

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-0125",
                messages=[
                    {"role": "system", "content": "You are a restaurant database expert. Provide realistic restaurant data in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )

            # Parse the JSON response
            restaurants_data = json.loads(response.choices[0].message.content)
            new_restaurants = []

            # Create restaurant entries in the database
            for restaurant_data in restaurants_data.get('restaurants', []):
                restaurant = Restaurant.objects.create(
                    name=restaurant_data['name'],
                    address=restaurant_data['address'],
                    cuisine_type=restaurant_data.get('cuisine_type', search_args.get('cuisine_type', '')),
                    price_range=restaurant_data.get('price_range', '$$'),
                    rating=float(restaurant_data.get('rating', 4.0)),
                    dietary_options=restaurant_data.get('dietary_options', []),
                    operating_hours=restaurant_data.get('operating_hours', {
                        'monday': '11:00-22:00',
                        'tuesday': '11:00-22:00',
                        'wednesday': '11:00-22:00',
                        'thursday': '11:00-22:00',
                        'friday': '11:00-23:00',
                        'saturday': '11:00-23:00',
                        'sunday': '11:00-22:00'
                    }),
                    capacity=restaurant_data.get('capacity', 50)
                )
                new_restaurants.append(restaurant)

            logger.info(f"Successfully auto-populated {len(new_restaurants)} restaurants")
            return new_restaurants

        except Exception as e:
            logger.error(f"Error in _populate_restaurants_from_ai: {str(e)}")
            raise

    def _format_restaurant_results(self, restaurants):
        """Format restaurant results into a readable string"""
        if not restaurants:
            return "Sorry, I couldn't find or generate any restaurant information. Please try a different search."

        result = "Here are some restaurants that match your criteria:\n\n"
        for restaurant in restaurants:
            result += f"- {restaurant.name} ({restaurant.price_range})\n"
            result += f"  Cuisine: {restaurant.cuisine_type}\n"
            result += f"  Address: {restaurant.address}\n"
            result += f"  Rating: {restaurant.rating}/5.0\n"
            if restaurant.dietary_options:
                result += f"  Dietary Options: {', '.join(restaurant.dietary_options)}\n"
            result += "\n"
        
        return result

    def _handle_availability_check(self, args):
        """Check restaurant availability"""
        try:
            restaurant = Restaurant.objects.get(id=args["restaurant_id"])
            datetime_str = f"{args['date']} {args['time']}"
            reservation_time = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
            
            # Check if restaurant is open
            day_of_week = reservation_time.strftime('%A').lower()
            if day_of_week not in restaurant.operating_hours:
                return f"Sorry, {restaurant.name} is closed on {day_of_week}."

            # Check existing reservations
            existing_reservations = Reservation.objects.filter(
                restaurant=restaurant,
                reservation_time=reservation_time,
                status='confirmed'
            )
            
            total_guests = sum(r.party_size for r in existing_reservations)
            available_capacity = restaurant.capacity - total_guests
            
            if available_capacity >= args["party_size"]:
                return f"Great news! {restaurant.name} is available for {args['party_size']} people at {args['time']} on {args['date']}."
            else:
                return f"Sorry, {restaurant.name} is fully booked at that time. Maybe try a different time?"
            
        except Restaurant.DoesNotExist:
            return "Sorry, I couldn't find that restaurant."
        except Exception as e:
            logger.error(f"Error in _handle_availability_check: {str(e)}", exc_info=True)
            return "Sorry, I encountered an error checking availability."

    def _handle_reservation(self, args, user):
        """Handle restaurant reservation"""
        try:
            restaurant = Restaurant.objects.get(id=args["restaurant_id"])
            datetime_str = f"{args['date']} {args['time']}"
            reservation_time = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')

            # Create new reservation
            reservation = Reservation.objects.create(
                restaurant=restaurant,
                user=user,
                party_size=args["party_size"],
                reservation_time=reservation_time,
                special_requests=args.get("special_requests", ""),
                status="confirmed"
            )
            
            return (f"Perfect! I've made a reservation for {args['party_size']} people at "
                   f"{restaurant.name} on {args['date']} at {args['time']}.\n"
                   f"Your reservation ID is: {reservation.id}")
            
        except Restaurant.DoesNotExist:
            return "Sorry, I couldn't find that restaurant."
        except Exception as e:
            logger.error(f"Error in _handle_reservation: {str(e)}", exc_info=True)
            return "Sorry, I encountered an error making the reservation."

    def _handle_restaurant_recommendations(self, args):
        """Handle personalized restaurant recommendations"""
        try:
            query = Restaurant.objects.all()
            
            # Filter by price range if specified
            if "price_range" in args:
                query = query.filter(price_range=args["price_range"])
            
            # Filter by cuisine preferences
            if "cuisine_preferences" in args and args["cuisine_preferences"]:
                query = query.filter(cuisine_type__in(args["cuisine_preferences"]))
            
            # Filter by dietary restrictions
            if "dietary_restrictions" in args and args["dietary_restrictions"]:
                for restriction in args["dietary_restrictions"]:
                    query = query.filter(dietary_options__contains=[restriction])
            
            # Order by rating and get top matches
            restaurants = query.order_by('-rating')[:5]
            
            if not restaurants:
                return "I couldn't find any restaurants matching your specific criteria. Would you like me to broaden the search?"
            
            # Craft a personalized response based on occasion
            occasion_intro = {
                "date": "Here are some romantic spots perfect for a date night:",
                "business": "These restaurants offer a professional atmosphere ideal for business meetings:",
                "casual": "For a relaxed dining experience, consider these options:",
                "family": "These family-friendly restaurants should be perfect:",
                "celebration": "These restaurants are great for special celebrations:"
            }
            
            result = f"{occasion_intro.get(args.get('occasion', 'casual'), 'Here are some recommendations:')}\n\n"
            
            for restaurant in restaurants:
                result += f"🍽️ {restaurant.name} ({restaurant.price_range})\n"
                result += f"   • Cuisine: {restaurant.cuisine_type}\n"
                result += f"   • Rating: {restaurant.rating}/5.0\n"
                result += f"   • Address: {restaurant.address}\n"
                if restaurant.dietary_options:
                    result += f"   • Dietary options: {', '.join(restaurant.dietary_options)}\n"
                result += "\n"
            
            result += "Would you like to check availability or make a reservation at any of these restaurants?"
            
            return result
            
        except Exception as e:
            logger.error(f"Error in _handle_restaurant_recommendations: {str(e)}", exc_info=True)
            return "Sorry, I encountered an error while finding restaurant recommendations."

def extract_criteria_from_message(message: str) -> Dict[str, Any]:
    """
    Use OpenAI to extract search criteria from user message
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """You are a restaurant recommendation assistant. 
                Extract search criteria from user messages. Return only a JSON object with these possible keys:
                - cuisine (string)
                - price_range (string: $, $$, or $$$)
                - location (string)
                - occasion (string)"""},
                {"role": "user", "content": message}
            ],
            response_format={ "type": "json_object" }
        )
        
        criteria = json.loads(response.choices[0].message.content)
        return criteria
    except Exception as e:
        logger.error(f"Error extracting criteria: {str(e)}")
        return {}

def generate_restaurant_response(message: str) -> str:
    """
    Generate a response based on user message and restaurant recommendations
    """
    try:
        # Extract search criteria from user message
        criteria = extract_criteria_from_message(message)
        
        # Get restaurant recommendations
        restaurants = get_restaurant_recommendations(criteria)
        
        # Format restaurant list for OpenAI
        restaurant_list = "\n".join([
            f"- {r.name}: {r.cuisine_type} cuisine, {r.price_range}, located in {r.address}"
            for r in restaurants
        ])
        
        if not restaurant_list:
            restaurant_list = "No specific restaurants found matching your criteria."
        
        # Generate natural language response
        prompt = f"""Based on the user's message: "{message}"
        Here are the available restaurants:
        {restaurant_list}
        
        Please provide a helpful response recommending these restaurants in a natural way.
        If no restaurants match the criteria exactly, recommend the available ones that might be of interest."""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful restaurant recommendation assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=250
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}", exc_info=True)
        return "I apologize, but I encountered an error while finding restaurant recommendations. Please try again."

def get_restaurant_recommendations(criteria: Dict[str, Any]) -> List[Restaurant]:
    """
    Get restaurant recommendations based on given criteria
    """
    # Use the dedicated RecommendationService instead of direct DB queries
    return RecommendationService.get_recommendations(criteria)

def generate_restaurant_response(user_message):
    """
    Generate a response to a user message using OpenAI API
    """
    try:
        api_key = settings.OPENAI_API_KEY
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful restaurant assistant. You provide information about restaurants, help with reservations, and give recommendations. Keep responses concise and helpful."},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 300
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            logger.error(f"Error from OpenAI API: {response.status_code} - {response.text}")
            return "Sorry, I'm having trouble processing your request right now. Please try again later."
            
    except Exception as e:
        logger.error(f"Error generating restaurant response: {str(e)}")
        return "I apologize, but I encountered an error. Please try again later."


import os
import logging
import openai
from django.conf import settings

logger = logging.getLogger(__name__)

# Configure OpenAI API key from Django settings
openai.api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY'))

class RestaurantAI:
    """
    Class to handle all AI interactions for restaurant recommendations,
    query understanding, and conversational abilities.
    """
    def __init__(self):
        self.conversation_history = []
        self.model = "gpt-4" # Update to "gpt-4.5-turbo" or actual model name when available
    
    def _get_system_prompt(self):
        """Return the system prompt that defines the AI's role"""
        return """You are RestaurantAI, a helpful assistant specializing in restaurant recommendations, 
        cuisine information, and dining experiences. Provide helpful, accurate information about restaurants, 
        food, reservations, and dining experiences. If users ask about making reservations, you can help them 
        understand availability but direct them to use the app's reservation system for actual bookings. 
        When recommending restaurants, be specific about cuisine types, price ranges, and special features.
        If you don't know something, admit it rather than making up information."""
    
    def process_user_input(self, user_message, user=None):
        """Process user input and generate a response"""
        try:
            # Add user message to conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            
            # Prepare messages for API call
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                # Add contextual information about the user if available
                *([] if not user or user.is_anonymous else [
                    {"role": "system", "content": f"The user's name is {user.username}. Personalize your responses appropriately."}
                ]),
                # Add conversation history (limited to last 10 exchanges for brevity)
                *self.conversation_history[-10:]
            ]
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=800,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                stream=False
            )
            
            # Extract response content
            ai_response = response.choices[0].message["content"]
            
            # Add AI response to conversation history
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error in OpenAI API call: {str(e)}")
            return "I'm sorry, I encountered an error while processing your request. Please try again later."
    
    def generate_streaming_response(self, user_message, user=None):
        """Generate a streaming response for real-time conversation"""
        try:
            # Add user message to conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            
            # Prepare messages for API call
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                # Add contextual information about the user if available
                *([] if not user or user.is_anonymous else [
                    {"role": "system", "content": f"The user's name is {user.username}. Personalize your responses appropriately."}
                ]),
                # Add conversation history (limited to last 10 exchanges for brevity)
                *self.conversation_history[-10:]
            ]
            
            # Call OpenAI API with streaming enabled
            stream = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=800,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                stream=True
            )
            
            # Return the stream object to be processed by the view
            return stream
            
        except Exception as e:
            logger.error(f"Error in OpenAI streaming API call: {str(e)}")
            return None
    
    def handle_stream_response(self, stream):
        """Process the streaming response and collect the full message"""
        full_response = ""
        try:
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content_chunk = chunk.choices[0].delta.content
                    full_response += content_chunk
                    yield chunk
                    
            # After streaming completes, add the full response to conversation history
            self.conversation_history.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            logger.error(f"Error processing stream: {str(e)}")


def generate_restaurant_response(message):
    """
    Utility function to generate a response regarding restaurant inquiries.
    This is a simplified version that doesn't track conversation history.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Update to the appropriate model when available
            messages=[
                {"role": "system", "content": "You are a helpful assistant specializing in restaurant recommendations and information."},
                {"role": "user", "content": message}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message["content"]
    except Exception as e:
        logger.error(f"Error in generate_restaurant_response: {str(e)}")
        return "I apologize, but I'm having trouble processing your request right now. Please try again later."
