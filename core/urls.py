from django.urls import path, include
from . import views

app_name = 'core'

urlpatterns = [
    
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('restaurant/<int:restaurant_id>/', views.restaurant_detail, name='restaurant_detail'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
    path('search/', views.search_restaurants, name='search_restaurants'),
    path('reservation/<int:reservation_id>/cancel/', views.cancel_reservation, name='cancel_reservation'),

    # Chat interface
    path('chat/', views.chat_interface, name='chat_interface'),
    path('api/chat/', views.chat_api, name='chat_api'),
    path('chat/endpoint/', views.chat_endpoint, name='chat_endpoint'),
    
    # Restaurant Catalog Service
    path('api/restaurants/search/', views.restaurant_search, name='restaurant_search'),
    path('api/restaurants/<int:restaurant_id>/', views.restaurant_detail, name='api_restaurant_detail'),
    
    # Location Service
    path('api/restaurants/nearby/', views.nearby_restaurants, name='nearby_restaurants'),
    
    # Reservation Service
    path('api/reservations/check-availability/', views.check_availability, name='check_availability'),
    path('api/reservations/create/', views.create_reservation, name='create_reservation'),
    
    # Recommendation Service
    path('api/recommendations/', views.get_recommendations, name='get_recommendations'),
    
    # Reviews
    path('api/reviews/submit/', views.submit_review, name='submit_review'),
]
