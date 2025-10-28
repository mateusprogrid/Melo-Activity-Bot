# auto_commits.py (versão robusta)
import os
import random
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# ========== CONFIG ==========
# Se o script estiver na raiz do repo, use a linha abaixo:
REPO_PATH = Path(__file__).resolve().parent

# Se preferir caminho fixo, DESCOMENTE e edite (use r"..." para evitar escape de \):
# REPO_PATH = Path(r"C:\Users\mateu.MATEUS\OneDrive\Documentos\MateusMeloProfissional\ProjetosPessoais\Melo-Activity-Bot")

BRANCH = "main"
MIN_COMMITS = 5
MAX_COMMITS = 15
SLEEP_BETWEEN_COMMITS_SECONDS = (5, 25)
HEARTBEAT_DIR = ".heartbeat"
RANDOMIZE_GIT_DATES = True
DAY_WINDOW_START = (9, 0)
DAY_WINDOW_END   = (22, 30)
# ===========================

def run(cmd, cwd=None, env=None):
    print(f"$ {cmd}  (cwd={cwd})")
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env, check=True, shell=True)

def is_git_repo(path: Path) -> bool:
    try:
        subprocess.run("git rev-parse --is-inside-work-tree", cwd=str(path), shell=True,
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def has_remote_origin(path: Path) -> bool:
    try:
        out = subprocess.check_output("git remote", cwd=str(path), shell=True, text=True)
        return "origin" in [r.strip() for r in out.splitlines()]
    except subprocess.CalledProcessError:
        return False

def random_time_today():
    today = datetime.now()
    start = today.replace(hour=DAY_WINDOW_START[0], minute=DAY_WINDOW_START[1], second=0, microsecond=0)
    end   = today.replace(hour=DAY_WINDOW_END[0],   minute=DAY_WINDOW_END[1],   second=0, microsecond=0)
    if end <= start:
        end += timedelta(days=1)
    delta = end - start
    seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=seconds)

def ensure_branch(repo_path: Path, branch: str):
    if not repo_path.exists():
        raise SystemExit(f"[ERRO] REPO_PATH não existe: {repo_path}")
    if not is_git_repo(repo_path):
        raise SystemExit(
            f"[ERRO] '{repo_path}' não é um repositório Git (não encontrei a pasta .git).\n"
            f"→ Confirme o caminho com 'git rev-parse --show-toplevel' e ajuste REPO_PATH."
        )

    # checkout (cria a branch se não existir)
    try:
        run(f"git checkout {branch}", cwd=repo_path)
    except subprocess.CalledProcessError:
        print(f"[INFO] Branch '{branch}' não existe localmente. Criando…")
        run(f"git checkout -b {branch}", cwd=repo_path)

    if has_remote_origin(repo_path):
        try:
            run("git fetch --all", cwd=repo_path)
            run(f"git pull --rebase origin {branch}", cwd=repo_path)
        except subprocess.CalledProcessError:
            print("[WARN] pull/rebase falhou. Tentando setar upstream…")
            run(f"git push -u origin {branch}", cwd=repo_path)
    else:
        print("[INFO] Sem remoto 'origin'. Commits ficarão locais até você adicionar um.")

def main():
    repo = Path(REPO_PATH)
    print(f"[DEBUG] REPO_PATH={repo}")

    ensure_branch(repo, BRANCH)

    hb_dir = repo / HEARTBEAT_DIR
    hb_dir.mkdir(parents=True, exist_ok=True)

    today_str = datetime.now().strftime("%Y-%m-%d")
    hb_file = hb_dir / f"{today_str}.md"
    if not hb_file.exists():
        hb_file.write_text(f"# Heartbeat {today_str}\n")

    n_commits = random.randint(MIN_COMMITS, MAX_COMMITS)
    print(f"[AutoCommits] Gerando {n_commits} commits...")

    for i in range(1, n_commits + 1):
        now = datetime.now().strftime("%H:%M:%S")
        hb_file.write_text(hb_file.read_text() + f"- update {i} às {now}\n")

        run('git add .', cwd=repo)

        commit_env = os.environ.copy()
        if RANDOMIZE_GIT_DATES:
            fake_dt = random_time_today()
            stamp = fake_dt.strftime("%Y-%m-%d %H:%M:%S")
            commit_env["GIT_AUTHOR_DATE"] = stamp
            commit_env["GIT_COMMITTER_DATE"] = stamp
            msg = f'auto: heartbeat {today_str} ({i}/{n_commits}) @ {stamp}'
        else:
            msg = f'auto: heartbeat {today_str} ({i}/{n_commits})'

        run(f'git commit -m "{msg}"', cwd=repo, env=commit_env)

        time.sleep(random.randint(*SLEEP_BETWEEN_COMMITS_SECONDS))

    run(f'git push origin {BRANCH}', cwd=repo)
    print("[AutoCommits] Concluído.")

if __name__ == "__main__":
    main()
