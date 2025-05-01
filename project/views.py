from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, ListView, DetailView, View
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Product, Routine, Favorite, Review
from .forms import SignUpForm
from .models import Product, Review
from .forms import ReviewForm
from django.db.models import Avg, Count
from django.db import IntegrityError
from .forms import ProductForm, RoutineForm
from .forms import RoutineItemForm
from django.shortcuts import render, get_object_or_404, redirect
from django.forms import inlineformset_factory
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    CreateView, ListView, DetailView, View
)
from .models import Product, Routine, RoutineItem, Favorite
from .forms import (
    SignUpForm, ProductForm, RoutineForm,
    RoutineItemForm, ReviewForm
)
from django.shortcuts import render
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from .models import Product, Routine
import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Product
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date
from .models import Product, UsageLog
from django.db.models import Count
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import Follow, Product, Routine
from django.contrib.auth import get_user_model
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
User = get_user_model()


@login_required
def export_products_csv(request):
    # Grab only the current user's products
    prods = Product.objects.filter(owner=request.user)

    # Create the HttpResponse with CSV headers
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="my_products.csv"'

    writer = csv.writer(response)
    # Header row
    writer.writerow(['Name', 'Brand', 'Category', 'Shade', 'Price', 'Expires On'])

    # Data rows
    for p in prods:
        writer.writerow([
            p.name,
            p.brand,
            p.category.name if p.category else '',
            p.shade,
            f"{p.price:.2f}",
            p.expiration_date,
        ])

    return response
@login_required
def dashboard(request):
    owner = request.user
    # all products & routines for this user
    prods = Product.objects.filter(owner=owner)
    routines = Routine.objects.filter(owner=owner)
    # count how many expire within 7 days
    soon_count = prods.filter(
        expiration_date__lte=date.today() + timedelta(days=7)
    ).count()

    return render(request, 'project/dashboard.html', {
        'total_products': prods.count(),
        'expiring_soon': soon_count,
        'total_routines': routines.count(),
    })

def manage_routine_items(request, pk):
    # Only allow the owner to edit
    routine = get_object_or_404(Routine, pk=pk, owner=request.user)
    # Create the inline formset
    RoutineItemFormSet = inlineformset_factory(
        Routine, RoutineItem,
        form=RoutineItemForm,
        extra=1,
        can_delete=True
    )
    if request.method == 'POST':
        formset = RoutineItemFormSet(request.POST, instance=routine)
        if formset.is_valid():
            formset.save()
            return redirect('routine-detail', pk=routine.pk)
    else:
        formset = RoutineItemFormSet(instance=routine)
    return render(request, 'project/routine_steps_form.html', {
        'routine': routine,
        'formset': formset,
    })
@login_required
def mark_used(request, pk):
    product = get_object_or_404(Product, pk=pk, owner=request.user)
    UsageLog.objects.get_or_create(
        user=request.user,
        product=product,
        date=date.today()
    )
    messages.success(request, f"✔️ Marked “{product.name}” as used today.")
    return redirect('product-detail', pk=pk)
@login_required
def usage_stats(request):
    today = date.today()

    # 1) Annotate each product with total use count
    prods = (
        Product.objects
        .filter(owner=request.user)
        .annotate(used_count=Count('usage_logs'))
    )

    # 2) Top 3 most-used products
    top_products = prods.order_by('-used_count')[:3]

    # 3) Usage logs in the last 30 days
    logs_30 = UsageLog.objects.filter(
        user=request.user,
        date__gte=today - timedelta(days=29)
    )
    total_30 = logs_30.count()
    avg_per_day = total_30 / 30 if total_30 else 0

    # 4) Build daily counts for the last 7 days
    daily_counts = []
    for i in range(6, -1, -1):  # 6 days ago ... today
        d = today - timedelta(days=i)
        cnt = logs_30.filter(date=d).count()
        daily_counts.append((d, cnt))

    # 5) Compute current streak (consecutive days used in last 30)
    dates = set(logs_30.values_list('date', flat=True))
    streak = 0
    for i in range(30):
        if today - timedelta(days=i) in dates:
            streak += 1
        else:
            break

    # 6) Determine start and end dates for display
    if daily_counts:
        start_date = daily_counts[0][0]
        end_date   = daily_counts[-1][0]
    else:
        start_date = end_date = today

    return render(request, 'project/usage_stats.html', {
        'products':       prods,
        'top_products':   top_products,
        'avg_per_day':    avg_per_day,
        'daily_counts':   daily_counts,
        'current_streak': streak,
        'start_date':     start_date,
        'end_date':       end_date,
    })

@login_required
def follow_user(request, username):
    target = get_object_or_404(User, username=username)
    if target != request.user:
        Follow.objects.get_or_create(
            follower=request.user,
            followee=target
        )
    return redirect('user-profile', username=username)

@login_required
def unfollow_user(request, username):
    target = get_object_or_404(User, username=username)
    Follow.objects.filter(
        follower=request.user,
        followee=target
    ).delete()
    return redirect('user-profile', username=username)

@login_required
def user_profile(request, username):
    target = get_object_or_404(User, username=username)
    is_following = Follow.objects.filter(
        follower=request.user,
        followee=target
    ).exists()

    # Gather their favorited products and routines:
    fav_products = Product.objects.filter(favorited_by__user=target)
    routines     = Routine.objects.filter(owner=target)

    return render(request, 'project/user_profile.html', {
        'target':        target,
        'is_following':  is_following,
        'fav_products':  fav_products,
        'routines':      routines,
    })
@login_required
def user_list(request):
    # show everyone except yourself
    qs = User.objects.exclude(pk=request.user.pk)
    return render(request, 'project/user_list.html', {'users': qs})
@login_required
def feed(request):
    # get all the users you follow
    followees = Follow.objects.filter(follower=request.user).values_list('followee', flat=True)

    # their 5 most recent favorite-products
    recent_faves = (
        Favorite.objects
        .filter(user__in=followees)
        .select_related('product','user')
        .order_by('-created_at')[:10]
    )

    # their 5 newest routines
    recent_routines = (
        Routine.objects
        .filter(owner__in=followees)
        .order_by('-date')[:10]
    )

    return render(request, 'project/feed.html', {
        'recent_faves': recent_faves,
        'recent_routines': recent_routines,
    })

# Signup
class SignUpView(CreateView):
    form_class    = SignUpForm
    success_url   = reverse_lazy('login')
    template_name = 'registration/signup.html'

# Products
class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'project/product_list.html'

    def get_queryset(self):
        # only your products
        return Product.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        products = ctx['object_list']

        # resurrect your expiring_products list
        ctx['expiring_products'] = [p for p in products if p.is_expiring_soon]

        # **and** re-compute the favorite flag:
        for p in products:
            p.is_favorited = p.favorited_by.filter(user=self.request.user).exists()

        return ctx

class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'project/product_detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product = ctx['object']

        # favorite flag
        ctx['is_favorited'] = product.favorited_by.filter(user=self.request.user).exists()

        # pull in all reviews
        ctx['reviews'] = product.reviews.all()

        # compute average & count
        agg = product.reviews.aggregate(
            avg_rating=Avg('rating'),
            review_count=Count('pk')
        )
        ctx['avg_rating']   = agg['avg_rating'] or 0
        ctx['review_count'] = agg['review_count']

        return ctx

# Routines
class RoutineListView(LoginRequiredMixin, ListView):
    model = Routine
    template_name = 'project/routine_list.html'
    def get_queryset(self):
        return Routine.objects.filter(owner=self.request.user)

class RoutineDetailView(LoginRequiredMixin, DetailView):
    model = Routine
    template_name = 'project/routine_detail.html'

# Favorites toggle
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
        # capture the product
        self.product = get_object_or_404(Product, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.product = self.product
        try:
            return super().form_valid(form)
        except IntegrityError:
            # attach an error and re-show the form
            form.add_error(None, "You’ve already reviewed this product.")
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('product-detail', kwargs={'pk': self.product.pk})
    
class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'project/product_form.html'
    success_url = reverse_lazy('product-list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

class RoutineCreateView(LoginRequiredMixin, CreateView):
    model = Routine
    form_class = RoutineForm
    template_name = 'project/routine_form.html'
    success_url = reverse_lazy('routine-list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)
    

