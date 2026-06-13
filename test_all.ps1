Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "      POS BACKEND - COMPLETE TEST" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Login
Write-Host "`n[1] Logging in..." -ForegroundColor Yellow
$body = @{email="admin@shop.com"; password="admin123"} | ConvertTo-Json
$response = Invoke-RestMethod -Uri http://localhost:5000/api/auth/login `
    -Method POST -Body $body -ContentType "application/json"
$token = $response.access_token
Write-Host "✅ Login successful!" -ForegroundColor Green

$headers = @{Authorization = "Bearer $token"; 'Content-Type' = 'application/json'}

# Create Product
Write-Host "`n[2] Creating product..." -ForegroundColor Yellow
$productBody = @{
    sku = "PROD001"
    name = "Maziwa Tatu"
    category = "Vyakula"
    cost_price = 1200
    selling_price = 1500
    stock_quantity = 50
    reorder_level = 10
} | ConvertTo-Json

try {
    $product = Invoke-RestMethod -Uri http://localhost:5000/api/products/ `
        -Method POST -Body $productBody -Headers $headers
    Write-Host "✅ Product created: $($product.product.name)" -ForegroundColor Green
} catch { Write-Host "⚠️ Product creation failed" -ForegroundColor Yellow }

# Get Products
Write-Host "`n[3] Getting products..." -ForegroundColor Yellow
$products = Invoke-RestMethod -Uri http://localhost:5000/api/products/ `
    -Method GET -Headers @{Authorization = "Bearer $token"}
Write-Host "✅ Found $($products.total) products" -ForegroundColor Green
$products.products | Format-Table -Property id, sku, name, selling_price, stock_quantity

# Create Customer
Write-Host "`n[4] Creating customer..." -ForegroundColor Yellow
$customerBody = @{
    name = "John Doe"
    phone = "0712345678"
    email = "john@example.com"
    address = "Dar es Salaam"
} | ConvertTo-Json

try {
    $customer = Invoke-RestMethod -Uri http://localhost:5000/api/customers/ `
        -Method POST -Body $customerBody -Headers $headers
    Write-Host "✅ Customer created: $($customer.customer.name)" -ForegroundColor Green
} catch { Write-Host "⚠️ Customer creation failed" -ForegroundColor Yellow }

# Record Sale
Write-Host "`n[5] Recording sale..." -ForegroundColor Yellow
$saleBody = @{
    items = @(@{product_id = 1; quantity = 2})
    payment_method = "cash"
    vat = 0
    discount = 0
} | ConvertTo-Json

try {
    $sale = Invoke-RestMethod -Uri http://localhost:5000/api/sales/ `
        -Method POST -Body $saleBody -Headers $headers
    Write-Host "✅ Sale recorded! Invoice: $($sale.invoice_no)" -ForegroundColor Green
} catch { Write-Host "⚠️ Sale recording failed" -ForegroundColor Yellow }

# Dashboard Report
Write-Host "`n[6] Dashboard report..." -ForegroundColor Yellow
$dashboard = Invoke-RestMethod -Uri http://localhost:5000/api/reports/dashboard `
    -Method GET -Headers @{Authorization = "Bearer $token"}
Write-Host "✅ Today's revenue: $($dashboard.today.revenue)" -ForegroundColor Green
Write-Host "   Today's sales: $($dashboard.today.sales_count)" -ForegroundColor Gray
Write-Host "   Total products: $($dashboard.counts.total_products)" -ForegroundColor Gray
Write-Host "   Total customers: $($dashboard.counts.total_customers)" -ForegroundColor Gray

Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
Write-Host "✅ ALL TESTS COMPLETE!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan