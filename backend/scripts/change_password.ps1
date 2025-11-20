#scripts/change_password.ps1
param (
    [string]$ip,
    [string]$user,
    [string]$oldpass,
    [string]$newpass
)

try {
    $uri = "http://$ip/ISAPI/Security/users/1"

    $xmlBody = @"
<?xml version="1.0" encoding="UTF-8"?>
<User>
  <id>1</id>
  <userName>$user</userName>
  <password>$newpass</password>
  <userLevel>Administrator</userLevel>
  <enable>true</enable>
</User>
"@

    $cache = New-Object System.Net.NetworkCredential($user, $oldpass)
    $req = [System.Net.HttpWebRequest]::Create($uri)
    $req.Method = "PUT"
    $req.Credentials = $cache
    $req.PreAuthenticate = $true
    $req.ContentType = "application/xml"

    $bytes = [System.Text.Encoding]::UTF8.GetBytes($xmlBody)
    $req.ContentLength = $bytes.Length
    $stream = $req.GetRequestStream()
    $stream.Write($bytes, 0, $bytes.Length)
    $stream.Close()

    $resp = $req.GetResponse()
    $resp.Close()

    Write-Output "Success"
} catch {
    Write-Output "Failed: $_"
}