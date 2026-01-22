from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.middleware.csrf import get_token
import json
import logging
from .models import Restaurant, Review, Reservation
from .utils import RestaurantAI, generate_restaurant_response
from .services import (
    RestaurantCatalogService, 
    ReservationService, 
    RecommendationService, 
    LocationService
)
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login, authenticate

logger = logging.getLogger(__name__)

def login_view(request):
    """Custom login view to handle authentication."""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('core:home')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            # Add additional error logging
            logger.warning(f"Login form errors: {form.errors}")
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'core/register.html', {'form': form})


def home(request):
    """Home page view that displays popular restaurants."""
    # Sample popular restaurants data for demonstration
    popular_restaurants = [
        {
            'id': 1,
            'name': 'Bella Vista Italian Kitchen',
            'cuisine_type': 'Italian',
            'price_range': '$$$',
            'rating': 4.8,
            'address': '123 Main St, Downtown',
            'stars': [True, True, True, True, True]  # 5 stars
        },
        {
            'id': 2,
            'name': 'Sakura Japanese Fusion',
            'cuisine_type': 'Japanese',
            'price_range': '$$',
            'rating': 4.6,
            'address': '456 Oak Ave, Midtown',
            'stars': [True, True, True, True, False]  # 4 stars
        },
        {
            'id': 3,
            'name': 'Taco Fiesta Mexican Grill',
            'cuisine_type': 'Mexican',
            'price_range': '$',
            'rating': 4.4,
            'address': '789 Pine St, Uptown',
            'stars': [True, True, True, True, False]  # 4 stars
        },
        {
            'id': 4,
            'name': 'Le Gourmet French Bistro',
            'cuisine_type': 'French',
            'price_range': '$$$$',
            'rating': 4.9,
            'address': '321 Elm St, Riverside',
            'stars': [True, True, True, True, True]  # 5 stars
        },
        {
            'id': 5,
            'name': 'Spice Route Indian Cuisine',
            'cuisine_type': 'Indian',
            'price_range': '$$',
            'rating': 4.7,
            'address': '654 Maple Dr, Westside',
            'stars': [True, True, True, True, True]  # 5 stars
        },
        {
            'id': 6,
            'name': 'Ocean Blue Seafood House',
            'cuisine_type': 'Seafood',
            'price_range': '$$$',
            'rating': 4.5,
            'address': '987 Harbor View, Waterfront',
            'stars': [True, True, True, True, False]  # 4 stars
        }
    ]

    return render(request, 'core/home.html', {
        'popular_restaurants': popular_restaurants
    })

@csrf_exempt
@require_http_methods(["POST"])
def chat_endpoint(request):
    try:
        data = json.loads(request.body)
        message = data.get('message', '')
        
        # Generate response using OpenAI
        response = generate_restaurant_response(message)
        
        return JsonResponse({
            'status': 'success',
            'response': response
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
def restaurant_detail(request, restaurant_id):
    # This is a stub - actual implementation would fetch the restaurant
    restaurant = {"id": restaurant_id, "name": "Example Restaurant"}
    return render(request, 'core/restaurant_detail.html', {'restaurant': restaurant})

@login_required
def my_reservations(request):
    return render(request, 'core/my_reservations.html', {'reservations': []})

@login_required
def cancel_reservation(request, reservation_id):
    # Handle reservation cancellation
    return redirect('core:my_reservations')

def search_restaurants(request):
    return render(request, 'core/search_restaurants.html')

# Chat interface views
def chat_interface(request):
    """Render the chat interface template with necessary context"""
    return render(request, 'core/chat_interface.html', {
        'page_title': 'Chat with Restaurant AI',
    })

@csrf_exempt
def chat_api(request):
    """API endpoint for the chat interface with streaming support"""
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            user_message = data.get('message', '')
            
            # Check if client accepts event-stream (for streaming responses)
            accepts_stream = 'text/event-stream' in request.headers.get('Accept', '')
            
            ai = RestaurantAI()
            
            if accepts_stream:
                # Stream the response
                stream = ai.generate_streaming_response(user_message, request.user)
                
                if not stream:
                    return JsonResponse({'error': 'Failed to generate streaming response'}, status=500)
                
                def event_stream():
                    for chunk in ai.handle_stream_response(stream):
                        yield f"data: {json.dumps(chunk)}\n\n"
                    yield "data: [DONE]\n\n"
                
                response = StreamingHttpResponse(
                    event_stream(),
                    content_type='text/event-stream'
                )
                response['Cache-Control'] = 'no-cache'
                response['X-Accel-Buffering'] = 'no'
                return response
            else:
                # Generate a standard response
                response = ai.process_user_input(user_message, request.user)
                return JsonResponse({'response': response})
        
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    except Exception as e:
        logger.error(f"Error in chat_api: {str(e)}")
        return JsonResponse({'error': 'An error occurred'}, status=500)

# Restaurant Catalog Service views
@require_http_methods(["GET"])
def restaurant_search(request):
    """Search for restaurants with filtering"""
    try:
        # Extract parameters from request
        filters = {
            'cuisine_type': request.GET.get('cuisine', ''),
            'location': request.GET.get('location', ''),
            'price_range': request.GET.get('price', ''),
            'dietary_restrictions': request.GET.getlist('dietary[]', []),
            'rating_min': request.GET.get('rating_min', None),
            'atmosphere': request.GET.get('atmosphere', None),
            'order_by': request.GET.get('order_by', '-rating')
        }
        
        # Use service to perform search
        restaurants = RestaurantCatalogService.search_restaurants(filters)
        
        # Format response
        results = [{
            'id': restaurant.id,
            'name': restaurant.name,
            'cuisine_type': restaurant.cuisine_type,
            'price_range': restaurant.price_range,
            'rating': float(restaurant.rating),
            'address': restaurant.address,
            'dietary_options': restaurant.dietary_options
        } for restaurant in restaurants]
        
        return JsonResponse({'results': results})
    except Exception as e:
        logger.error(f"Error in restaurant_search: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def restaurant_detail(request, restaurant_id):
    """Get detailed information about a restaurant"""
    try:
        details = RestaurantCatalogService.get_restaurant_details(restaurant_id)
        
        if details:
            return JsonResponse(details)
        else:
            return JsonResponse({'error': 'Restaurant not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in restaurant_detail: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

# Location Service views
@require_http_methods(["GET"])
def nearby_restaurants(request):
    """Find restaurants near a location"""
    try:
        latitude = float(request.GET.get('lat', 0))
        longitude = float(request.GET.get('lng', 0))
        radius = float(request.GET.get('radius', 5.0))
        
        if not (latitude and longitude):
            return JsonResponse({'error': 'Latitude and longitude are required'}, status=400)
        
        restaurants = LocationService.find_nearby_restaurants(latitude, longitude, radius)
        
        results = [{
            'id': restaurant.id,
            'name': restaurant.name,
            'cuisine_type': restaurant.cuisine_type,
            'price_range': restaurant.price_range,
            'rating': float(restaurant.rating),
            'address': restaurant.address,
            'distance': round(getattr(restaurant, 'distance', 0), 2)  # Distance in km
        } for restaurant in restaurants]
        
        return JsonResponse({'results': results})
    except Exception as e:
        logger.error(f"Error in nearby_restaurants: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

# Reservation Service views
@require_http_methods(["GET"])
def check_availability(request):
    """Check restaurant availability"""
    try:
        restaurant_id = int(request.GET.get('restaurant_id', 0))
        date = request.GET.get('date', '')
        time = request.GET.get('time', '')
        party_size = int(request.GET.get('party_size', 0))
        
        if not all([restaurant_id, date, time, party_size]):
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
        
        availability = ReservationService.check_availability(
            restaurant_id, date, time, party_size
        )
        
        return JsonResponse(availability)
    except Exception as e:
        logger.error(f"Error in check_availability: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def create_reservation(request):
    """Create a new reservation"""
    try:
        data = json.loads(request.body)
        restaurant_id = data.get('restaurant_id')
        date = data.get('date')
        time = data.get('time')
        party_size = data.get('party_size')
        special_requests = data.get('special_requests', '')
        
        if not all([restaurant_id, date, time, party_size]):
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
        
        result = ReservationService.create_reservation(
            restaurant_id, request.user, date, time, party_size, special_requests
        )
        
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"Error in create_reservation: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

# Recommendation Service views
@require_http_methods(["GET"])
def get_recommendations(request):
    """Get personalized restaurant recommendations"""
    try:
        filters = {
            'occasion': request.GET.get('occasion', ''),
            'cuisine_preferences': request.GET.getlist('cuisine[]', []),
            'dietary_restrictions': request.GET.getlist('dietary[]', []),
            'price_range': request.GET.get('price', ''),
            'location': request.GET.get('location', '')
        }
        
        restaurants = RecommendationService.get_recommendations(filters, request.user)
        
        results = [{
            'id': restaurant.id,
            'name': restaurant.name,
            'cuisine_type': restaurant.cuisine_type,
            'price_range': restaurant.price_range,
            'rating': float(restaurant.rating),
            'address': restaurant.address,
            'atmosphere': restaurant.atmosphere,
            'dietary_options': restaurant.dietary_options
        } for restaurant in restaurants]
        
        return JsonResponse({'recommendations': results})
    except Exception as e:
        logger.error(f"Error in get_recommendations: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

# Review management
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def submit_review(request):
    """Submit a review for a restaurant"""
    try:
        data = json.loads(request.body)
        restaurant_id = data.get('restaurant_id')
        rating = data.get('rating')
        comment = data.get('comment', '')
        
        restaurant = get_object_or_404(Restaurant, id=restaurant_id)
        
        # Check if user already reviewed this restaurant
        existing_review = Review.objects.filter(restaurant=restaurant, user=request.user).first()
        
        if existing_review:
            # Update existing review
            existing_review.rating = rating
            existing_review.comment = comment
            existing_review.save()
            message = "Review updated successfully"
        else:
            # Create new review
            Review.objects.create(
                restaurant=restaurant,
                user=request.user,
                rating=rating,
                comment=comment
            )
            message = "Review submitted successfully"
        
        # Update restaurant's average rating
        avg_rating = Review.objects.filter(restaurant=restaurant).aggregate(
            models.Avg('rating'))['rating__avg']
        restaurant.rating = avg_rating
        restaurant.save()
        
        return JsonResponse({'success': True, 'message': message})
    except Exception as e:
        logger.error(f"Error in submit_review: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
