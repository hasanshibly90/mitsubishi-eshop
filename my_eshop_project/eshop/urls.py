# eshop/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('product/<str:sku>/', views.product_detail_view, name='product_detail'),
    path('fx-series/', views.fx_series_view, name='fx_series'),
    path('vfd/', views.vfd_view, name='vfd'),
    
    # Single route for category filter:
    path('category/<str:cat_name>/', views.category_filter_view, name='category_filter'),
    
    path('brand/<int:brand_id>/', views.brand_detail_view, name='brand_detail'),
    path('search/', views.search_view, name='search'),
    path('ask-discount/<str:sku>/', views.ask_for_discount_view, name='ask_for_discount'),
    path('quotation/<int:pk>/', views.quotation_detail_view, name='quotation_detail'),
    path('order-management/', views.order_management_view, name='order_management'),
    
    # NEW: Edit Order route for staff to update/confirm orders
    path('order/edit/<int:pk>/', views.edit_order_view, name='edit_order'),
    
    # Use only the version with a quotation_id parameter
    path('discount-submitted/<int:quotation_id>/', views.discount_submitted_view, name='discount_submitted'),
    
    path('filter/', views.product_filter_search_view, name='product_filter_search'),
    path('product-suggestions/', views.product_search_suggestions, name='product_search_suggestions'),
    
    # NEW: Series filter route
    path('series/<str:series_name>/', views.series_filter_view, name='series_filter'),
    
    # NEW: Parent detail route (for e.g. "D SERIES", "E SERIES", etc.)
    path('parent/<slug:parent_slug>/', views.parent_detail_view, name='parent_detail'),
    
    # NEW: API-like endpoints for dependent dropdowns
    path('top-level-categories/', views.top_level_categories_view, name='top_level_categories'),
    path('category-children/<int:parent_id>/', views.category_children_view, name='category_children'),
    
    path('all-vfd-inverters/', views.all_vfd_inverters_view, name='all_vfd_inverters'),
]
