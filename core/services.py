from django.db.models import Q, F
from django.conf import settings
import logging
from datetime import datetime, timedelta
from .models import Restaurant, Reservation

logger = logging.getLogger(__name__)

class RestaurantCatalogService:
    """Service for searching and retrieving restaurant information"""
    
    @staticmethod
    def search_restaurants(filters):
        """
        Search for restaurants based on provided filters
        """
        try:
            # Start with all restaurants
            query = Restaurant.objects.all()
            
            # Apply filters if they exist
            if filters.get('cuisine_type'):
                query = query.filter(cuisine_type__icontains=filters['cuisine_type'])
                
            if filters.get('location'):
                query = query.filter(address__icontains=filters['location'])
                
            if filters.get('price_range'):
                query = query.filter(price_range=filters['price_range'])
                
            if filters.get('dietary_restrictions'):
                # Filter for all dietary restrictions (AND logic)
                for restriction in filters['dietary_restrictions']:
                    query = query.filter(dietary_options__icontains=restriction)
                    
            if filters.get('rating_min'):
                query = query.filter(rating__gte=filters['rating_min'])
                
            if filters.get('atmosphere'):
                query = query.filter(atmosphere__icontains=filters['atmosphere'])
                
            # Order results
            order_by = filters.get('order_by', '-rating')
            query = query.order_by(order_by)
            
            return query
        except Exception as e:
            logger.error(f"Error in search_restaurants: {str(e)}")
            return Restaurant.objects.none()
    
    @staticmethod
    def get_restaurant_details(restaurant_id):
        """
        Get detailed information about a restaurant
        """
        try:
            restaurant = Restaurant.objects.get(id=restaurant_id)
            return {
                'id': restaurant.id,
                'name': restaurant.name,
                'cuisine_type': restaurant.cuisine_type,
                'description': restaurant.description,
                'price_range': restaurant.price_range,
                'rating': float(restaurant.rating),
                'address': restaurant.address,
                'phone': restaurant.phone,
                'website': restaurant.website,
                'hours_of_operation': restaurant.hours_of_operation,
                'dietary_options': restaurant.dietary_options,
                'atmosphere': restaurant.atmosphere,
                'image_url': restaurant.image_url
            }
        except Restaurant.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error in get_restaurant_details: {str(e)}")
            return None


class LocationService:
    """Service for location-based restaurant operations"""
    
    @staticmethod
    def find_nearby_restaurants(latitude, longitude, radius=5.0):
        """
        Find restaurants near a specific location
        Note: This is a simplified implementation that doesn't use actual geo-calculations
        In a real app, you would use PostGIS or similar for proper geo-queries
        """
        try:
            # For simplicity, we're just returning all restaurants
            # In a real application, you would filter by actual distance
            restaurants = Restaurant.objects.all()[:20]  # Limit to 20 for demo
            
            # In a real app, you'd calculate actual distance and add it to each restaurant
            # For now, we'll just simulate a random distance for each
            import random
            for restaurant in restaurants:
                setattr(restaurant, 'distance', round(random.uniform(0.5, radius), 1))
                
            # Sort by our simulated distance
            restaurants = sorted(restaurants, key=lambda r: getattr(r, 'distance'))
            
            return restaurants
        except Exception as e:
            logger.error(f"Error in find_nearby_restaurants: {str(e)}")
            return []


class ReservationService:
    """Service for handling restaurant reservations"""
    
    @staticmethod
    def check_availability(restaurant_id, date, time, party_size):
        """
        Check if a restaurant has availability for a given time and party size
        """
        try:
            # Parse date and time
            try:
                # Format: YYYY-MM-DD
                reservation_date = datetime.strptime(date, '%Y-%m-%d').date()
                # Format: HH:MM
                reservation_time = datetime.strptime(time, '%H:%M').time()
                reservation_datetime = datetime.combine(reservation_date, reservation_time)
            except ValueError:
                return {'available': False, 'error': 'Invalid date or time format'}
                
            # Check if restaurant exists
            try:
                restaurant = Restaurant.objects.get(id=restaurant_id)
            except Restaurant.DoesNotExist:
                return {'available': False, 'error': 'Restaurant not found'}
                
            # Check if restaurant is open at that time
            # In a real app, you would check the restaurant's hours of operation
                
            # Check existing reservations
            # This is a simplified check - in reality, you'd need to consider tables, capacity, etc.
            existing_reservations = Reservation.objects.filter(
                restaurant_id=restaurant_id,
                reservation_time__date=reservation_date,
                reservation_time__hour=reservation_time.hour,
                reservation_time__minute=reservation_time.minute
            ).count()
            
            # Assume a restaurant can handle 5 reservations per time slot for this demo
            if existing_reservations >= 5:
                # Suggest alternative times
                alternative_times = [
                    (reservation_datetime - timedelta(hours=1)).strftime('%H:%M'),
                    (reservation_datetime + timedelta(hours=1)).strftime('%H:%M'),
                    (reservation_datetime - timedelta(hours=2)).strftime('%H:%M'),
                    (reservation_datetime + timedelta(hours=2)).strftime('%H:%M'),
                ]
                
                return {
                    'available': False, 
                    'message': 'No availability at the requested time',
                    'alternative_times': alternative_times
                }
                
            return {'available': True}
            
        except Exception as e:
            logger.error(f"Error in check_availability: {str(e)}")
            return {'available': False, 'error': 'An error occurred while checking availability'}
    
    @staticmethod
    def create_reservation(restaurant_id, user, date, time, party_size, special_requests=''):
        """
        Create a new reservation
        """
        try:
            # First check availability
            availability = ReservationService.check_availability(restaurant_id, date, time, party_size)
            
            if not availability.get('available'):
                return availability
                
            # Parse date and time
            reservation_date = datetime.strptime(date, '%Y-%m-%d').date()
            reservation_time = datetime.strptime(time, '%H:%M').time()
            reservation_datetime = datetime.combine(reservation_date, reservation_time)
            
            # Create the reservation
            reservation = Reservation.objects.create(
                restaurant_id=restaurant_id,
                user=user,
                party_size=party_size,
                reservation_time=reservation_datetime,
                special_requests=special_requests
            )
            
            return {
                'success': True,
                'reservation_id': reservation.id,
                'message': f'Reservation successfully created for {date} at {time}'
            }
            
        except Exception as e:
            logger.error(f"Error in create_reservation: {str(e)}")
            return {'success': False, 'error': 'An error occurred while creating the reservation'}


class RecommendationService:
    """Service for personalized restaurant recommendations"""
    
    @staticmethod
    def get_recommendations(filters, user=None):
        """
        Get personalized restaurant recommendations based on filters and user history
        """
        try:
            # Start with standard search based on filters
            base_results = RestaurantCatalogService.search_restaurants(filters)
            
            # If user is authenticated, we could personalize results
            if user and user.is_authenticated:
                # Get user's past reservations
                past_restaurants = Reservation.objects.filter(
                    user=user
                ).values_list('restaurant_id', flat=True).distinct()
                
                # In a real recommendation system, you'd use more sophisticated algorithms
                # For now, we'll just boost restaurants of cuisines they've tried before
                
                # Get cuisines from past reservations
                if past_restaurants:
                    cuisine_preferences = Restaurant.objects.filter(
                        id__in=past_restaurants
                    ).values_list('cuisine_type', flat=True)
                    
                    # Boost restaurants with these cuisines (simple approach)
                    if cuisine_preferences:
                        cuisine_filter = Q()
                        for cuisine in cuisine_preferences:
                            cuisine_filter |= Q(cuisine_type__icontains=cuisine)
                            
                        # Combine with base results
                        recommended = Restaurant.objects.filter(cuisine_filter)
                        # Remove duplicates and combine
                        recommended_ids = set(recommended.values_list('id', flat=True))
                        base_ids = set(base_results.values_list('id', flat=True))
                        
                        # Prioritize recommendations, then add remaining base results
                        final_ids = list(recommended_ids) + list(base_ids - recommended_ids)
                        
                        # Preserve ordering with Case When
                        from django.db.models import Case, When
                        preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(final_ids)])
                        
                        return Restaurant.objects.filter(id__in=final_ids).order_by(preserved_order)
            
            return base_results
            
        except Exception as e:
            logger.error(f"Error in get_recommendations: {str(e)}")
            return Restaurant.objects.none()
