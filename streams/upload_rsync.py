import os
import subprocess
import time
import shutil


def upload_with_rsync(
    local_file, remote_user, remote_host, remote_path, max_retries=3, timeout=300
):
    """
    Upload un fichier avec rsync et retry automatique.
    Retourne (True, message) ou (False, erreur)
    """
    print(
        f"[RSYNC] Début upload: {local_file} -> {remote_user}@{remote_host}:{remote_path}"
    )

    if not os.path.exists(local_file):
        error_msg = f"Fichier local non trouvé: {local_file}"
        print(f"[RSYNC] ERREUR: {error_msg}")
        return False, error_msg

    if not shutil.which("rsync"):
        error_msg = "rsync n'est pas installé sur le système"
        print(f"[RSYNC] ERREUR: {error_msg}")
        return False, error_msg

    rsync_cmd = [
        "rsync",
        "-avz",
        "--progress",
        "--partial",
        "--inplace",
        f"--timeout={timeout}",
        local_file,
        f"{remote_user}@{remote_host}:{remote_path}",
    ]

    print(f"[RSYNC] Commande: {' '.join(rsync_cmd)}")

    for attempt in range(1, max_retries + 1):
        print(f"[RSYNC] Tentative {attempt}/{max_retries}")
        try:
            result = subprocess.run(
                rsync_cmd, capture_output=True, timeout=timeout, text=True
            )
            print(f"[RSYNC] Code de retour: {result.returncode}")
            print(f"[RSYNC] Sortie stdout: {result.stdout}")
            print(f"[RSYNC] Sortie stderr: {result.stderr}")

            if result.returncode == 0:
                success_msg = f"Upload réussi (tentative {attempt})"
                print(f"[RSYNC] SUCCÈS: {success_msg}")
                return True, success_msg
            else:
                error_msg = f"Erreur rsync (code {result.returncode}): {result.stderr}"
                print(f"[RSYNC] ERREUR: {error_msg}")

                if attempt < max_retries:
                    print(f"[RSYNC] Nouvelle tentative dans 5 secondes...")
                    time.sleep(5)
                else:
                    return False, error_msg

        except subprocess.TimeoutExpired:
            error_msg = f"Timeout après {timeout} secondes"
            print(f"[RSYNC] TIMEOUT: {error_msg}")

            if attempt < max_retries:
                print(f"[RSYNC] Nouvelle tentative dans 5 secondes...")
                time.sleep(5)
            else:
                return False, "Timeout après toutes les tentatives"

        except Exception as e:
            error_msg = f"Erreur inattendue: {str(e)}"
            print(f"[RSYNC] EXCEPTION: {error_msg}")
            return False, error_msg

    return False, f"Échec après {max_retries} tentatives"
