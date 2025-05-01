from django.contrib import admin
from .models import Category, Product, Routine, RoutineItem, Favorite, Review, UsageLog, Follow

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name','brand','owner','category','shade','price')
    list_filter  = ('category','brand','owner')
    search_fields= ('name','brand','shade')

@admin.register(Routine)
class RoutineAdmin(admin.ModelAdmin):
    list_display = ('name','owner','date')
    list_filter  = ('owner',)
    search_fields= ('name',)

@admin.register(RoutineItem)
class RoutineItemAdmin(admin.ModelAdmin):
    list_display = ('routine','product','step_order')
    list_filter  = ('routine',)

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user','product','created_at')
    list_filter  = ('user','product')
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display  = ('product', 'user', 'rating', 'created_at')
    list_filter   = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'text')

@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'date')
    list_filter  = ('date', 'product')

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display  = ('follower', 'followee', 'created_at')
    search_fields = ('follower__username', 'followee__username')