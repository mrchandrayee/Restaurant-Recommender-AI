from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from core import views as core_views  # Import core views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    
    # Authentication URLs
    path('login/', core_views.login_view, name='login'),
    path('register/', core_views.register, name='register'),
    path('logout/', auth_views.LogoutView.as_view(next_page='core:home'), name='logout'),
]
