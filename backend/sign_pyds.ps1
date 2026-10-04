$cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=LocalCodeSigning" -CertStoreLocation "Cert:\CurrentUser\My"
Set-AuthenticodeSignature -Certificate $cert -FilePath "backend\venv\Lib\site-packages\sklearn\tree\_utils.cp314-win_amd64.pyd"
Set-AuthenticodeSignature -Certificate $cert -FilePath "backend\venv\Lib\site-packages\sklearn\cluster\_k_means_common.cp314-win_amd64.pyd"
Write-Host "Cert Subject:" $cert.Subject
Write-Host "Cert Thumbprint:" $cert.Thumbprint
