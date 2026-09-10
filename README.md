# B2B 外贸官网模板

面向海外客户的高端 B2B 外贸企业官网模板。基于 **Python + FastAPI + SQLite + Docker + Nginx**，
集成 **GitHub Actions + GHCR** 实现「代码提交 → 自动构建镜像 → 自动部署服务器 → 客户询盘邮件提醒」
的完整自动化流程。

- 设计风格：现代科技感 × 极简杂志风，响应式适配桌面 / 平板 / 手机
- 所有公司信息、联系方式、SEO、邮箱通知、域名、端口统一通过 `.env` 管理
- 询盘自动入库（SQLite）+ 邮件通知销售 + 自动回复客户确认函
- SEO 完备：canonical、OG/Twitter Card、Organization/Product/面包屑 JSON-LD、sitemap、robots

## 项目结构

```
外贸官网/
├─ app/
│  ├─ main.py              # FastAPI 入口、异常页、静态资源挂载
│  ├─ config.py            # 全部配置项（从 .env 读取）
│  ├─ database.py          # SQLite 连接与建表
│  ├─ models.py            # 询盘数据模型
│  ├─ schemas.py           # 询盘表单校验（含蜜罐字段）
│  ├─ email_service.py     # 询盘通知邮件 + 客户自动回复
│  ├─ catalog.py / catalog.json   # 产品目录（改内容只改 catalog.json）
│  ├─ routers/
│  │  ├─ pages.py          # 页面路由 + sitemap.xml / robots.txt / health
│  │  └─ api.py            # POST /api/inquiries（限流 + 蜜罐）
│  ├─ templates/           # Jinja2 模板（首页/产品/详情/关于/联系/404/500）
│  └─ static/              # CSS 设计系统 + JS 交互
├─ nginx/nginx.conf        # Nginx 反向代理（静态资源直出 + 反代 FastAPI）
├─ Dockerfile              # 应用镜像（python:3.12-slim，非 root 运行）
├─ docker-compose.yml      # app + nginx 编排，数据命名卷持久化
├─ scripts/deploy.sh       # 服务器端部署脚本（CI 通过 SSH 调用）
├─ .github/workflows/deploy.yml   # CI/CD 流水线
├─ .env.example            # 配置模板（复制为 .env 使用）
└─ requirements.txt
```

## 本地运行

```bash
# 1. 准备配置
cp .env.example .env        # Windows PowerShell: copy .env.example .env

# 2. 方式一：Docker（推荐，与生产一致）
docker compose up -d --build
# 访问 http://localhost:8080  （端口由 .env 的 NGINX_HTTP_PORT 控制）

# 3. 方式二：Python 直跑（需 Python 3.11+）
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# 访问 http://localhost:8000
```

> - 未配置 SMTP 时网站功能完全正常，询盘只入库不发邮件，日志会提示 `SMTP not configured`。
> - 若部署目录为中文（如 `外贸官网/`），`.env` 中的 `COMPOSE_PROJECT_NAME` 必须保留，
>   否则 Docker Compose 会报 `project name must not be empty`。

## .env 配置项说明

| 变量 | 说明 |
|---|---|
| `COMPOSE_PROJECT_NAME` | Compose 项目名（小写英文/短横线）；部署目录为中文名时必须显式指定 |
| `SITE_DOMAIN` | 站点正式域名（含 https，不带尾斜杠），用于 canonical / sitemap / OG |
| `NGINX_HTTP_PORT` | 宿主机对外 HTTP 端口（服务器防火墙需放行） |
| `COMPANY_*` | 公司名称、标语、简介、成立年份、员工数、出口国家数、厂房面积 |
| `COMPANY_EMAIL / PHONE / WHATSAPP / ADDRESS / HOURS` | 联系方式（页脚 / 联系页 / 邮件共用） |
| `LINKEDIN_URL / FACEBOOK_URL / YOUTUBE_URL / INSTAGRAM_URL` | 社交链接，留空自动隐藏 |
| `SEO_TITLE / SEO_DESCRIPTION / SEO_KEYWORDS / SEO_OG_IMAGE` | 全站 SEO 信息 |
| `DATABASE_URL` | SQLite 路径，默认容器内 `/app/data/inquiries.db`（已挂载持久化卷） |
| `SMTP_HOST / PORT / USER / PASSWORD / FROM / FROM_NAME` | 发信邮箱（465=SSL，587=STARTTLS） |
| `MAIL_TO` | 接收询盘通知的销售邮箱 |
| `GHCR_IMAGE` | 服务器拉取的镜像地址，CI 部署时会自动写入 |

### 邮件提醒流程

客户在联系页提交询盘 → 后端校验（蜜罐 + 每 IP 5 次/小时限流）→ 存入 SQLite：

1. 向 `MAIL_TO` 发送询盘通知（含客户全部信息与留言，**Reply-To 设为客户邮箱**，可直接回复）
2. 向客户发送自动确认函（告知 24 工作小时内回复）

邮件发送失败不影响询盘入库，数据不丢失。

## 自动化部署（GitHub + GitHub Actions + GHCR）

1. 将本仓库推送到 GitHub；
2. 在仓库 **Settings → Secrets and variables → Actions** 添加：

   | Secret | 说明 |
   |---|---|
   | `SSH_HOST` | 服务器 IP 或域名 |
   | `SSH_USER` | SSH 用户（需在 docker 用户组） |
   | `SSH_PORT` | SSH 端口，默认 22（可省略） |
   | `SSH_PRIVATE_KEY` | 登录服务器的私钥 |
   | `DEPLOY_PATH` | 服务器部署目录，如 `/opt/b2b-website`（建议用英文目录名） |
   | `GHCR_USERNAME` | GitHub 用户名 |
   | `GHCR_TOKEN` | PAT，需 `read:packages`（私有仓库再加 `repo`） |

3. 服务器首次准备：安装 Docker Engine + Compose 插件，在 `DEPLOY_PATH` 放好填好的 `.env`；
4. 之后每次 `git push origin main` 自动完成：

   ```
   构建镜像 → 推送 ghcr.io/<owner>/<repo>:latest（+ :sha）
          → SSH 执行 scripts/deploy.sh
          → git 同步配置 → docker login → compose pull → 滚动重启
   ```

   镜像构建失败不会部署；部署失败不影响线上旧容器（compose 滚动更新）。

## 自定义内容

- **增删 / 修改产品**：编辑 [app/catalog.json](app/catalog.json)（每个产品含名称、分类、特性、参数表、图片描述），无需改代码
- **页面文案 / 布局**：编辑 [app/templates/](app/templates/) 下对应模板
- **配色与字体**：编辑 [app/static/css/style.css](app/static/css/style.css) 顶部 `:root` 设计变量
- **产品图片**：默认按 `image_prompt` 由文生图接口动态生成；如需替换为实拍图，
  将图片放入 `app/static/img/` 并把 `catalog.json` 中产品加上 `"image": "/static/img/xxx.jpg"`
  （优先级高于自动生成）

## 常用运维命令

```bash
docker compose ps            # 查看容器状态（app 应为 healthy）
docker compose logs -f app   # 跟踪应用日志（含询盘/邮件记录）
docker compose down          # 停止并移除容器（数据卷保留，询盘不丢）
docker compose up -d --build # 改完代码后重建并滚动更新
docker volume ls             # 查看 b2b-website_app_data / _app_static 数据卷
```

## 上线域名与 HTTPS

- Nginx 使用通配 `server_name`，域名解析到服务器即可访问；
- 正式上线建议在 Nginx 前加 443 证书（可自行接入 Caddy / certbot 做 Let's Encrypt 自动续期）。
