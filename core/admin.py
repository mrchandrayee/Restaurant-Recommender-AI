from django.contrib import admin
from .models import Restaurant, Review, Reservation

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'cuisine_type', 'price_range', 'rating', 'atmosphere')
    list_filter = ('cuisine_type', 'price_range', 'atmosphere')
    search_fields = ('name', 'cuisine_type', 'address')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('restaurant__name', 'user__username', 'comment')
    readonly_fields = ('created_at',)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'user', 'party_size', 'reservation_time', 'status')
    list_filter = ('status', 'reservation_time')
    search_fields = ('restaurant__name', 'user__username', 'special_requests')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['confirm_reservations', 'cancel_reservations']
    date_hierarchy = 'reservation_time'

    def confirm_reservations(self, request, queryset):
        queryset.update(status='confirmed')
    confirm_reservations.short_description = "Mark selected reservations as confirmed"

    def cancel_reservations(self, request, queryset):
        queryset.update(status='cancelled')
    cancel_reservations.short_description = "Mark selected reservations as cancelled"
