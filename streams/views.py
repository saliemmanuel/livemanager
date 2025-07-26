import os
import sys
import tempfile
import subprocess
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from .forms import UserRegistrationForm, LiveForm, StreamKeyForm
from .models import User, Live, StreamKey


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
            user = form.save(commit=False)
            user.is_approved = False  # Nécessite approbation admin
            user.save()
            messages.success(
                request,
                "Inscription réussie ! Votre compte sera activé par un administrateur.",
            )
            return redirect("login")
    else:
        form = UserRegistrationForm()
    return render(request, "streams/register.html", {"form": form})


@require_POST
def logout_view(request):
    """Déconnexion utilisateur."""
    from django.contrib.auth import logout

    logout(request)
    messages.success(request, "Vous avez été déconnecté.")
    return redirect("home")


@login_required
def dashboard(request):
    """Dashboard utilisateur."""
    lives = Live.objects.filter(user=request.user).order_by("-created_at")

    context = {
        "lives": lives,
        "is_approved": request.user.is_approved,
        "user_lives": lives,  # Pour compatibilité avec le template
    }

    if not request.user.is_approved:
        messages.warning(
            request,
            "Votre compte n'est pas encore approuvé. "
            "Un administrateur vous activera bientôt.",
        )

    return render(request, "streams/dashboard.html", context)


@login_required
def profile(request):
    """Profil utilisateur avec gestion des clés de streaming."""
    stream_keys = StreamKey.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "streams/profile.html", {"stream_keys": stream_keys})


@login_required
def add_stream_key(request):
    """Ajouter une clé de streaming."""
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
    """Modifier une clé de streaming."""
    stream_key = get_object_or_404(StreamKey, id=key_id, user=request.user)
    if request.method == "POST":
        form = StreamKeyForm(request.POST, instance=stream_key, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Clé de streaming modifiée avec succès !")
            return redirect("profile")
    else:
        form = StreamKeyForm(instance=stream_key, user=request.user)
    return render(request, "streams/edit_stream_key.html", {"form": form})


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

                    # Option temporaire : désactiver la compression si FFmpeg n'est pas
                    # disponible
                    skip_compression = False
                    try:
                        # Tester si FFmpeg est disponible
                        subprocess.run(
                            ["ffmpeg", "-version"], capture_output=True, timeout=5
                        )
                    except (FileNotFoundError, subprocess.TimeoutExpired):
                        print(
                            "[DEBUG] FFmpeg non disponible, upload direct sans "
                            "compression"
                        )
                        skip_compression = True

                    if skip_compression:
                        # Upload direct sans compression
                        output_path = os.path.join("media", "videos", video_file.name)
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)

                        with open(output_path, "wb") as f:
                            for chunk in video_file.chunks():
                                f.write(chunk)

                        live.video_file = f"videos/{video_file.name}"
                        live.save()
                        print(f"[DEBUG] Live sauvegardé sans compression: {live.id}")

                        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                            return JsonResponse(
                                {
                                    "success": True,
                                    "message": ("Video uploadée ! (sans compression)"),
                                    "redirect_url": reverse("dashboard"),
                                }
                            )

                        messages.success(
                            request, "Vidéo uploadée avec succès ! (sans compression)"
                        )
                        return redirect("dashboard")

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
                        print(f"[DEBUG] Erreur lors de la compression: {str(e)}")
                        # Nettoyer le fichier temporaire en cas d'erreur
                        if os.path.exists(temp_file_path):
                            os.unlink(temp_file_path)

                        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                            return JsonResponse(
                                {
                                    "success": False,
                                    "message": f"Erreur compression: {str(e)}",
                                }
                            )

                        messages.error(
                            request, f"Erreur lors de la compression: {str(e)}"
                        )
                        return redirect("dashboard")

                else:
                    # Pas de fichier vidéo
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse(
                            {"success": False, "message": "Aucun fichier vidéo fourni"}
                        )

                    messages.error(request, "Aucun fichier vidéo fourni")
                    return redirect("dashboard")

            except Exception as e:
                print(f"[DEBUG] Erreur générale: {str(e)}")
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse(
                        {"success": False, "message": f"Erreur: {str(e)}"}
                    )

                messages.error(request, f"Erreur: {str(e)}")
                return redirect("dashboard")
        else:
            print(f"[DEBUG] Formulaire invalide: {form.errors}")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": False,
                        "message": f"Erreur de validation: {form.errors}",
                    }
                )

            messages.error(request, f"Erreur de validation: {form.errors}")
            return redirect("dashboard")

    else:
        form = LiveForm(user=request.user)
        return render(request, "streams/create_live.html", {"form": form})


@login_required
@require_POST
def start_live(request, live_id):
    """Démarrage manuel d'un live."""
    live = get_object_or_404(Live, id=live_id, user=request.user)

    print(f"[DEBUG] Tentative de démarrage du live {live.id}")
    print(f"[DEBUG] Statut du live: {live.status}")
    print(f"[DEBUG] Utilisateur approuvé: {live.user.is_approved}")
    print(f"[DEBUG] can_start: {live.can_start}")

    if not live.can_start:
        print("[DEBUG] Live ne peut pas être démarré")
        return JsonResponse({"success": False, "message": "Live non démarré"})

    if not live.stream_key:
        print("[DEBUG] Clé de streaming manquante")
        return JsonResponse({"success": False, "message": "Clé de streaming manquante"})

    try:
        # Construire la commande FFmpeg
        video_path = os.path.join("media", live.video_file.name)
        if not os.path.exists(video_path):
            print(f"[DEBUG] Fichier vidéo non trouvé: {video_path}")
            return JsonResponse(
                {"success": False, "message": "Fichier vidéo non trouvé"}
            )

        # Construire l'URL RTMP avec la clé de streaming
        rtmp_url = live.stream_key.key

        # Commande FFmpeg pour le streaming (sans setsid pour compatibilité Windows)
        ffmpeg_cmd = [
            "ffmpeg",
            "-re",  # Lire à la vitesse réelle
            "-stream_loop",
            "-1",  # Boucle infinie
            "-i",
            video_path,  # Fichier d'entrée
            "-c:v",
            "libx264",  # Codec vidéo H.264
            "-preset",
            "ultrafast",  # Preset rapide pour streaming
            "-b:v",
            "500k",  # Bitrate vidéo 500k
            "-maxrate",
            "800k",  # Bitrate maximum 800k
            "-bufsize",
            "1200k",  # Taille du buffer 1200k
            "-s",
            "640x360",  # Résolution 640x360
            "-g",
            "60",  # GOP size 60
            "-keyint_min",
            "60",  # Keyframe minimum 60
            "-c:a",
            "aac",  # Codec audio AAC
            "-b:a",
            "96k",  # Bitrate audio 96k
            "-f",
            "flv",  # Format de sortie FLV
            "-reconnect",
            "1",  # Activer la reconnexion
            "-reconnect_streamed",
            "1",  # Reconnexion pour streaming
            "-reconnect_delay_max",
            "2",  # Délai max de reconnexion 2s
            rtmp_url,  # URL de destination RTMP
        ]

        print(f"[DEBUG] Démarrage live {live.id}")
        print(f"[DEBUG] Commande FFmpeg: {' '.join(ffmpeg_cmd)}")

        # Lancer FFmpeg en arrière-plan (compatible Windows et Linux)
        if sys.platform.startswith("win"):
            # Windows: utiliser subprocess.Popen avec creationflags
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
        else:
            # Linux/Unix: utiliser subprocess.Popen normal
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,  # Créer une nouvelle session
            )

        # Sauvegarder le PID et mettre à jour le statut
        live.ffmpeg_pid = process.pid
        live.status = "running"
        live.save()

        print(f"[DEBUG] Live {live.id} démarré avec PID {process.pid}")

        return JsonResponse(
            {
                "success": True,
                "message": f"Live démarré avec succès (PID: {process.pid})",
            }
        )

    except Exception as e:
        print(f"[DEBUG] Erreur lors du démarrage du live {live.id}: {str(e)}")
        live.status = "failed"
        live.save()
        return JsonResponse(
            {"success": False, "message": f"Erreur lors du démarrage: {str(e)}"}
        )


@login_required
@require_POST
def stop_live(request, live_id):
    """Arrêt d'un live."""
    live = get_object_or_404(Live, id=live_id, user=request.user)

    if not live.is_running:
        return JsonResponse({"success": False, "message": "Live non en cours"})

    try:
        # Arrêter le processus FFmpeg si un PID est enregistré
        if live.ffmpeg_pid:
            print(f"[DEBUG] Arrêt du live {live.id} avec PID {live.ffmpeg_pid}")

            try:
                # Arrêter le processus selon la plateforme
                if sys.platform.startswith("win"):
                    # Windows: utiliser taskkill
                    subprocess.run(
                        ["taskkill", "/F", "/PID", str(live.ffmpeg_pid)],
                        capture_output=True,
                        timeout=10,
                    )
                else:
                    # Linux/Unix: utiliser os.kill
                    os.kill(live.ffmpeg_pid, 15)  # SIGTERM

                    # Attendre un peu pour voir si le processus s'arrête
                    import time

                    time.sleep(2)

                    # Vérifier si le processus existe encore
                    try:
                        os.kill(live.ffmpeg_pid, 0)  # Test si le processus existe
                        # Si on arrive ici, le processus existe encore, le forcer
                        os.kill(live.ffmpeg_pid, 9)  # SIGKILL
                        print(f"[DEBUG] Processus {live.ffmpeg_pid} forcé à s'arrêter")
                    except OSError:
                        print(f"[DEBUG] Processus {live.ffmpeg_pid} arrêté proprement")

            except Exception as e:
                print(
                    f"[DEBUG] Erreur lors de l'arrêt du processus "
                    f"{live.ffmpeg_pid}: {e}"
                )
                # Le processus n'existe peut-être plus, continuer

        # Mettre à jour le statut
        live.status = "completed"
        live.ffmpeg_pid = None
        live.save()

        print(f"[DEBUG] Live {live.id} arrêté avec succès")

        return JsonResponse({"success": True, "message": "Live arrêté avec succès"})

    except Exception as e:
        print(f"[DEBUG] Erreur lors de l'arrêt du live {live.id}: {str(e)}")
        return JsonResponse(
            {"success": False, "message": f"Erreur lors de l'arrêt: {str(e)}"}
        )


@login_required
def check_approval_status(request):
    """Vérifier le statut d'approbation de l'utilisateur (AJAX)."""
    return JsonResponse(
        {"is_approved": request.user.is_approved, "username": request.user.username}
    )


@user_passes_test(is_admin)
def admin_dashboard(request):
    """Dashboard administrateur."""
    total_users = User.objects.count()
    approved_users = User.objects.filter(is_approved=True).count()
    total_lives = Live.objects.count()
    running_lives = Live.objects.filter(status="running").count()
    context = {
        "total_users": total_users,
        "approved_users": approved_users,
        "total_lives": total_lives,
        "running_lives": running_lives,
    }
    return render(request, "streams/admin_dashboard.html", context)


@user_passes_test(is_admin)
def admin_users(request):
    """Gestion des utilisateurs par l'admin."""
    users = User.objects.all().order_by("-date_joined")
    return render(request, "streams/admin_users.html", {"users": users})


@user_passes_test(is_admin)
@require_POST
def approve_user(request, user_id):
    """Approuver un utilisateur."""
    user = get_object_or_404(User, id=user_id)
    user.is_approved = True
    user.save()

    # Forcer la mise à jour de la session si l'utilisateur est connecté
    if user.is_authenticated:
        # Mettre à jour la session de l'utilisateur
        from django.contrib.auth import update_session_auth_hash

        update_session_auth_hash(request, user)

    messages.success(request, f"Utilisateur {user.username} approuvé avec succès !")
    return redirect("admin_users")


@user_passes_test(is_admin)
@require_POST
def reject_user(request, user_id):
    """Rejeter un utilisateur."""
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, f"Utilisateur {user.username} rejeté et supprimé.")
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
