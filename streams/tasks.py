import subprocess
import os
import signal
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from .models import Live


@shared_task
def start_live_stream(live_id):
    """Démarre un live en utilisant FFmpeg."""
    try:
        live = Live.objects.get(id=live_id)

        if live.status != "pending":
            return False

        # Vérifier que l'utilisateur est approuvé
        if not live.user.is_approved:
            return False

        # Chemin vers FFmpeg
        ffmpeg_path = getattr(settings, "FFMPEG_PATH", "/usr/bin/ffmpeg")

        # Commande FFmpeg pour YouTube Live
        command = [
            ffmpeg_path,
            "-re",  # Lire à la vitesse réelle
            "-i",
            live.video_file.path,  # Fichier d'entrée
            "-c:v",
            "libx264",  # Codec vidéo
            "-preset",
            "ultrafast",  # Preset pour streaming
            "-tune",
            "zerolatency",  # Optimisation latence
            "-c:a",
            "aac",  # Codec audio
            "-b:a",
            "128k",  # Bitrate audio
            "-f",
            "flv",  # Format de sortie
            f"rtmp://a.rtmp.youtube.com/live2/{live.stream_key}",  # URL YouTube
        ]

        # Démarrer le processus FFmpeg
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Sauvegarder le PID
        live.ffmpeg_pid = process.pid
        live.status = "running"
        live.save()

        # Notification admin
        send_admin_notification.delay(live_id)

        return True

    except Exception as e:
        # En cas d'erreur
        live.status = "failed"
        live.save()

        # Notification d'erreur
        send_error_notification.delay(live_id, str(e))

        return False


@shared_task
def stop_live_stream(live_id):
    """Arrête un live en cours."""
    try:
        live = Live.objects.get(id=live_id)

        if live.status != "running" or not live.ffmpeg_pid:
            return False

        # Arrêt du processus FFmpeg
        try:
            os.kill(live.ffmpeg_pid, signal.SIGKILL)
        except ProcessLookupError:
            pass  # Le processus n'existe plus

        # Mise à jour du statut
        live.status = "completed"
        live.ffmpeg_pid = None
        live.save()

        return True

    except Exception:
        return False


@shared_task
def send_admin_notification(live_id):
    """Envoie une notification à l'admin lors du démarrage d'un live."""
    try:
        live = Live.objects.get(id=live_id)

        # Trouver les admins
        admins = Live.objects.filter(user__is_admin=True)

        for admin in admins:
            send_mail(
                subject=f"Live démarré: {live.title}",
                message=f"""
                Un live a été démarré:

                Titre: {live.title}
                Utilisateur: {live.user.email}
                Heure: {timezone.now()}
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin.user.email],
                fail_silently=True,
            )
    except Exception:
        pass


@shared_task
def send_error_notification(live_id, error_message):
    """Envoie une notification d'erreur."""
    try:
        live = Live.objects.get(id=live_id)

        send_mail(
            subject=f"Erreur lors du démarrage du live: {live.title}",
            message=f"""
            Une erreur s'est produite lors du démarrage du live:

            Titre: {live.title}
            Utilisateur: {live.user.email}
            Erreur: {error_message}
            Heure: {timezone.now()}
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[live.user.email],
            fail_silently=True,
        )
    except Exception:
        pass


@shared_task
def check_scheduled_lives():
    """Vérifie et démarre les lives programmés."""
    now = timezone.now()

    # Trouver les lives programmés à démarrer
    scheduled_lives = Live.objects.filter(
        is_scheduled=True, status="pending", scheduled_at__lte=now
    )

    for live in scheduled_lives:
        start_live_stream.delay(live.id)
