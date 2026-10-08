<#
 Registers the ST tools as External Tools in TwinCAT XAE (TcXaeShell).
 Run with XAE closed:   powershell -ExecutionPolicy Bypass -File Install_XAE_Tools.ps1
 Options: -Python <path\to\python.exe>   -Uninstall
 Existing External Tools of the user are kept; ST entries are replaced on re-run.
#>
param([string]$Python = "", [switch]$Uninstall)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$key  = "HKCU:\Software\Beckhoff\TcXaeShell\15.0_IsoShell\External Tools"
$tag  = "ST:"                     # marker in the title to recognise our entries

if (Get-Process TcXaeShell -ErrorAction SilentlyContinue) {
    throw "Close TwinCAT XAE first (it overwrites the settings on exit)."
}

# --- read existing tools -------------------------------------------------
$tools = @()
if (Test-Path $key) {
    $p = Get-ItemProperty $key
    for ($i = 0; $i -lt [int]$p.ToolNumKeys; $i++) {   # XAE numbers its tools from 0
        $tools += [pscustomobject]@{
            Title = $p."ToolTitle$i"; Cmd = $p."ToolCmd$i"; Arg = $p."ToolArg$i"
            Dir = $p."ToolDir$i"; Opt = $p."ToolOpt$i"; Src = $p."ToolSourceKey$i" }
    }
    $tools = @($tools | Where-Object { $_.Title -notlike "*$tag*" })
}

if (-not $Uninstall) {
    if (-not $Python) {
        $Python = (& where.exe python.exe 2>$null |
                   Where-Object { $_ -notlike "*WindowsApps*" } | Select-Object -First 1)
    }
    if (-not $Python -or -not (Test-Path $Python)) { throw "python.exe not found - pass -Python <path>." }

    $dest = Join-Path $env:LOCALAPPDATA "STTools"
    New-Item -ItemType Directory -Force $dest | Out-Null
    $core = Join-Path $here "StructuredText_Format.py"
    if (-not (Test-Path $core)) { $core = Join-Path $here "..\src\StructuredText_Format.py" }   # repo layout
    Copy-Item (Join-Path $here "st_twincat.py"), $core $dest -Force
    $py = Join-Path $dest "st_twincat.py"

    # Opt 2 = "Use Output window"
    $tools += [pscustomobject]@{ Title = "$tag Format current &object"; Cmd = $Python
        Arg = "`"$py`" `"`$(ItemPath)`""; Dir = "`$(ItemDir)"; Opt = 2; Src = "" }
    $tools += [pscustomobject]@{ Title = "$tag Format &solution"; Cmd = $Python
        Arg = "`"$py`" `"`$(SolutionDir)`""; Dir = "`$(SolutionDir)"; Opt = 2; Src = "" }
    $tools += [pscustomobject]@{ Title = "$tag Check &names"; Cmd = $Python
        Arg = "`"$py`" --check `"`$(SolutionDir)`""; Dir = "`$(SolutionDir)"; Opt = 2; Src = "" }
}

# --- write back -----------------------------------------------------------
New-Item -Path $key -Force | Out-Null
Get-Item $key | Select-Object -ExpandProperty Property | ForEach-Object { Remove-ItemProperty $key $_ }
Set-ItemProperty $key ToolNumKeys ([int]$tools.Count) -Type DWord
$i = -1
foreach ($t in $tools) {
    $i++
    Set-ItemProperty $key "ToolTitle$i"     $t.Title -Type String
    Set-ItemProperty $key "ToolCmd$i"       $t.Cmd   -Type String
    Set-ItemProperty $key "ToolArg$i"       $t.Arg   -Type String
    Set-ItemProperty $key "ToolDir$i"       $t.Dir   -Type String
    Set-ItemProperty $key "ToolOpt$i"       ([int]$t.Opt) -Type DWord
    Set-ItemProperty $key "ToolSourceKey$i" ([string]$t.Src) -Type String
}
if ($Uninstall) { "ST tools removed from XAE." } else { "Installed $($tools.Count) External Tools; files in $dest. Start XAE -> Tools menu." }
