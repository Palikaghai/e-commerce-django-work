from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('signup/page/', views.signup_page, name='signup_page'),
    path('signup/ajax/', views.signup_ajax, name='signup_ajax'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]