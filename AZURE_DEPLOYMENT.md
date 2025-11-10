# Azure Deployment Configuration

## Prerequisites

- Azure subscription
- Azure CLI installed and authenticated
- OpenAI API key stored in Azure Key Vault

## Resources Needed

### 1. Resource Group
```bash
az group create --name rg-cash-forecast --location eastus
```

### 2. App Service Plan
```bash
az appservice plan create \
  --name plan-cash-forecast \
  --resource-group rg-cash-forecast \
  --sku B1 \
  --is-linux
```

### 3. Web App
```bash
az webapp create \
  --name cash-forecast-analyzer \
  --resource-group rg-cash-forecast \
  --plan plan-cash-forecast \
  --runtime "PYTHON:3.11"
```

### 4. Storage Account (for file uploads)
```bash
az storage account create \
  --name stcashforecast \
  --resource-group rg-cash-forecast \
  --location eastus \
  --sku Standard_LRS
```

### 5. Key Vault (for secrets)
```bash
az keyvault create \
  --name kv-cash-forecast \
  --resource-group rg-cash-forecast \
  --location eastus
```

### 6. Store OpenAI API Key in Key Vault
```bash
az keyvault secret set \
  --vault-name kv-cash-forecast \
  --name "openai-api-key" \
  --value "your-openai-api-key"
```

## Configuration

### Application Settings
```bash
az webapp config appsettings set \
  --name cash-forecast-analyzer \
  --resource-group rg-cash-forecast \
  --settings \
    OPENAI_MODEL="gpt-4o-mini" \
    FLASK_ENV="production" \
    AZURE_KEY_VAULT_URL="https://kv-cash-forecast.vault.azure.net/"
```

### Enable Managed Identity
```bash
az webapp identity assign \
  --name cash-forecast-analyzer \
  --resource-group rg-cash-forecast
```

### Grant Key Vault Access
```bash
# Get the app's managed identity principal ID
PRINCIPAL_ID=$(az webapp identity show \
  --name cash-forecast-analyzer \
  --resource-group rg-cash-forecast \
  --query principalId -o tsv)

# Grant access to Key Vault
az keyvault set-policy \
  --name kv-cash-forecast \
  --object-id $PRINCIPAL_ID \
  --secret-permissions get list
```

## Deployment

### Option 1: Deploy from Local (Quick Test)
```bash
# Package the app
cd cash-forecast-analyzer
zip -r deploy.zip . -x "venv/*" "uploads/*" ".git/*" ".env"

# Deploy
az webapp deployment source config-zip \
  --name cash-forecast-analyzer \
  --resource-group rg-cash-forecast \
  --src deploy.zip
```

### Option 2: Deploy from GitHub (Recommended)
```bash
az webapp deployment source config \
  --name cash-forecast-analyzer \
  --resource-group rg-cash-forecast \
  --repo-url https://github.com/your-repo/cash-forecast-analyzer \
  --branch main \
  --manual-integration
```

### Option 3: Deploy using GitHub Actions (Best for CI/CD)

Create `.github/workflows/azure-deploy.yml`:

```yaml
name: Deploy to Azure

on:
  push:
    branches: [ main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Deploy to Azure Web App
      uses: azure/webapps-deploy@v2
      with:
        app-name: 'cash-forecast-analyzer'
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
```

## Production Considerations

### 1. Environment Variables
Update app code to read from Key Vault in production:

```python
# Add to app.py for production
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

def get_secret(secret_name):
    if os.environ.get('FLASK_ENV') == 'production':
        kv_url = os.environ.get('AZURE_KEY_VAULT_URL')
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=kv_url, credential=credential)
        return client.get_secret(secret_name).value
    else:
        return os.environ.get(secret_name)

# Use it:
OPENAI_API_KEY = get_secret('openai-api-key')
```

### 2. File Storage
For production, use Azure Blob Storage instead of local file system:

```python
from azure.storage.blob import BlobServiceClient

# Upload files to blob storage
blob_service = BlobServiceClient.from_connection_string(
    os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
)
```

### 3. Logging
Configure Azure Application Insights:

```bash
az monitor app-insights component create \
  --app cash-forecast-insights \
  --location eastus \
  --resource-group rg-cash-forecast
```

### 4. Scaling
For handling multiple concurrent analyses:

```bash
az appservice plan update \
  --name plan-cash-forecast \
  --resource-group rg-cash-forecast \
  --sku P1V2  # Premium tier for auto-scaling
```

### 5. Custom Domain (Optional)
```bash
az webapp config hostname add \
  --webapp-name cash-forecast-analyzer \
  --resource-group rg-cash-forecast \
  --hostname forecast.yourdomain.com
```

## Cost Estimates (East US, as of 2025)

- **App Service Plan (B1)**: ~$13/month
- **Storage Account (Standard LRS)**: ~$0.02/GB + transactions
- **Key Vault**: $0.03/10k operations (minimal)
- **Application Insights**: First 5GB free, then $2.30/GB

**Total**: ~$15-20/month for basic deployment

For 100 properties with ~25 analyses per month:
- Storage: ~$5/month (for uploaded files)
- OpenAI API: Depends on usage (gpt-4o-mini is very cost-effective)

## Monitoring

View logs:
```bash
az webapp log tail \
  --name cash-forecast-analyzer \
  --resource-group rg-cash-forecast
```

Check app health:
```bash
curl https://cash-forecast-analyzer.azurewebsites.net/health
```

## Security Checklist

- [ ] OpenAI API key stored in Key Vault
- [ ] Managed Identity enabled for Web App
- [ ] HTTPS enforced (automatic with Azure Web Apps)
- [ ] File upload size limits configured
- [ ] Input validation on all uploads
- [ ] Regular dependency updates (pip-audit)

## Troubleshooting

### App won't start
- Check logs: `az webapp log tail`
- Verify Python version: Should be 3.11
- Check startup command in Azure Portal

### Can't access Key Vault
- Verify Managed Identity is assigned
- Check Key Vault access policies
- Ensure correct Key Vault URL in settings

### File uploads failing
- Check App Service Plan has enough disk space
- Verify WEBSITE_MAX_DYNAMIC_APPLICATION_SCALE_OUT setting
- Consider moving to Blob Storage for large files

---

**Note**: This is a template. Adjust resource names, SKUs, and configurations based on your specific needs and existing Azure infrastructure.
