$cert = New-SelfSignedCertificate `
    -Subject "CN=IncentiveHouse ERP" `
    -FriendlyName "IHE-ERP Development Cert" `
    -CertStoreLocation "Cert:\LocalMachine\My" `
    -KeyUsage DigitalSignature,KeyEncipherment `
    -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.1")

$pwd = ConvertTo-SecureString -String "ihe-erp-dev" -Force -AsPlainText

$certPath = Join-Path $PSScriptRoot "..\certs"
New-Item -ItemType Directory -Path $certPath -Force | Out-Null

Export-PfxCertificate -Cert $cert -FilePath (Join-Path $certPath "ihe-erp.pfx") -Password $pwd
openssl pkcs12 -in (Join-Path $certPath "ihe-erp.pfx") -out (Join-Path $certPath "ihe-erp.crt") -nodes -password pass:ihe-erp-dev
openssl pkcs12 -in (Join-Path $certPath "ihe-erp.pfx") -out (Join-Path $certPath "ihe-erp.key") -nocerts -nodes -password pass:ihe-erp-dev

Write-Host "Certs generated in: $certPath"
Write-Host "  - ihe-erp.crt (SSL cert)"
Write-Host "  - ihe-erp.key (SSL key)"
