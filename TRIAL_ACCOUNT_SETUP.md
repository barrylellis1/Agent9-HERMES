# Phase 10D-B: Trial Account Setup Guide

Complete step-by-step instructions for creating Snowflake and Databricks trial accounts for MCP integration testing.

---

## Part 1: Snowflake Trial Account Setup

### Step 1.1: Create Snowflake Account

1. **Go to:** https://signup.snowflake.com/
2. **Fill in the form:**
   - Email: (your email)
   - Password: (strong password)
   - First Name / Last Name: (your name)
   - Company: (Agent9-HERMES or your name)
   - Country: United States (or your location)

3. **Choose edition and region:**
   - Edition: **Standard** (sufficient for testing, cheaper)
   - Cloud Provider: **AWS** (best MCP availability)
   - Region: **us-east-1** (good default)
   - Click "Get Started"

4. **Verify email:** Check your email for verification link, click it

5. **Set up account:**
   - Create new Snowflake account name (e.g., `agent9test`)
   - You'll get redirected to Snowflake console

**Save these details:**
```
Account Name: [e.g., agent9test]
Account URL: [e.g., https://xy12345.us-east-1.snowflake.app]
Admin User: [usually ACCOUNTADMIN]
Admin Password: [what you set]
Email: [your email]
```

---

### Step 1.2: Create Admin User for Testing

After initial setup, log in with ACCOUNTADMIN role:

1. **In Snowflake console**, go to **Admin → Users**
2. **Click "+ User"** to create new user:
   - Username: `mcp_test_user`
   - Password: (strong password)
   - Email: (your email)
   - Default Role: ACCOUNTADMIN (for testing, simplifies permissions)
   - Default Warehouse: (create new or use default_wh)

3. **Click "Create User"**

**Save these details:**
```
Username: mcp_test_user
Password: [what you set]
Role: ACCOUNTADMIN
```

---

### Step 1.3: Enable MCP and Get Credentials

**Important:** Snowflake MCP is in public preview as of 2026. Availability depends on your region and edition.

#### Option A: Snowflake Managed MCP (Preferred)

1. **Check MCP availability:**
   - In Snowflake console, go to **Admin → Integrations**
   - Look for "Model Context Protocol" or "MCP Server"
   - If available, click to enable

2. **If MCP is available:**
   - Click "Create MCP Integration" or similar
   - Select authentication type: **OAuth 2.0** or **Service Account**
   - For testing, use **OAuth 2.0**
   - Generate credentials
   - You'll get:
     - `MCP_ENDPOINT`: (provided by Snowflake)
     - `MCP_AUTH_TOKEN`: (OAuth token)

3. **If MCP is NOT yet available in your region:**
   - Try switching region in account dropdown (top-right)
   - Or request early access: Contact Snowflake support

#### Option B: Fallback - Use REST API

If MCP not available, you can use Snowflake REST API:
- Endpoint: `https://YOUR_ACCOUNT.snowflakecomputing.com/api/v2/`
- Auth: Bearer token from OAuth or API key

**For now, assume MCP is available and proceed with that.**

---

### Step 1.4: Test Snowflake Connection

1. **Create a simple test database:**
   ```sql
   CREATE DATABASE IF NOT EXISTS test_db;
   CREATE SCHEMA IF NOT EXISTS test_db.public;
   CREATE TABLE test_db.public.sample_data (id INT, name VARCHAR);
   INSERT INTO test_db.public.sample_data VALUES (1, 'Test');
   ```

2. **Verify credentials work:**
   ```bash
   # Save credentials to .env.local (never commit to git)
   echo 'SNOWFLAKE_MCP_ENDPOINT=https://your-endpoint' > .env.local
   echo 'SNOWFLAKE_MCP_TOKEN=your-token' >> .env.local
   echo 'SNOWFLAKE_MCP_AUTH=bearer' >> .env.local
   ```

3. **Test with Python:**
   ```bash
   source .env.local
   python3 << 'EOF'
   import os
   import asyncio
   from src.database.mcp_client import MCPClient
   
   async def test():
       client = MCPClient(
           endpoint=os.getenv('SNOWFLAKE_MCP_ENDPOINT'),
           auth_token=os.getenv('SNOWFLAKE_MCP_TOKEN'),
           auth_type='bearer'
       )
       tools = await client.list_tools()
       print(f"Available tools: {tools}")
       await client.close()
   
   asyncio.run(test())
   EOF
   ```

   **Expected output:** List of available MCP tools (e.g., `sql_execute`, etc.)

---

## Part 2: Databricks Trial Account Setup

### Step 2.1: Create Databricks Workspace

1. **Go to:** https://databricks.com/try-databricks (free trial link)
2. **Or sign up:** https://accounts.cloud.databricks.com/
3. **Fill in the form:**
   - Email: (your email)
   - Password: (strong password)
   - First/Last Name: (your name)
   - Company: (Agent9-HERMES or your name)

4. **Choose workspace setup:**
   - Cloud: **AWS** (or Azure/GCP, but AWS is most stable)
   - Region: **us-east-1** or **us-west-2**
   - Workspace name: `agent9-test`
   - Click "Create Workspace"

5. **Wait for workspace to initialize** (2-5 minutes)

6. **You'll get:**
   - Workspace URL: `https://adb-XXXXXXXX.azurewebsites.net` (Azure) or similar
   - Login credentials

**Save these details:**
```
Workspace URL: [your workspace URL]
Email: [your email]
Password: [what you set]
```

---

### Step 2.2: Create Personal Access Token (PAT)

1. **In Databricks workspace**, click **Settings** (bottom-left)
2. **Click "Developer"** → **"Personal access tokens"**
3. **Click "Generate new token":**
   - Comment: `mcp_integration_test`
   - Lifetime: 90 days (or max)
   - Click "Generate"

4. **IMPORTANT: Copy the token immediately** (you can only see it once!)
   ```
   dapi123456789abcdefghijk...
   ```

5. **Store it safely** (we'll use it in .env.local):
   ```bash
   echo 'DATABRICKS_MCP_TOKEN=dapi123456789...' >> .env.local
   echo 'DATABRICKS_MCP_ENDPOINT=https://your-workspace-url/api/2.0/mcp' >> .env.local
   echo 'DATABRICKS_MCP_AUTH=pat' >> .env.local
   ```

**Save these details:**
```
PAT Token: dapi... (KEEP SECURE!)
Token Type: Personal Access Token
Workspace URL: [from above]
```

---

### Step 2.3: Enable MCP Support

1. **In workspace settings**, look for:**
   - **Admin Settings** → **Networking** or **API**
   - Check if MCP is enabled (should be by default in 2026)

2. **Create a test catalog/schema:**
   - Click **Catalog** (left sidebar)
   - Click **Create Catalog**
   - Name: `test_catalog`
   - Click **Create**
   
3. **Create test schema:**
   - Click **Create Schema**
   - Name: `public`
   - Location: (default)
   - Click **Create**

4. **Create test table (optional, for later testing):**
   - Use SQL notebook to create:
   ```sql
   CREATE TABLE test_catalog.public.sample_data (
     id INT,
     name STRING
   );
   INSERT INTO test_catalog.public.sample_data VALUES (1, 'Test');
   ```

---

### Step 2.4: Test Databricks Connection

1. **Verify credentials work:**
   ```bash
   source .env.local
   python3 << 'EOF'
   import os
   import asyncio
   from src.database.mcp_client import MCPClient
   
   async def test():
       client = MCPClient(
           endpoint=os.getenv('DATABRICKS_MCP_ENDPOINT'),
           auth_token=os.getenv('DATABRICKS_MCP_TOKEN'),
           auth_type='pat'
       )
       tools = await client.list_tools()
       print(f"Available tools: {tools}")
       await client.close()
   
   asyncio.run(test())
   EOF
   ```

   **Expected output:** List of available MCP tools

---

## Part 3: Secure Credential Management

### ⚠️ IMPORTANT: Never Commit Credentials to Git

1. **Create `.env.local` file** (NOT in git):
   ```bash
   cat > .env.local << 'EOF'
   # Snowflake MCP
   SNOWFLAKE_MCP_ENDPOINT=https://your-snowflake-endpoint
   SNOWFLAKE_MCP_TOKEN=your-snowflake-token
   SNOWFLAKE_MCP_AUTH=bearer

   # Databricks MCP
   DATABRICKS_MCP_ENDPOINT=https://your-databricks-workspace/api/2.0/mcp
   DATABRICKS_MCP_TOKEN=dapi...your-pat-token...
   DATABRICKS_MCP_AUTH=pat
   EOF
   
   # Add to .gitignore if not already there
   echo ".env.local" >> .gitignore
   git add .gitignore && git commit -m "Add .env.local to gitignore"
   ```

2. **Load credentials when testing:**
   ```bash
   source .env.local
   pytest tests/unit/test_phase_10d_mcp.py -v
   ```

3. **For production/CI/CD:**
   - Use environment variables or secrets manager
   - Never hardcode credentials in code

---

## Part 4: Verification Checklist

### Snowflake ✅

- [ ] Trial account created and verified
- [ ] MCP endpoint obtained
- [ ] Auth token obtained
- [ ] Test user created with ACCOUNTADMIN role
- [ ] Test database and table created
- [ ] `.env.local` has `SNOWFLAKE_MCP_*` variables
- [ ] Python script successfully lists MCP tools
- [ ] Credentials saved in secure location

### Databricks ✅

- [ ] Trial workspace created
- [ ] Personal Access Token (PAT) generated
- [ ] PAT stored securely (NOT in code)
- [ ] Test catalog and schema created
- [ ] `.env.local` has `DATABRICKS_MCP_*` variables
- [ ] Python script successfully lists MCP tools
- [ ] Credentials saved in secure location

---

## Part 5: Running Integration Tests

Once both accounts are set up and verified:

```bash
# Load credentials
source .env.local

# Run all Phase 10D MCP tests
pytest tests/unit/test_phase_10d_mcp.py -v --timeout=15

# Run Snowflake tests only
pytest tests/unit/test_phase_10d_mcp.py -k snowflake -v --timeout=15

# Run Databricks tests only
pytest tests/unit/test_phase_10d_mcp.py -k databricks -v --timeout=15

# Run integration tests (when ready)
MCP_INTEGRATION_TESTS=true pytest tests/unit/test_phase_10d_mcp.py::TestMCPIntegration -v
```

---

## Troubleshooting

### Snowflake Issues

**Issue:** MCP endpoint not available
- **Solution:** Check your region and edition; MCP is public preview in limited regions
- **Fallback:** Use REST API instead (contact Snowflake support)

**Issue:** Auth token invalid
- **Solution:** Regenerate OAuth token in Snowflake console
- **Check:** Token hasn't expired

**Issue:** "Tool not found" error
- **Solution:** Tool names may differ in your version
- **Action:** Document actual tool names and update `VENDOR_TOOL_MAPS`

### Databricks Issues

**Issue:** PAT token not working
- **Solution:** Regenerate new PAT (old one may be invalid)
- **Check:** Token hasn't been revoked

**Issue:** MCP endpoint 404
- **Solution:** Verify workspace URL is correct
- **Format:** Should be `https://WORKSPACE_URL/api/2.0/mcp`

**Issue:** "Workspace not authorized for MCP"
- **Solution:** Contact Databricks support to enable MCP on workspace
- **Check:** Admin settings → Networking/API

---

## Cost Considerations

### Snowflake
- **Trial:** 30 days free credit (~$400)
- **Standard edition:** $4/credit (on-demand)
- **Testing costs:** Minimal (schema discovery queries are cheap)
- **Estimated for Phase 10D-B:** < $5

### Databricks
- **Trial:** $50-100 free credit
- **All-Purpose cluster:** $0.40-0.50/DBU/hour
- **Testing costs:** Minimal (small cluster, simple queries)
- **Estimated for Phase 10D-B:** < $5

**Total estimated cost for both trials:** < $20 (very cheap!)

---

## Next Steps After Setup

1. ✅ Create both trial accounts (this guide)
2. ✅ Verify credentials work (Python test script above)
3. 🔄 Run Phase 10D-B integration tests
4. 📋 Document actual tool names and result formats
5. 🔧 Fix implementation if needed (update VENDOR_TOOL_MAPS)
6. ✨ Move to Phase 10D-C (Admin Console UI)

---

## Support Resources

- **Snowflake:** https://docs.snowflake.com/
- **Snowflake MCP:** https://github.com/Snowflake-Labs/mcp
- **Databricks:** https://docs.databricks.com/
- **Databricks MCP:** https://docs.databricks.com/aws/en/generative-ai/mcp/

---

**Ready to proceed? Follow the steps above and report back with:**
1. Successfully created accounts
2. Credentials saved in `.env.local`
3. Python test scripts returning tool lists
