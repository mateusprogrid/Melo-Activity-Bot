# auto_commits.py
import os
import random
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# ========== CONFIG ==========
REPO_PATH = r"C:\caminho\para\seu\repositorio"  # <<< edite
BRANCH = "main"                                  # ou "master"
MIN_COMMITS = 5                                  # <<< edite
MAX_COMMITS = 15                                 # <<< edite
SLEEP_BETWEEN_COMMITS_SECONDS = (5, 25)          # variação entre commits no mesmo dia
HEARTBEAT_DIR = ".heartbeat"                     # pasta dos arquivos de log/heartbeat
# Se quiser simular horários diferentes do dia (carimbar autor/committer date):
RANDOMIZE_GIT_DATES = True
# Janela de horários aleatórios neste dia (ex.: entre 09:00 e 22:30)
DAY_WINDOW_START = (9, 0)    # 09:00
DAY_WINDOW_END   = (22, 30)  # 22:30
# ===========================

def run(cmd, cwd=None, env=None):
    subprocess.run(cmd, cwd=cwd, env=env, check=True, shell=True)

def random_time_today():
    today = datetime.now()
    start = today.replace(hour=DAY_WINDOW_START[0], minute=DAY_WINDOW_START[1], second=0, microsecond=0)
    end   = today.replace(hour=DAY_WINDOW_END[0], minute=DAY_WINDOW_END[1], second=0, microsecond=0)
    if end <= start:
        end += timedelta(days=1)
    delta = end - start
    seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=seconds)

def ensure_branch(repo_path, branch):
    # Garante checkout na branch correta e sincroniza
    run(f'git fetch --all', cwd=repo_path)
    run(f'git checkout {branch}', cwd=repo_path)
    # Pull rebase para evitar commits desalinhados
    run(f'git pull --rebase origin {branch}', cwd=repo_path)

def main():
    repo = Path(REPO_PATH)
    assert repo.exists(), f"Repo path não existe: {repo}"

    ensure_branch(repo, BRANCH)

    hb_dir = repo / HEARTBEAT_DIR
    hb_dir.mkdir(parents=True, exist_ok=True)

    # Um arquivo por dia (mantém histórico limpo)
    today_str = datetime.now().strftime("%Y-%m-%d")
    hb_file = hb_dir / f"{today_str}.md"
    if not hb_file.exists():
        hb_file.write_text(f"# Heartbeat {today_str}\n")

    n_commits = random.randint(MIN_COMMITS, MAX_COMMITS)
    print(f"[AutoCommits] Gerando {n_commits} commits...")

    for i in range(1, n_commits + 1):
        # Conteúdo diferente em cada commit
        now = datetime.now().strftime("%H:%M:%S")
        hb_file.write_text(hb_file.read_text() + f"- update {i} às {now}\n")

        # Add e commit
        run('git add .', cwd=repo)

        commit_env = os.environ.copy()
        if RANDOMIZE_GIT_DATES:
            fake_dt = random_time_today()
            # Git respeita estas variáveis de ambiente para carimbar data do commit
            stamp = fake_dt.strftime("%Y-%m-%d %H:%M:%S")
            commit_env["GIT_AUTHOR_DATE"] = stamp
            commit_env["GIT_COMMITTER_DATE"] = stamp
            msg = f'auto: heartbeat {today_str} ({i}/{n_commits}) @ {stamp}'
        else:
            msg = f'auto: heartbeat {today_str} ({i}/{n_commits})'

        run(f'git commit -m "{msg}"', cwd=repo, env=commit_env)

        # Pausa aleatória entre commits (humaniza um pouco)
        time.sleep(random.randint(*SLEEP_BETWEEN_COMMITS_SECONDS))

    # Push no final
    run(f'git push origin {BRANCH}', cwd=repo)
    print("[AutoCommits] Concluído com sucesso.")

if __name__ == "__main__":
    main()