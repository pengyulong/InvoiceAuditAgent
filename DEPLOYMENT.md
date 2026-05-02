# 智能合同发票审计系统部署文档

## 1. 部署包内容

部署包包含：

- `backend/`：FastAPI 后端源码。
- `frontend/dist/`：已构建好的前端静态文件。
- `.env.example`：环境变量模板。
- `deploy/start_backend.sh`：单机启动后端脚本。
- `deploy/invoice-audit.service.example`：systemd 服务示例。
- `deploy/nginx.conf.example`：Nginx 反向代理示例。

默认登录账号：

- 用户名：`admin`
- 密码：`gsfPYL1989323`

上线后建议在 `.env` 中修改 `AUTH_PASSWORD` 和 `SECRET_KEY`。

## 2. 服务器依赖

建议服务器环境：

- Ubuntu 22.04+
- Python 3.10+
- Node.js 20+（仅当需要在服务器重新构建前端）
- Nginx
- Poppler 工具：`pdfinfo`、`pdftoppm`

安装基础依赖：

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx poppler-utils unzip
```

## 3. 解压部署包

```bash
sudo mkdir -p /opt/InvoiceAuditAgent
sudo tar -xzf InvoiceAuditAgent-deploy.tar.gz -C /opt/InvoiceAuditAgent --strip-components=1
sudo chown -R www-data:www-data /opt/InvoiceAuditAgent
```

## 4. 配置环境变量

```bash
cd /opt/InvoiceAuditAgent
sudo cp .env.example .env
sudo nano .env
```

生产环境至少修改：

```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=replace-with-a-long-random-secret
AUTH_USERNAME=admin
AUTH_PASSWORD=replace-with-your-password
DATABASE_URL=sqlite+aiosqlite:///./audit.db
UPLOAD_DIR=uploads
LOG_FILE=logs/app.log
ALLOWED_HOSTS=["http://your-domain.com","https://your-domain.com"]
```

并填写 OCR/AI 模型密钥：

```env
BAIDU_OCR_API_KEY=your-baidu-ocr-api-key
BAIDU_OCR_SECRET_KEY=your-baidu-ocr-secret-key
DEEPSEEK_API_KEY=your-deepseek-api-key
```

## 5. 初始化后端

```bash
cd /opt/InvoiceAuditAgent/backend
sudo -u www-data python3 -m venv .venv
sudo -u www-data .venv/bin/python -m pip install --upgrade pip
sudo -u www-data .venv/bin/python -m pip install -r requirements.txt
sudo -u www-data mkdir -p uploads logs
```

手动启动验证：

```bash
sudo -u www-data .venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

## 6. 配置 systemd

```bash
sudo cp /opt/InvoiceAuditAgent/deploy/invoice-audit.service.example /etc/systemd/system/invoice-audit.service
sudo systemctl daemon-reload
sudo systemctl enable invoice-audit
sudo systemctl start invoice-audit
sudo systemctl status invoice-audit
```

## 7. 配置 Nginx

```bash
sudo cp /opt/InvoiceAuditAgent/deploy/nginx.conf.example /etc/nginx/sites-available/invoice-audit
sudo nano /etc/nginx/sites-available/invoice-audit
sudo ln -s /etc/nginx/sites-available/invoice-audit /etc/nginx/sites-enabled/invoice-audit
sudo nginx -t
sudo systemctl reload nginx
```

访问：

```text
http://your-domain.com/login
```

## 8. 验证登录和鉴权

未登录访问业务接口应返回 `401`：

```bash
curl -i http://127.0.0.1:8000/api/v1/upload/sample
```

登录获取 token：

```bash
curl -s -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"gsfPYL1989323"}' \
  http://127.0.0.1:8000/api/v1/auth/login
```

浏览器打开 `/login` 后登录，进入上传页即可使用。

## 9. 常见问题

- 上传大文件失败：确认 Nginx `client_max_body_size 60m` 已生效。
- PDF 无法识别页数：确认服务器安装了 `poppler-utils`。
- WebSocket 无进度：确认 Nginx `/ws/` 配置包含 `Upgrade` 和 `Connection` 头。
- 生产环境看不到 `/docs`：这是预期行为，`ENVIRONMENT=production` 会关闭 API 文档。
