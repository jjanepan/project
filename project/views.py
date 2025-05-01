"""
views.py

Defines all view logic for the app:
- Product management (listing, details, create, export, favorites)
- Routine management (listing, details, create, manage steps)
- Social features (follow/unfollow users, feed, user profiles)
- Usage tracking (mark used, stats)
- Authentication (signup)
"""

from datetime import date, timedelta
import csv

from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, ListView, DetailView, View
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db.models import Avg, Count
from django.db import IntegrityError
from django.forms import inlineformset_factory
from django.http import HttpResponse

from .models import (
    Product, Routine, RoutineItem, Favorite,
    Review, Follow, UsageLog
)
from .forms import (
    SignUpForm, ProductForm, RoutineForm,
    RoutineItemForm, ReviewForm
)

User = get_user_model()

# -------------------------- EXPORT --------------------------
@login_required
def export_products_csv(request):
    # Export current user's products to CSV
    prods = Product.objects.filter(owner=request.user)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="my_products.csv"'
    writer = csv.writer(response)
    writer.writerow(['Name', 'Brand', 'Category', 'Shade', 'Price', 'Expires On'])
    for p in prods:
        writer.writerow([
            p.name, p.brand, p.category.name if p.category else '',
            p.shade, f"{p.price:.2f}", p.expiration_date,
        ])
    return response

# -------------------------- DASHBOARD --------------------------
@login_required
def dashboard(request):
    owner = request.user
    prods = Product.objects.filter(owner=owner)
    routines = Routine.objects.filter(owner=owner)
    soon_count = prods.filter(expiration_date__lte=date.today() + timedelta(days=7)).count()
    return render(request, 'project/dashboard.html', {
        'total_products': prods.count(),
        'expiring_soon': soon_count,
        'total_routines': routines.count(),
    })

# -------------------------- ROUTINE MANAGEMENT --------------------------
def manage_routine_items(request, pk):
    routine = get_object_or_404(Routine, pk=pk, owner=request.user)
    RoutineItemFormSet = inlineformset_factory(Routine, RoutineItem, form=RoutineItemForm, extra=1, can_delete=True)
    if request.method == 'POST':
        formset = RoutineItemFormSet(request.POST, instance=routine)
        if formset.is_valid():
            formset.save()
            return redirect('routine-detail', pk=routine.pk)
    else:
        formset = RoutineItemFormSet(instance=routine)
    return render(request, 'project/routine_steps_form.html', {'routine': routine, 'formset': formset})

# -------------------------- USAGE TRACKING --------------------------
@login_required
def mark_used(request, pk):
    product = get_object_or_404(Product, pk=pk, owner=request.user)
    UsageLog.objects.get_or_create(user=request.user, product=product, date=date.today())
    messages.success(request, f"✔️ Marked “{product.name}” as used today.")
    return redirect('product-detail', pk=pk)

@login_required
def usage_stats(request):
    today = date.today()
    prods = Product.objects.filter(owner=request.user).annotate(used_count=Count('usage_logs'))
    top_products = prods.order_by('-used_count')[:3]
    logs_30 = UsageLog.objects.filter(user=request.user, date__gte=today - timedelta(days=29))
    total_30 = logs_30.count()
    avg_per_day = total_30 / 30 if total_30 else 0
    daily_counts = [(today - timedelta(days=i), logs_30.filter(date=today - timedelta(days=i)).count()) for i in range(6, -1, -1)]
    dates = set(logs_30.values_list('date', flat=True))
    streak = sum(1 for i in range(30) if (today - timedelta(days=i)) in dates)
    return render(request, 'project/usage_stats.html', {
        'products': prods, 'top_products': top_products, 'avg_per_day': avg_per_day,
        'daily_counts': daily_counts, 'current_streak': streak,
        'start_date': daily_counts[0][0] if daily_counts else today,
        'end_date': daily_counts[-1][0] if daily_counts else today,
    })

# -------------------------- SOCIAL FEATURES --------------------------
@login_required
def follow_user(request, username):
    target = get_object_or_404(User, username=username)
    if target != request.user:
        Follow.objects.get_or_create(follower=request.user, followee=target)
    return redirect('user-profile', username=username)

@login_required
def unfollow_user(request, username):
    target = get_object_or_404(User, username=username)
    Follow.objects.filter(follower=request.user, followee=target).delete()
    return redirect('user-profile', username=username)

@login_required
def user_profile(request, username):
    target = get_object_or_404(User, username=username)
    is_following = Follow.objects.filter(follower=request.user, followee=target).exists()
    fav_products = Product.objects.filter(favorited_by__user=target)
    routines = Routine.objects.filter(owner=target)
    return render(request, 'project/user_profile.html', {
        'target': target, 'is_following': is_following,
        'fav_products': fav_products, 'routines': routines,
    })

@login_required
def user_list(request):
    qs = User.objects.exclude(pk=request.user.pk)
    return render(request, 'project/user_list.html', {'users': qs})

@login_required
def feed(request):
    followees = Follow.objects.filter(follower=request.user).values_list('followee', flat=True)
    recent_faves = Favorite.objects.filter(user__in=followees).select_related('product', 'user').order_by('-created_at')[:10]
    recent_routines = Routine.objects.filter(owner__in=followees).order_by('-date')[:10]
    return render(request, 'project/feed.html', {'recent_faves': recent_faves, 'recent_routines': recent_routines})

# -------------------------- SIGNUP --------------------------
class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

# -------------------------- PRODUCT VIEWS --------------------------
class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'project/product_list.html'

    def get_queryset(self):
        return Product.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        products = ctx['object_list']
        ctx['expiring_products'] = [p for p in products if p.is_expiring_soon]
        for p in products:
            p.is_favorited = p.favorited_by.filter(user=self.request.user).exists()
        return ctx

class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'project/product_detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product = ctx['object']
        ctx['is_favorited'] = product.favorited_by.filter(user=self.request.user).exists()
        ctx['reviews'] = product.reviews.all()
        agg = product.reviews.aggregate(avg_rating=Avg('rating'), review_count=Count('pk'))
        ctx['avg_rating'] = agg['avg_rating'] or 0
        ctx['review_count'] = agg['review_count']
        return ctx

class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'project/product_form.html'
    success_url = reverse_lazy('product-list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

# -------------------------- ROUTINE VIEWS --------------------------
class RoutineListView(LoginRequiredMixin, ListView):
    model = Routine
    template_name = 'project/routine_list.html'

    def get_queryset(self):
        return Routine.objects.filter(owner=self.request.user)

class RoutineDetailView(LoginRequiredMixin, DetailView):
    model = Routine
    template_name = 'project/routine_detail.html'

class RoutineCreateView(LoginRequiredMixin, CreateView):
    model = Routine
    form_class = RoutineForm
    template_name = 'project/routine_form.html'
    success_url = reverse_lazy('routine-list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

# -------------------------- FAVORITES & REVIEWS --------------------------
class ToggleFavoriteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        fav, created = Favorite.objects.get_or_create(user=request.user, product=product)
        if not created:
            fav.delete()
        return redirect('product-detail', pk=pk)

class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'project/review_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.product = self.product
        try:
            return super().form_valid(form)
        except IntegrityError:
            form.add_error(None, "You’ve already reviewed this product.")
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('product-detail', kwargs={'pk': self.product.pk})
