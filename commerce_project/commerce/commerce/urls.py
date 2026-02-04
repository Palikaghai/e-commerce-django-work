"""
URL configuration for commerce project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import *
from django.conf.urls.static import static

# Import main views so we can expose some admin-like dashboards at project level
from main import views as main_views

urlpatterns = [
    # Project-level dashboard endpoints should be matched BEFORE the admin site so
    # requests to /admin/dashboard/* land on our custom dashboard instead of the
    # admin's catch-all view.
    path('admin/dashboard/', main_views.admin_dashboard, name='admin_dashboard'),
    path('admin/dashboard/data/', main_views.admin_sales_data, name='admin_sales_data'),
    path('admin/dashboard/export/', main_views.admin_export_sales_csv, name='admin_export_sales_csv'),

    path('admin/', admin.site.urls),
    path('auth/', include('user_auth.urls')), # User authentication URLs
    path('', include('main.urls')), # Home page and product pages
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
