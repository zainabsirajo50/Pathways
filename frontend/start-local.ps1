# Uses installed Node/pnpm, or the existing Codex runtime on this computer.
# Does not install global software or alter the user's permanent PATH.
$ErrorActionPreference = 'Stop'
$frontendDirectory = $PSScriptRoot
$pnpmCommand = Get-Command pnpm -ErrorAction SilentlyContinue
if ($pnpmCommand) {
    $packageManager = $pnpmCommand.Source
} else {
    $runtimeDirectory = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies'
    $packageManager = Join-Path $runtimeDirectory 'bin\fallback\pnpm.cmd'
    $nodeDirectory = Join-Path $runtimeDirectory 'node\bin'
    if (-not (Test-Path -LiteralPath $packageManager) -or -not (Test-Path -LiteralPath (Join-Path $nodeDirectory 'node.exe'))) {
        throw 'Node.js and pnpm are required. See the frontend setup section in README.md.'
    }
    $env:PATH = $nodeDirectory + [IO.Path]::PathSeparator + $env:PATH
}
Push-Location -LiteralPath $frontendDirectory
try {
    & $packageManager install --frozen-lockfile
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
    & $packageManager dev
    if ($LASTEXITCODE -ne 0) { throw 'Frontend server exited with an error.' }
} finally {
    Pop-Location
}
