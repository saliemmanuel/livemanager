import os
import subprocess
import time
import shutil

def upload_with_rsync(local_file, remote_user, remote_host, remote_path, max_retries=3, timeout=300):
    """
    Upload un fichier avec rsync et retry automatique.
    Retourne (True, message) ou (False, erreur)
    """
    if not os.path.exists(local_file):
        return False, f"Fichier local non trouvé: {local_file}"

    if not shutil.which("rsync"):
        return False, "rsync n'est pas installé sur le système"

    rsync_cmd = [
        "rsync", "-avz", "--progress", "--partial", "--inplace", f"--timeout={timeout}",
        local_file, f"{remote_user}@{remote_host}:{remote_path}"
    ]

    for attempt in range(1, max_retries + 1):
        try:
            result = subprocess.run(
                rsync_cmd,
                capture_output=True,
                timeout=timeout,
                text=True
            )
            if result.returncode == 0:
                return True, f"Upload réussi (tentative {attempt})"
            else:
                if attempt < max_retries:
                    time.sleep(5)
                else:
                    return False, f"Erreur rsync: {result.stderr}"
        except subprocess.TimeoutExpired:
            if attempt < max_retries:
                time.sleep(5)
            else:
                return False, "Timeout après toutes les tentatives"
        except Exception as e:
            return False, f"Erreur: {str(e)}"
    return False, f"Échec après {max_retries} tentatives" 