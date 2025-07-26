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
    """Démarre un live avec FFmpeg."""
    try:
        live = Live.objects.get(id=live_id)
        
        if live.status != 'pending':
            return False
        
        # Chemin vers la vidéo
        video_path = live.video_file.path
        
        # Commande FFmpeg
        ffmpeg_cmd = [
            'setsid',
            settings.FFMPEG_PATH,
            '-re',
            '-stream_loop', '-1',
            '-i', video_path,
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-b:v', '500k',
            '-maxrate', '800k',
            '-bufsize', '1200k',
            '-s', '640x360',
            '-g', '60',
            '-keyint_min', '60',
            '-c:a', 'aac',
            '-b:a', '96k',
            '-f', 'flv',
            '-reconnect', '1',
            '-reconnect_streamed', '1',
            '-reconnect_delay_max', '2',
            f"rtmp://a.rtmp.youtube.com/live2/{live.stream_key}"
        ]
        
        # Démarrage du processus FFmpeg
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        
        # Mise à jour du statut
        live.status = 'running'
        live.ffmpeg_pid = process.pid
        live.save()
        
        # Notification à l'admin
        send_admin_notification.delay(live_id)
        
        return True
        
    except Exception as e:
        # En cas d'erreur
        live.status = 'failed'
        live.save()
        
        # Notification d'erreur
        send_error_notification.delay(live_id, str(e))
        
        return False


@shared_task
def stop_live_stream(live_id):
    """Arrête un live en cours."""
    try:
        live = Live.objects.get(id=live_id)
        
        if live.status != 'running' or not live.ffmpeg_pid:
            return False
        
        # Arrêt du processus FFmpeg
        try:
            os.kill(live.ffmpeg_pid, signal.SIGKILL)
        except ProcessLookupError:
            pass  # Le processus n'existe plus
        
        # Mise à jour du statut
        live.status = 'completed'
        live.ffmpeg_pid = None
        live.save()
        
        return True
        
    except Exception as e:
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
        is_scheduled=True,
        status='pending',
        scheduled_at__lte=now
    )
    
    for live in scheduled_lives:
        start_live_stream.delay(live.id) 