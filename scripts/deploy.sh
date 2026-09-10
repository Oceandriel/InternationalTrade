#!/usr/bin/env bash
# ==========================================================================
#  服务器端一键部署脚本（由 GitHub Actions 通过 SSH 调用，也可手动执行）
#
#  流程：同步仓库配置 -> 校验 .env -> 写入最新镜像地址 ->
#        登录 GHCR -> 拉取镜像 -> 滚动重启 -> 清理旧镜像
#
#  所需环境变量（由 CI 注入；手动执行时自行 export）：
#    DEPLOY_PATH    部署目录，如 /opt/b2b-website
#    IMAGE_NAME     镜像名，如 ghcr.io/owner/repo
#    GHCR_USERNAME  GHCR 登录用户名（GitHub 用户名）
#    GHCR_TOKEN     具备 read:packages（私有仓库加 repo）权限的 PAT
#    REPO_URL       仓库克隆地址
#
#  服务器前置要求：Docker Engine + Compose 插件，SSH 用户在 docker 用户组
# ==========================================================================
set -euo pipefail

: "${DEPLOY_PATH:?DEPLOY_PATH is required}"
: "${IMAGE_NAME:?IMAGE_NAME is required}"
: "${GHCR_USERNAME:?GHCR_USERNAME is required}"
: "${GHCR_TOKEN:?GHCR_TOKEN is required}"
: "${REPO_URL:?REPO_URL is required}"

mkdir -p "$DEPLOY_PATH"
cd "$DEPLOY_PATH"

echo "==> [1/5] Syncing repository (docker-compose.yml / nginx config)..."
if [ -d ".git" ]; then
  git fetch --depth 1 origin main
  git reset --hard origin/main
else
  git init
  git remote add origin "$REPO_URL" || git remote set-url origin "$REPO_URL"
  git fetch --depth 1 origin main
  git checkout -B main origin/main -f
fi

echo "==> [2/5] Checking .env..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "ERROR: $DEPLOY_PATH/.env did not exist. A template has been copied —" >&2
  echo "       fill in real company info / SMTP / domain, then re-run the deploy." >&2
  exit 1
fi

echo "==> [3/5] Updating GHCR_IMAGE in .env..."
if grep -q '^GHCR_IMAGE=' .env; then
  sed -i "s|^GHCR_IMAGE=.*|GHCR_IMAGE=${IMAGE_NAME}:latest|" .env
else
  echo "GHCR_IMAGE=${IMAGE_NAME}:latest" >> .env
fi

echo "==> [4/5] Logging in to GHCR and pulling the latest image..."
echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USERNAME" --password-stdin
docker compose pull

echo "==> [5/5] Restarting services..."
docker compose up -d --remove-orphans
docker image prune -f

echo ""
echo "✅ Deploy finished: ${IMAGE_NAME}:latest"
docker compose ps
