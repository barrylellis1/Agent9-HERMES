# PowerShell script to commit all registry-related changes
Write-Host "Checking modified files..." -ForegroundColor Cyan

# List modified registry files
$modifiedRegistryFiles = @(
    "src/registry_references/business_process_registry/yaml/business_process_registry.yaml",
    "src/registry/models/business_process.py",
    "src/registry/providers/business_process_provider.py",
    "validate_kpi_business_process_mappings.py",
    "test_business_process_registry.py"
)

# Check if files exist
foreach ($file in $modifiedRegistryFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file exists" -ForegroundColor Green
    } else {
        Write-Host "❌ $file does not exist" -ForegroundColor Red
    }
}

# Show a summary of the changes
Write-Host "`nPreparing to commit the following changes:" -ForegroundColor Cyan
Write-Host "1. Removed KPI definitions from Business Process Registry"
Write-Host "2. Updated BusinessProcess model to remove kpis field"
Write-Host "3. Enhanced YAML loader to handle cleaned structure"
Write-Host "4. Added validation scripts for KPI-BP mappings"
Write-Host "5. Created test script for business process registry"

# Prompt for confirmation
$confirmation = Read-Host "`nDo you want to git add and commit these changes? (y/n)"
if ($confirmation -eq 'y') {
    Write-Host "Adding files to git..." -ForegroundColor Cyan
    git add $modifiedRegistryFiles
    
    # Commit the changes
    $commitMessage = "KPI Registry Simplification: Single Source of Truth Implementation
    
- Removed KPI definitions from Business Process Registry
- Preserved owner_role, stakeholder_roles, and other metadata
- Updated model and provider to match cleaned structure
- Added validation for KPI-to-Business Process mappings
- Implemented single source of truth for KPI-BP relationships"

    git commit -m $commitMessage
    
    Write-Host "`nChanges committed successfully!" -ForegroundColor Green
    Write-Host "You can now push these changes to your remote repository." -ForegroundColor Cyan
} else {
    Write-Host "Operation canceled. No changes were committed." -ForegroundColor Yellow
}
