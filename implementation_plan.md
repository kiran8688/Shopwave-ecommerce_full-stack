# Project: ShopWave MCP Integration & Deployment Strategy

This plan outlines the steps to fully integrate the Model Context Protocol (MCP) servers into the ShopWave platform, as requested. It follows the architectural blueprint established in the project's documentation and adds a premium deployment and CI/CD strategy.

## Goal
- **Codebase Analysis**: Deep dive into current backend/frontend/MCP state.
- **Segment Analysis**: Align with the roadmap in `implementation_sequence_guide.md`.
- **MCP Implementation**: Complete the logic for all 6 MCP servers and their client integration in FastAPI.
- **Deployment & CI/CD**: Recommended services (Neon, Railway, etc.) and a dedicated documentation file.

## User Review Required
> [!IMPORTANT]
> The implementation of `mcp-search` requires an `ANTHROPIC_API_KEY` for vector embeddings (Voyage-3). 
> The `mcp-payments` server requires `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`.
> The `mcp-notifications` server requires `SENDGRID_API_KEY`.
> Please ensure these are available in your environment or Doppler/Secret Manager.

## Proposed Changes

### 1. Model Context Protocol (MCP) Layer
We will complete the implementation of the 6 specialized MCP services.

#### [MODIFY] [Inventory Server](file:///d:/sskr/Admin%20personal/Projects/shopwave-ecommerce/ecommerce/mcp-servers/inventory/server.py)
- Ensure all tools (`check_stock_levels`, `suggest_reorder`, `bulk_update_stock`) are fully implemented as per the roadmap.

#### [MODIFY] [Payments Server](file:///d:/sskr/Admin%20personal/Projects/shopwave-ecommerce/ecommerce/mcp-servers/payments/server.py)
- Implement `create_payment_intent`, `verify_payment`, and `process_refund`.
- Isolation of Razorpay logic here makes the main API "gateway agnostic".

#### [MODIFY] [Search Server](file:///d:/sskr/Admin%20personal/Projects/shopwave-ecommerce/ecommerce/mcp-servers/search/server.py)
- Implement `semantic_search` using `pgvector` and Anthropic's `voyage-3` embeddings.

#### [NEW] [Notifications Server](file:///d:/sskr/Admin%20personal/Projects/shopwave-ecommerce/ecommerce/mcp-servers/notifications/server.py)
- Implement SendGrid integration for order receipts and shipping updates.

#### [NEW] [Analytics Server](file:///d:/sskr/Admin%20personal/Projects/shopwave-ecommerce/ecommerce/mcp-servers/analytics/server.py)
- Implement BI tools: `get_sales_summary`, `get_top_products`, and `detect_anomalies`.

#### [NEW] [Content Server](file:///d:/sskr/Admin%20personal/Projects/shopwave-ecommerce/ecommerce/mcp-servers/content/server.py)
- Implement AI product description and SEO metadata generation using Claude 3.5 Sonnet.

---

### 2. Backend Integration (FastAPI)
The backend acts as the MCP client, delegating complex or AI-heavy tasks to the specialized servers.

#### [MODIFY] [Orders Endpoint](file:///d:/sskr/Admin%20personal/Projects/shopwave-ecommerce/ecommerce/backend/app/api/v1/endpoints/orders.py)
- Integrate `payments_mcp` for payment intent creation and signature verification.
- Integrate `notify_mcp` for transactional emails.

#### [MODIFY] [Products Endpoint](file:///d:/sskr/Admin%20personal/Projects/shopwave-ecommerce/ecommerce/backend/app/api/v1/endpoints/products.py)
- Add `/search/semantic` endpoint using `search_mcp`.
- Add `/reorder-suggestion` admin endpoint using `inventory_mcp`.

---

### 3. Deployment & CI/CD Documentation
We will provide a high-end HTML dashboard for tracking deployment status and CI/CD pipelines.

#### [NEW] [deployment_and_cicd.html](file:///d:/sskr/Admin%20personal/Projects/shopwave-ecommerce/ecommerce/docs/deployment_and_cicd.html)
- A standalone, premium UI showing the recommended stack:
    - **Database**: [Neon](https://neon.tech) (Serverless Postgres with branching).
    - **Backends/MCPs**: [Railway](https://railway.app) or [Render](https://render.com) (Container hosting).
    - **Frontend**: [Vercel](https://vercel.com) or [Netlify](https://netlify.com) for optimized React deployments.
    - **CI/CD**: [GitHub Actions](https://github.com/features/actions) with full YAML examples.

## Verification Plan

### Automated Tests
- Each MCP server will have a `tests/` directory with `pytest` scripts.
- Example: `pytest mcp-servers/inventory/tests/test_tools.py`

### Manual Verification
- Use `docker compose up` to spin up the full stack.
- Use the Swagger UI (`/docs`) to test the new integrated endpoints.
- Verify MCP server logs to ensure tool calls are being received and processed correctly.
