# Fahim Al Efaji — Portfolio · Azure Cosmos DB Edition

Every feature in this portfolio is backed by **Azure Cosmos DB (free tier)** via **Azure Functions (Python)**.

---

## 📁 File Structure

```
portfolio/
├── index.html                          ← Main portfolio page
├── css/style.css                       ← All styles
├── js/
│   ├── main.js                         ← Portfolio JS (contact form → Cosmos DB)
│   └── api.js                          ← Shared Azure API client for all projects
├── projects/
│   ├── ai-assistant.html               ← Chat history  → Cosmos: chat_history
│   ├── sql-playground.html             ← Saved queries → Cosmos: sql_queries
│   ├── kpi-dashboard.html              ← KPI dashboard (static generated data)
│   ├── csv-analyzer.html               ← Analysis meta → Cosmos: csv_uploads
│   └── finance-tracker.html            ← Transactions  → Cosmos: finance_tx
└── azure_function/
    ├── function_app.py                 ← All HTTP endpoints (Python, Azure Functions v2)
    ├── cosmos_client.py                ← Shared Cosmos DB helper / connection pool
    ├── host.json                       ← Azure Functions runtime config
    └── requirements.txt                ← Python packages
```

---

## ☁️ Azure Cosmos DB Schema

One **free-tier Cosmos DB account**, one `portfolio` database, five containers:

| Container       | Partition Key | Stores                               |
|-----------------|---------------|--------------------------------------|
| `contacts`      | `/email`      | Contact form messages                |
| `finance_tx`    | `/userId`     | Finance tracker transactions         |
| `sql_queries`   | `/userId`     | Saved SQL queries                    |
| `csv_uploads`   | `/userId`     | CSV analysis metadata + stats        |
| `chat_history`  | `/sessionId`  | AI assistant chat sessions           |

**Free tier:** 1 000 RU/s + 25 GB — plenty for a portfolio.

---

## 🚀 Full Deployment (5 Steps)

### Step 1 — Install prerequisites
```bash
# Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Azure Functions Core Tools v4
npm install -g azure-functions-core-tools@4 --unsafe-perm true

# Login
az login
```

### Step 2 — Create Azure resources (all free)
```bash
# ── Variables (edit these) ──────────────────────────────────
RESOURCE_GROUP="portfolio-rg"
LOCATION="westeurope"
COSMOS_ACCOUNT="portfolio-cosmos-$(openssl rand -hex 4)"   # globally unique
FUNCTION_APP="portfolio-fn-$(openssl rand -hex 4)"         # globally unique
STORAGE="portfoliosa$(openssl rand -hex 4)"                # lowercase, globally unique
# ────────────────────────────────────────────────────────────

# Resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Cosmos DB — FREE TIER (25 GB + 1000 RU/s, no charge)
az cosmosdb create \
  --name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --locations regionName=$LOCATION \
  --enable-free-tier true \
  --default-consistency-level Session

# Save the connection string
COSMOS_CONN=$(az cosmosdb keys list \
  --name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --type connection-strings \
  --query "connectionStrings[0].connectionString" \
  --output tsv)

echo "==> Cosmos connection string saved to COSMOS_CONN"

# Storage account (Functions dependency — free LRS)
az storage account create \
  --name $STORAGE \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

# Function App — Python 3.11, Consumption plan (1M req/month FREE)
az functionapp create \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --consumption-plan-location $LOCATION \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --storage-account $STORAGE \
  --os-type linux
```

### Step 3 — Configure environment variables
```bash
# Replace with your GitHub Pages URL (or Azure Static Web Apps URL)
PORTFOLIO_URL="https://YOUR-GITHUB-USERNAME.github.io"

az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings \
    "COSMOS_CONNECTION_STRING=$COSMOS_CONN" \
    "COSMOS_DB_NAME=portfolio" \
    "ALLOWED_ORIGIN=$PORTFOLIO_URL"
```

### Step 4 — Deploy the Python Azure Functions
```bash
cd azure_function

# Deploy to Azure
func azure functionapp publish $FUNCTION_APP

# Print your API base URL
echo "Your API base URL:"
echo "https://$FUNCTION_APP.azurewebsites.net/api"
```

### Step 5 — Wire up the frontend
Open each of the files below and replace the empty string with your Function App URL:

**`js/main.js`** — line 8:
```js
const API_BASE = window.PORTFOLIO_API_BASE || 'https://portfolio-fn-xxxx.azurewebsites.net/api';
```

**`projects/finance-tracker.html`**, **`projects/ai-assistant.html`**,  
**`projects/sql-playground.html`**, **`projects/csv-analyzer.html`** — `<head>` tag:
```html
<script>window.PORTFOLIO_API_BASE = 'https://portfolio-fn-xxxx.azurewebsites.net/api';</script>
```

---

## 🌐 Host the Frontend for Free

### GitHub Pages (recommended)
```bash
git init && git add . && git commit -m "Portfolio + Azure Cosmos DB"
git remote add origin https://github.com/YOUR-USERNAME/portfolio.git
git push -u origin main
# → Settings → Pages → Deploy from branch → main
# Live at: https://YOUR-USERNAME.github.io/portfolio
```

### Azure Static Web Apps (free tier, auto HTTPS + CI/CD)
```bash
az staticwebapp create \
  --name portfolio-web \
  --resource-group $RESOURCE_GROUP \
  --source https://github.com/YOUR-USERNAME/portfolio \
  --location "westeurope" \
  --branch main \
  --app-location "/" \
  --output-location "/"
```

---

## 🔌 API Endpoints

| Method | Endpoint | Cosmos Container | Purpose |
|--------|----------|-----------------|---------|
| POST | `/api/contact` | `contacts` | Save contact message |
| GET | `/api/finance` | `finance_tx` | List transactions |
| POST | `/api/finance` | `finance_tx` | Add transaction |
| DELETE | `/api/finance/{id}` | `finance_tx` | Delete transaction |
| POST | `/api/finance/seed` | `finance_tx` | Seed sample data |
| GET | `/api/sql/queries` | `sql_queries` | List saved queries |
| POST | `/api/sql/queries` | `sql_queries` | Save a query |
| DELETE | `/api/sql/queries/{id}` | `sql_queries` | Delete a query |
| GET | `/api/csv` | `csv_uploads` | List analysis history |
| POST | `/api/csv` | `csv_uploads` | Save analysis metadata |
| GET | `/api/chat?session=X` | `chat_history` | Load chat session |
| POST | `/api/chat` | `chat_history` | Append message |
| DELETE | `/api/chat/{session}` | `chat_history` | Clear session |

---

## 💰 Cost Breakdown

| Service | Free Tier Limit | Estimated Use |
|---------|----------------|---------------|
| Azure Cosmos DB | 25 GB + 1 000 RU/s | < 1% |
| Azure Functions | 1 000 000 req/month | < 0.1% |
| Azure Static Web Apps | Unlimited bandwidth | Free |
| GitHub Pages | Unlimited | Free |

**Total monthly cost: $0.00** ✅

---

## 🧪 Test Locally

```bash
cd azure_function

# Install deps
pip install -r requirements.txt --break-system-packages

# Set local env vars
export COSMOS_CONNECTION_STRING="your-cosmos-connection-string"
export COSMOS_DB_NAME="portfolio"
export ALLOWED_ORIGIN="http://localhost:8080"

# Start Functions locally
func start

# Test in another terminal
curl -X POST http://localhost:7071/api/contact \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","message":"Hello from Cosmos!"}'

# Serve the frontend
cd ..
python -m http.server 8080
# → open http://localhost:8080
```

---

## 🔐 Security Notes

- CORS locked to `ALLOWED_ORIGIN` — only your domain can call the API
- User identity = browser session-scoped random ID (no login required)
- Contact messages are private — only visible in Azure Portal / Cosmos Data Explorer
- For production: add Azure API Management or Function-level auth keys
