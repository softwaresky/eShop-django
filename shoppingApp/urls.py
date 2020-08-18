from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', auth_views.LoginView.as_view(template_name='shoppingApp/login.html'), name='login'),
    path('logout', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('registration', views.registration, name='registration'),
    path('category/<int:category_id>', views.select_category, name='category'),
    path('product/<int:product_id>', views.select_product, name='product_details'),
    path('add-product-to-cart/<int:product_id>/<path:url_order_from>', views.order_product, name='add-product-to-cart'),
    path('cart-update-item', views.cart_update_item, name='cart-update-item'),
    path('cart-remove-item', views.cart_remove_item, name='cart-remove-item'),
    path('session-clear', views.session_clear, name='session-clear'),
    path('fill_data', views.fill_data, name="fill_data"),
    path('remove_data', views.remove_data, name="remove_data")
]
