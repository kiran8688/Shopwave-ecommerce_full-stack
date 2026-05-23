# ShopWave — Full-Stack E-Commerce Platform

> **Stack:** React 19 + Tailwind CSS · FastAPI + Python 3.14 · PostgreSQL 18 · Docker Compose · MCP Servers

---

## Quick Start (Docker)

```bash
# 1. Clone and enter the project
git clone https://github.com/your-org/shopwave.git
cd shopwave

# 2. Copy env files and fill in secrets
cp .env.example .env
cp backend/.env.example backend/.env

# 3. Generate a secure secret key
python -c "import secrets; print(secrets.token_hex(32))"
# Paste the output as SECRET_KEY in .env and backend/.env

# 4. Start all services
docker compose up --build

# Services:
#   Frontend  → http://localhost:3000
#   Backend   → http://localhost:8000
#   API Docs  → http://localhost:8000/docs
#   Database  → localhost:5432
```

---

## Project Structure

```
shopwave/
├── backend/                   # FastAPI application
│   ├── app/
│   │   ├── api/v1/endpoints/  # auth, users, products, categories, orders
│   │   ├── core/              # config, security (pwdlib + pyjwt), dependencies
│   │   ├── db/                # SQLAlchemy session + declarative base
│   │   ├── models/            # ORM models (User, Product, Category, Order, OrderItem)
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── services/          # Business logic layer
│   │   └── utils/             # MCP client, pagination, exceptions
│   ├── alembic/               # Database migrations
│   ├── pyproject.toml         # Python 3.14 dependencies
│   └── Dockerfile             # Multi-stage production build
│
├── frontend/                  # React 19 application
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/        # Navbar, Footer, Layout
│   │   │   ├── ui/            # ProductCard, LoadingSpinner
│   │   │   └── features/      # PaymentModal
│   │   ├── pages/             # Home, Products, ProductDetail, Cart, Checkout, Auth, Orders, Profile
│   │   ├── hooks/             # useAuth, useCart, useSemanticSearch
│   │   ├── services/          # api.js (axios), auth.service.js, product.service.js
│   │   ├── store/             # authStore (Zustand), cartStore (Zustand + persist)
│   │   └── utils/             # helpers (formatINR, truncate, shortId, formatDate)
│   ├── package.json
│   └── Dockerfile             # Vite build + Nginx serve
│
├── mcp-servers/               # Model Context Protocol servers
│   ├── inventory/             # Stock monitoring + reorder intelligence
│   ├── payments/              # Razorpay abstraction layer
│   ├── search/                # Semantic search via pgvector + Voyage-3
│   ├── notifications/         # Transactional email via SendGrid
│   ├── analytics/             # Sales BI queries
│   └── content/               # AI product descriptions via Claude
│
├── nginx/nginx.conf           # Nginx SPA + API proxy config
├── docker-compose.yml         # Full stack orchestration
└── docs/
    └── implementation_sequence_guide.md  # MCP integration roadmap
```

---

## Database Schema

| Table | Key Columns |
|---|---|
| `users` | id (UUID), email (unique), username, hashed_password, role, is_active |
| `categories` | id, name, slug, parent_id (self-ref FK) |
| `products` | id, name, sku (unique), price (NUMERIC), stock_quantity, category_id |
| `orders` | id, user_id, status, total_amount, shipping_* (snapshot), payment_status |
| `order_items` | id, order_id, product_id, unit_price (snapshot), quantity, line_total |

---

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register` | Public | Create account |
| POST | `/api/v1/auth/login` | Public | OAuth2 login → JWT |
| POST | `/api/v1/auth/logout` | Public | Clear refresh cookie |
| GET | `/api/v1/users/me` | User | Own profile |
| GET | `/api/v1/products/` | Public | Paginated product list |
| GET | `/api/v1/products/{id}` | Public | Single product |
| POST | `/api/v1/products/` | Admin | Create product |
| GET | `/api/v1/categories/` | Public | Category tree |
| POST | `/api/v1/orders/` | User | Place order |
| GET | `/api/v1/orders/` | User | My orders |
| PATCH | `/api/v1/orders/{id}/status` | Admin | Update order status |
| POST | `/api/v1/orders/{id}/payment-intent` | User | Create Razorpay intent (via MCP) |
| POST | `/api/v1/orders/{id}/verify-payment` | User | Verify payment (via MCP) |

Full interactive docs: **http://localhost:8000/docs**

---

## Running Migrations

```bash
# Generate a new migration after model changes
docker exec shopwave_backend alembic revision --autogenerate -m "add_product_embedding"

# Apply all pending migrations
docker exec shopwave_backend alembic upgrade head

# Rollback one migration
docker exec shopwave_backend alembic downgrade -1
```

---

## MCP Servers

See [`docs/implementation_sequence_guide.md`](docs/implementation_sequence_guide.md) for the full integration roadmap.

MCP servers are internal-only services (no public ports). They communicate with the FastAPI backend via Docker Compose internal DNS:

| Service | Internal URL | Port |
|---|---|---|
| mcp-inventory | `http://mcp-inventory:8001` | 8001 |
| mcp-payments | `http://mcp-payments:8002` | 8002 |
| mcp-search | `http://mcp-search:8003` | 8003 |
| mcp-notifications | `http://mcp-notifications:8004` | 8004 |
| mcp-analytics | `http://mcp-analytics:8005` | 8005 |
| mcp-content | `http://mcp-content:8006` | 8006 |

---

## Windows PowerShell Generation Command

Regenerate the empty directory/file scaffold on Windows:

```powershell
# Run from the parent directory where you want 'shopwave/' to be created
$dirs = @(
  "shopwave/backend/app/api/v1/endpoints","shopwave/backend/app/core",
  "shopwave/backend/app/db","shopwave/backend/app/models",
  "shopwave/backend/app/schemas","shopwave/backend/app/services",
  "shopwave/backend/app/utils","shopwave/backend/alembic/versions",
  "shopwave/frontend/src/components/layout","shopwave/frontend/src/components/ui",
  "shopwave/frontend/src/components/features","shopwave/frontend/src/pages",
  "shopwave/frontend/src/hooks","shopwave/frontend/src/services",
  "shopwave/frontend/src/store","shopwave/frontend/src/utils",
  "shopwave/frontend/public","shopwave/mcp-servers/inventory/tests",
  "shopwave/mcp-servers/payments","shopwave/mcp-servers/search",
  "shopwave/mcp-servers/notifications","shopwave/mcp-servers/analytics",
  "shopwave/mcp-servers/content","shopwave/nginx","shopwave/docs"
)
$dirs | ForEach-Object { New-Item -ItemType Directory -Force -Path $_ | Out-Null }
Write-Host "ShopWave directory tree created."
```

---

## Development (without Docker)

```bash
# Backend
cd backend
python -m venv .venv && .venv/Scripts/activate   # Windows
pip install -e ".[dev]"
cp .env.example .env                              # fill DATABASE_URL
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
cp .env.example .env.local                        # fill VITE_API_BASE_URL
npm run dev
```

---

## Tech Decisions

| Concern | Choice | Why |
|---|---|---|
| Password hashing | `pwdlib` + Argon2 | Memory-hard; PHC winner; future-proof |
| JWT | `pyjwt` | Lightweight, well-maintained; no extra deps |
| ORM | SQLAlchemy 2.x async | Native async; type-annotated `Mapped[]` columns |
| State management | Zustand + persist | Minimal boilerplate vs Redux; built-in localStorage |
| Server state | TanStack Query v5 | Caching, background refetch, deduplication |
| Search | pgvector + Voyage-3 embeddings | Semantic recall; no extra search infra needed |
| Payments | Razorpay (via MCP) | INR-native; MCP layer makes it swappable |
