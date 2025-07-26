import os
import subprocess
import tempfile
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.db.models import Q
from .models import User, Live, StreamKey
from .forms import UserRegistrationForm, LiveForm, StreamKeyForm


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
def profile(request):
    """Page de profil utilisateur avec gestion des clés de streaming."""
    user_stream_keys = StreamKey.objects.filter(user=request.user).order_by(
        "-created_at"
    )

    context = {
        "user_stream_keys": user_stream_keys,
    }

    return render(request, "streams/profile.html", context)


@login_required
def add_stream_key(request):
    """Ajouter une nouvelle clé de streaming."""
    if request.method == "POST":
        form = StreamKeyForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Clé de streaming ajoutée avec succès !")
            return redirect("profile")
    else:
        form = StreamKeyForm(user=request.user)

    return render(request, "streams/add_stream_key.html", {"form": form})


@login_required
def edit_stream_key(request, key_id):
    """Modifier une clé de streaming existante."""
    stream_key = get_object_or_404(StreamKey, id=key_id, user=request.user)

    if request.method == "POST":
        form = StreamKeyForm(request.POST, instance=stream_key, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Clé de streaming modifiée avec succès !")
            return redirect("profile")
    else:
        form = StreamKeyForm(instance=stream_key, user=request.user)

    return render(
        request,
        "streams/edit_stream_key.html",
        {"form": form, "stream_key": stream_key},
    )


@login_required
@require_POST
def delete_stream_key(request, key_id):
    """Supprimer une clé de streaming."""
    stream_key = get_object_or_404(StreamKey, id=key_id, user=request.user)
    stream_key.delete()
    messages.success(request, "Clé de streaming supprimée avec succès !")
    return redirect("profile")


@login_required
@require_POST
def toggle_stream_key(request, key_id):
    """Activer/désactiver une clé de streaming."""
    stream_key = get_object_or_404(StreamKey, id=key_id, user=request.user)
    stream_key.is_active = not stream_key.is_active
    stream_key.save()

    status = "activée" if stream_key.is_active else "désactivée"
    messages.success(request, f"Clé de streaming {status} avec succès !")
    return redirect("profile")


@login_required
def create_live(request):
    """Création d'un nouveau live avec compression vidéo."""
    if not request.user.is_approved:
        messages.error(request, "Vous devez être approuvé pour créer un live.")
        return redirect("dashboard")

    if request.method == "POST":
        print(f"[DEBUG] Création de live - Utilisateur: {request.user.username}")
        print(f"[DEBUG] Fichiers reçus: {list(request.FILES.keys())}")

        form = LiveForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            print("[DEBUG] Formulaire valide")
            try:
                live = form.save(commit=False)
                live.user = request.user

                # Upload normal via navigateur
                if "video_file" in request.FILES:
                    video_file = request.FILES["video_file"]
                    print(
                        f"[DEBUG] Fichier vidéo reçu: {video_file.name}, "
                        f"taille: {video_file.size}"
                    )

                    # Créer un fichier temporaire pour la vidéo compressée
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".mp4"
                    ) as temp_file:
                        # Sauvegarder le fichier uploadé
                        for chunk in video_file.chunks():
                            temp_file.write(chunk)
                        temp_file_path = temp_file.name
                        print(f"[DEBUG] Fichier temporaire créé: {temp_file_path}")

                    try:
                        # Décompresser la vidéo avec FFmpeg
                        output_path = os.path.join(
                            "media", "videos", f"decompressed_{video_file.name}"
                        )
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        print(f"[DEBUG] Chemin de sortie: {output_path}")

                        # Commande FFmpeg pour décompresser et optimiser
                        ffmpeg_cmd = [
                            "ffmpeg",
                            "-i",
                            temp_file_path,
                            "-c:v",
                            "libx264",  # Codec vidéo H.264
                            "-c:a",
                            "aac",  # Codec audio AAC
                            "-preset",
                            "medium",  # Équilibre qualité/performance
                            "-crf",
                            "23",  # Qualité constante (18-28 recommandé)
                            "-movflags",
                            "+faststart",  # Optimisation web
                            "-y",  # Écraser si existe
                            output_path,
                        ]
                        print(f"[DEBUG] Commande FFmpeg: {' '.join(ffmpeg_cmd)}")

                        # Exécuter FFmpeg
                        result = subprocess.run(
                            ffmpeg_cmd,
                            capture_output=True,
                            text=True,
                            timeout=300,  # 5 minutes max
                        )
                        print(f"[DEBUG] FFmpeg returncode: {result.returncode}")
                        if result.returncode != 0:
                            print(f"[DEBUG] FFmpeg stderr: {result.stderr}")

                        if result.returncode == 0:
                            # Sauvegarder le chemin de la vidéo décompressée
                            live.video_file = f"videos/decompressed_{video_file.name}"
                            live.save()
                            print(f"[DEBUG] Live sauvegardé avec succès: {live.id}")

                            # Nettoyer le fichier temporaire
                            os.unlink(temp_file_path)
                            print("[DEBUG] Fichier temporaire supprimé")

                            if (
                                request.headers.get("X-Requested-With")
                                == "XMLHttpRequest"
                            ):
                                print("[DEBUG] Réponse AJAX de succès")
                                return JsonResponse(
                                    {
                                        "success": True,
                                        "message": (
                                            "Vidéo compressée et live créé "
                                            "avec succès !"
                                        ),
                                        "redirect_url": reverse("dashboard"),
                                    }
                                )

                            messages.success(
                                request,
                                "Vidéo compressée et live créé avec succès !",
                            )
                            return redirect("dashboard")
                        else:
                            raise Exception(f"Erreur FFmpeg: {result.stderr}")

                    except Exception as e:
                        print(f"[DEBUG] Exception lors du traitement vidéo: {str(e)}")
                        # Nettoyer le fichier temporaire en cas d'erreur
                        if os.path.exists(temp_file_path):
                            os.unlink(temp_file_path)
                        raise e

                else:
                    # Pas de fichier vidéo, sauvegarder normalement
                    live.save()
                    print(f"[DEBUG] Live sauvegardé sans vidéo: {live.id}")

                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse(
                            {
                                "success": True,
                                "message": "Live créé avec succès !",
                                "redirect_url": reverse("dashboard"),
                            }
                        )

                    messages.success(request, "Live créé avec succès !")
                    return redirect("dashboard")

            except Exception as e:
                print(f"[DEBUG] Exception générale: {str(e)}")
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse(
                        {
                            "success": False,
                            "message": f"Erreur lors de la création: {str(e)}",
                        },
                        status=400,
                    )
                else:
                    messages.error(request, f"Erreur lors de la création: {str(e)}")
        else:
            print(f"[DEBUG] Formulaire invalide: {form.errors}")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Données invalides",
                        "errors": form.errors,
                    },
                    status=400,
                )
    else:
        form = LiveForm(user=request.user)

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
        "total_users": total_users,
        "pending_users": pending_users,
        "approved_users": approved_users,
        "admin_users": admin_users,
        "search": search,
        "status_filter": status_filter,
    }

    return render(request, "streams/admin_users.html", context)


@user_passes_test(is_admin)
@require_POST
def approve_user(request, user_id):
    """Approuver un utilisateur."""
    user = get_object_or_404(User, id=user_id)
    user.is_approved = True
    user.save()
    messages.success(request, f"Utilisateur {user.username} approuvé avec succès.")
    return redirect("admin_users")


@user_passes_test(is_admin)
@require_POST
def reject_user(request, user_id):
    """Rejeter un utilisateur."""
    user = get_object_or_404(User, id=user_id)
    user.is_approved = False
    user.save()
    messages.success(request, f"Utilisateur {user.username} rejeté.")
    return redirect("admin_users")


@user_passes_test(is_admin)
@require_POST
def toggle_admin(request, user_id):
    """Basculer le statut admin d'un utilisateur."""
    user = get_object_or_404(User, id=user_id)
    user.is_admin = not user.is_admin
    user.save()
    status = "admin" if user.is_admin else "utilisateur"
    messages.success(request, f"{user.username} est maintenant {status}.")
    return redirect("admin_users")


@user_passes_test(is_admin)
@require_POST
def delete_user(request, user_id):
    """Supprimer un utilisateur."""
    user = get_object_or_404(User, id=user_id)
    username = user.username
    user.delete()
    messages.success(request, f"Utilisateur {username} supprimé avec succès.")
    return redirect("admin_users")
