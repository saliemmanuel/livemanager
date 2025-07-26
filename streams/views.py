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
from django.views.decorators.csrf import csrf_exempt


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
        form = LiveForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            try:
                live = form.save(commit=False)
                live.user = request.user

                # Vérifier la méthode d'upload
                upload_method = request.POST.get("upload_method")

                if upload_method == "scp":
                    # Fichier uploadé via SCP
                    video_file_name = request.POST.get("video_file_name")
                    if not video_file_name:
                        raise Exception("Nom de fichier manquant")

                    # Vérifier que le fichier existe
                    scp_file_path = os.path.join("media", "videos", video_file_name)
                    if not os.path.exists(scp_file_path):
                        raise Exception(
                            f"Fichier {video_file_name} non trouvé. "
                            "Vérifiez que l'upload SCP s'est bien terminé."
                        )

                    # Utiliser le fichier SCP
                    live.video_file = f"videos/{video_file_name}"
                    live.save()

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

                else:
                    # Upload normal via navigateur
                    if "video_file" in request.FILES:
                        video_file = request.FILES["video_file"]

                        # Créer un fichier temporaire pour la vidéo compressée
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".mp4"
                        ) as temp_file:
                            # Sauvegarder le fichier uploadé
                            for chunk in video_file.chunks():
                                temp_file.write(chunk)
                            temp_file_path = temp_file.name

                        try:
                            # Décompresser la vidéo avec FFmpeg
                            output_path = os.path.join(
                                "media", "videos", f"decompressed_{video_file.name}"
                            )
                            os.makedirs(os.path.dirname(output_path), exist_ok=True)

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

                            # Exécuter FFmpeg
                            result = subprocess.run(
                                ffmpeg_cmd,
                                capture_output=True,
                                text=True,
                                timeout=300,  # 5 minutes max
                            )

                            if result.returncode == 0:
                                # Sauvegarder le chemin de la vidéo décompressée
                                live.video_file = (
                                    f"videos/decompressed_{video_file.name}"
                                )
                                live.save()

                                # Réponse JSON pour les uploads AJAX
                                if (
                                    request.headers.get("X-Requested-With")
                                    == "XMLHttpRequest"
                                ):
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

                        finally:
                            # Nettoyer le fichier temporaire
                            if os.path.exists(temp_file_path):
                                os.unlink(temp_file_path)
                    else:
                        # Pas de fichier vidéo, sauvegarder normalement
                        live.save()

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


@csrf_exempt
@login_required
def upload_chunk(request):
    """Réception d'un chunk vidéo et assemblage côté serveur."""
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "message": "Méthode non autorisée"}, status=405
        )

    user = request.user
    chunk = request.FILES.get("chunk")
    chunk_number = int(request.POST.get("chunk_number", -1))
    total_chunks = int(request.POST.get("total_chunks", -1))
    file_id = request.POST.get("file_id")
    file_name = request.POST.get("file_name")

    if not all([chunk, chunk_number >= 0, total_chunks > 0, file_id, file_name]):
        return JsonResponse(
            {"success": False, "message": "Paramètres manquants"}, status=400
        )

    # Dossier temporaire par utilisateur et fichier
    temp_dir = os.path.join("media", "temp_chunks", str(user.id), file_id)
    os.makedirs(temp_dir, exist_ok=True)
    chunk_path = os.path.join(temp_dir, f"chunk_{chunk_number:05d}")

    # Sauvegarder le chunk
    with open(chunk_path, "wb") as f:
        for c in chunk.chunks():
            f.write(c)

    # Vérifier si tous les chunks sont présents
    received_chunks = [f for f in os.listdir(temp_dir) if f.startswith("chunk_")]
    if len(received_chunks) == total_chunks:
        # Assembler le fichier final
        final_path = os.path.join("media", "videos", f"{file_id}_{file_name}")
        os.makedirs(os.path.dirname(final_path), exist_ok=True)
        with open(final_path, "wb") as outfile:
            for i in range(total_chunks):
                part_path = os.path.join(temp_dir, f"chunk_{i:05d}")
                with open(part_path, "rb") as infile:
                    outfile.write(infile.read())
        # Nettoyer les chunks
        for f in received_chunks:
            os.remove(os.path.join(temp_dir, f))
        try:
            os.rmdir(temp_dir)
        except Exception:
            pass
        return JsonResponse(
            {"success": True, "message": "Fichier assemblé", "file_path": final_path}
        )
    else:
        return JsonResponse(
            {"success": True, "message": f"Chunk {chunk_number+1}/{total_chunks} reçu"}
        )


@csrf_exempt
@login_required
def upload_chunk_status(request):
    """Retourne la liste des chunks déjà reçus pour un fichier donné."""
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "message": "Méthode non autorisée"}, status=405
        )
    user = request.user
    file_id = request.POST.get("file_id")
    if not file_id:
        return JsonResponse(
            {"success": False, "message": "file_id manquant"}, status=400
        )
    temp_dir = os.path.join("media", "temp_chunks", str(user.id), file_id)
    if not os.path.exists(temp_dir):
        return JsonResponse({"success": True, "chunks": []})
    chunks = [
        int(f.split("_")[1]) for f in os.listdir(temp_dir) if f.startswith("chunk_")
    ]
    return JsonResponse({"success": True, "chunks": sorted(chunks)})


@csrf_exempt
@login_required
def upload_via_scp(request):
    """Génère les instructions SCP pour uploader un fichier vidéo."""
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "message": "Méthode non autorisée"}, status=405
        )

    file_name = request.POST.get("file_name")
    if not file_name:
        return JsonResponse(
            {"success": False, "message": "Nom de fichier manquant"}, status=400
        )

    # Obtenir l'IP du serveur
    server_ip = request.META.get("SERVER_NAME", "localhost")
    if server_ip == "localhost":
        # Si on est en local, utiliser l'IP du serveur
        import socket

        server_ip = socket.gethostbyname(socket.gethostname())

    # Générer la commande SCP
    scp_command = (
        f'scp "{file_name}" root@{server_ip}:/var/www/livemanager/media/videos/'
    )

    # Instructions détaillées
    instructions = f"""
📁 Instructions d'upload via SCP :

1. Ouvrez un terminal sur votre ordinateur
2. Naviguez vers le dossier contenant votre fichier
3. Exécutez cette commande :

{scp_command}

4. Entrez le mot de passe du serveur si demandé
5. Revenez sur cette page et cliquez sur "Vérifier le fichier"

💡 Avantages :
• Upload ultra-rapide (pas de limite HTTP)
• Reprise automatique en cas de coupure
• Plus stable pour les gros fichiers
"""

    return JsonResponse(
        {
            "success": True,
            "scp_command": scp_command,
            "instructions": instructions,
            "file_name": file_name,
        }
    )


@csrf_exempt
@login_required
def check_file_exists(request):
    """Vérifie si un fichier existe sur le serveur après upload SCP."""
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "message": "Méthode non autorisée"}, status=405
        )

    file_name = request.POST.get("file_name")
    if not file_name:
        return JsonResponse(
            {"success": False, "message": "Nom de fichier manquant"}, status=400
        )

    # Vérifier si le fichier existe
    file_path = os.path.join("media", "videos", file_name)
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        return JsonResponse(
            {
                "success": True,
                "exists": True,
                "file_size": file_size,
                "file_path": file_path,
            }
        )
    else:
        return JsonResponse(
            {
                "success": True,
                "exists": False,
                "message": (
                    "Fichier non trouvé. Vérifiez que l'upload SCP s'est bien terminé."
                ),
            }
        )
