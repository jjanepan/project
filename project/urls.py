from django.urls import path
from django.views.generic import RedirectView

from .views import (
    dashboard,
    SignUpView,
    ProductListView, ProductDetailView, ProductCreateView,
    RoutineListView, RoutineDetailView, RoutineCreateView,
    ToggleFavoriteView, ReviewCreateView,
    export_products_csv,
    mark_used,
    usage_stats,
    manage_routine_items,
    follow_user, unfollow_user, user_profile, user_list,
    feed,
)

urlpatterns = [
    # 1) Redirect /project/ → product list
    path('', RedirectView.as_view(pattern_name='product-list', permanent=False)),
    
    # 2) Authentication
    path('signup/', SignUpView.as_view(), name='signup'),
    
    # 3) Products
    path('products/',                       ProductListView.as_view(),   name='product-list'),
    path('products/add/',                   ProductCreateView.as_view(), name='product-add'),
    path('products/export_csv/',            export_products_csv,         name='export-products-csv'),
    path('products/<int:pk>/',              ProductDetailView.as_view(), name='product-detail'),
    path('products/<int:pk>/favorite/',     ToggleFavoriteView.as_view(),name='toggle-favorite'),
    path('products/<int:pk>/use/',          mark_used,                   name='product-use'),
    path('products/<int:pk>/review/',       ReviewCreateView.as_view(),  name='add-review'),
    
    # 4) Routines
    path('routines/',                       RoutineListView.as_view(),   name='routine-list'),
    path('routines/add/',                   RoutineCreateView.as_view(), name='routine-add'),
    path('routines/<int:pk>/',              RoutineDetailView.as_view(), name='routine-detail'),
    path('routines/<int:pk>/steps/',        manage_routine_items,        name='routine-manage-steps'),

    # 5) Usage statistics
    path('stats/usage/',                    usage_stats,                 name='usage-stats'),

    # 6) Social: user directory & profiles
    path('users/',                          user_list,                   name='user-list'),
    path('users/<str:username>/',           user_profile,                name='user-profile'),
    path('users/<str:username>/follow/',    follow_user,                 name='follow-user'),
    path('users/<str:username>/unfollow/',  unfollow_user,               name='unfollow-user'),

    # 7) Social feed
    path('feed/',                           feed,                        name='feed'),
]
