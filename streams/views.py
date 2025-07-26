from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import User, Live
from .forms import UserRegistrationForm, LiveForm


def is_admin(user):
    """Vérifie si l'utilisateur est admin."""
    return user.is_authenticated and user.is_admin


def home(request):
    """Page d'accueil."""
    return render(request, "streams/home.html")


def register(request):
    """Inscription utilisateur."""
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Compte créé avec succès ! En attente d'approbation par "
                "l'administrateur.",
            )
            return redirect("login")
    else:
        form = UserRegistrationForm()

    return render(request, "streams/register.html", {"form": form})


@require_POST
def logout_view(request):
    """Vue de déconnexion personnalisée."""
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect("home")


@login_required
def dashboard(request):
    """Dashboard utilisateur."""
    user_lives = Live.objects.filter(user=request.user).order_by("-created_at")

    context = {
        "user_lives": user_lives,
        "is_approved": request.user.is_approved,
    }

    return render(request, "streams/dashboard.html", context)


@login_required
def create_live(request):
    """Création d'un nouveau live."""
    if not request.user.is_approved:
        messages.error(request, "Vous devez être approuvé pour créer un live.")
        return redirect("dashboard")

    if request.method == "POST":
        form = LiveForm(request.POST, request.FILES)
        if form.is_valid():
            live = form.save(commit=False)
            live.user = request.user
            live.save()

            messages.success(request, "Live créé avec succès !")
            return redirect("dashboard")
    else:
        form = LiveForm()

    return render(request, "streams/create_live.html", {"form": form})


@login_required
@require_POST
def start_live(request, live_id):
    """Démarrage manuel d'un live."""
    live = get_object_or_404(Live, id=live_id, user=request.user)

    if not live.can_start:
        return JsonResponse({"success": False, "message": "Live non démarré"})

    # Pour l'instant, on simule le démarrage
    live.status = "running"
    live.save()

    return JsonResponse({"success": True, "message": "Live démarré avec succès"})


@login_required
@require_POST
def stop_live(request, live_id):
    """Arrêt d'un live."""
    live = get_object_or_404(Live, id=live_id, user=request.user)

    if not live.is_running:
        return JsonResponse({"success": False, "message": "Live non en cours"})

    # Pour l'instant, on simule l'arrêt
    live.status = "completed"
    live.save()

    return JsonResponse({"success": True, "message": "Live arrêté avec succès"})


@user_passes_test(is_admin)
def admin_dashboard(request):
    """Dashboard administrateur."""
    users = User.objects.all().order_by("-date_joined")
    all_lives = Live.objects.all().order_by("-created_at")

    context = {
        "users": users,
        "all_lives": all_lives,
    }

    return render(request, "streams/admin_dashboard.html", context)


@user_passes_test(is_admin)
def admin_users(request):
    """Page de gestion des utilisateurs pour l'admin."""
    # Filtres
    search = request.GET.get("search", "")
    status_filter = request.GET.get("status", "")

    users = User.objects.all().order_by("-date_joined")

    # Filtre par recherche
    if search:
        users = users.filter(Q(username__icontains=search) | Q(email__icontains=search))

    # Filtre par statut
    if status_filter == "pending":
        users = users.filter(is_approved=False)
    elif status_filter == "approved":
        users = users.filter(is_approved=True)
    elif status_filter == "admin":
        users = users.filter(is_admin=True)

    # Statistiques
    total_users = User.objects.count()
    pending_users = User.objects.filter(is_approved=False).count()
    approved_users = User.objects.filter(is_approved=True).count()
    admin_users = User.objects.filter(is_admin=True).count()

    context = {
        "users": users,
        "search": search,
        "status_filter": status_filter,
        "stats": {
            "total": total_users,
            "pending": pending_users,
            "approved": approved_users,
            "admin": admin_users,
        },
    }

    return render(request, "streams/admin_users.html", context)


@user_passes_test(is_admin)
@require_POST
def approve_user(request, user_id):
    """Approbation d'un utilisateur."""
    user = get_object_or_404(User, id=user_id)
    user.is_approved = True
    user.save()

    messages.success(request, f"Utilisateur {user.email} approuvé avec succès.")
    return redirect("admin_users")


@user_passes_test(is_admin)
@require_POST
def reject_user(request, user_id):
    """Rejet d'un utilisateur."""
    user = get_object_or_404(User, id=user_id)
    user.is_approved = False
    user.save()

    messages.warning(request, f"Utilisateur {user.email} rejeté.")
    return redirect("admin_users")


@user_passes_test(is_admin)
@require_POST
def toggle_admin(request, user_id):
    """Activation/désactivation du statut admin."""
    user = get_object_or_404(User, id=user_id)
    user.is_admin = not user.is_admin
    user.save()

    status = "administrateur" if user.is_admin else "utilisateur"
    messages.success(request, f"{user.email} est maintenant {status}.")
    return redirect("admin_users")


@user_passes_test(is_admin)
@require_POST
def delete_user(request, user_id):
    """Suppression d'un utilisateur."""
    user = get_object_or_404(User, id=user_id)
    email = user.email
    user.delete()

    messages.success(request, f"Utilisateur {email} supprimé avec succès.")
    return redirect("admin_users")
