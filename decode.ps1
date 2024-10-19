param(
    [string]$sourceFile,
    [string]$destinationFile
)

$lines = Get-Content $sourceFile
$hexString = ($lines[2..$lines.Length] -join '' -replace '\s+', '')
$byteList = New-Object System.Collections.Generic.List[byte]

for ($i = 0; $i -lt $hexString.Length; $i += 2) {
    if ($i + 1 -lt $hexString.Length) {
        $byte = [Convert]::ToByte($hexString.Substring($i, 2), 16)
        $byteList.Add($byte)
    } 
}


[System.IO.File]::WriteAllBytes($destinationFile, $byteList.ToArray())
