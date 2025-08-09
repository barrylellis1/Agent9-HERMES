# PowerShell script to commit all changes in the project
Write-Host "Checking git status..." -ForegroundColor Cyan
git status

# Prompt for confirmation
$confirmation = Read-Host "`nDo you want to git add and commit ALL changes shown above? (y/n)"
if ($confirmation -eq 'y') {
    Write-Host "Adding all files to git..." -ForegroundColor Cyan
    git add .
    
    # Commit the changes
    $commitMessage = "KPI Registry Simplification and MVP Finance Focus Implementation

- Removed KPI definitions from Business Process Registry
- Implemented single source of truth for KPI-to-Business Process mappings
- Updated models and providers to match cleaned structure
- Added validation for registry integrity
- Created test scripts for registry functionality
- Focused MVP scope on Finance KPIs from fi_star_schema.yaml"

    git commit -m $commitMessage
    
    Write-Host "`nChanges committed successfully!" -ForegroundColor Green
    Write-Host "You can now push these changes with 'git push'." -ForegroundColor Cyan
} else {
    Write-Host "Operation canceled. No changes were committed." -ForegroundColor Yellow
}
