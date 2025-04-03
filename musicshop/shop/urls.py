from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import (BaseView, ArtistDetailView,
                    AlbumDetailView, RegistrationView,
                    LoginView, AccountView,
                    CartView, AddToCartView,
                    DeleteFromCartView, ChangeQTYView)

urlpatterns = [
# end-point для корзины
    path('cart/', CartView.as_view(), name='cart'),
    path('add-to-cart/<str:ct_model>/<str:slug>/', AddToCartView.as_view(), name='add-to-cart'),
    path('remove-to-cart/<str:ct_model>/<str:slug>/', DeleteFromCartView.as_view(), name='delete-to-cart'),
    path('change_qty/<str:ct_model>/<str:slug>/', ChangeQTYView.as_view(), name='change_qty'),
    path('', BaseView.as_view(), name='base'),
    path('login/',LoginView.as_view(), name='login'),
    path('logout/',LogoutView.as_view(next_page='/'), name='logout'),
    path('registration/',RegistrationView.as_view(), name='registration'),
    path('account/',AccountView.as_view(), name='account'),
    path('<str:artist_slug>/', ArtistDetailView.as_view(), name='artist_detail'),
    path('<str:artist_slug>/<str:album_slug>/', AlbumDetailView.as_view(), name='album_detail'),
]
