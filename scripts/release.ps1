[CmdletBinding()]
param(
    [ValidateSet('Validate', 'Draft', 'Publish')]
    [string]$Mode = 'Validate',
    [string]$Python = 'python',
    [switch]$PlanOnly,
    [switch]$Yes,
    [switch]$NoWait
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-NativeCommand {
    param(
        [Parameter(Mandatory)] [string]$FilePath,
        [Parameter(Mandatory)] [string[]]$Arguments,
        [Parameter(Mandatory)] [string]$Description
    )

    Write-Host "`n==> $Description"
    & $FilePath @Arguments | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}

function Get-NativeCommandOutput {
    param(
        [Parameter(Mandatory)] [string]$FilePath,
        [Parameter(Mandatory)] [string[]]$Arguments,
        [Parameter(Mandatory)] [string]$Description
    )

    $output = & $FilePath @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        $diagnostic = ($output | Out-String).Trim()
        throw "$Description failed: $diagnostic"
    }
    return ($output | Out-String).Trim()
}

function Get-ProjectVersion {
    param([Parameter(Mandatory)] [string]$VersionFile)

    $content = Get-Content -LiteralPath $VersionFile -Raw
    $match = [regex]::Match(
        $content,
        '(?m)^__version__\s*=\s*["''](?<version>[^"'']+)["'']\s*$'
    )
    if (-not $match.Success) {
        throw "Could not read __version__ from $VersionFile."
    }
    $version = $match.Groups['version'].Value
    if ($version -notmatch '^\d+\.\d+\.\d+(?:(?:a|b|rc)\d+|(?:\.post|\.dev)\d+)?$') {
        throw "Version '$version' is not a supported release version."
    }
    return $version
}

function Assert-ReleaseCheckout {
    param(
        [Parameter(Mandatory)] [string]$RepositoryRoot,
        [Parameter(Mandatory)] [string]$Tag
    )

    $actualRoot = Get-NativeCommandOutput git @('rev-parse', '--show-toplevel') 'Locating repository root'
    if ([IO.Path]::GetFullPath($actualRoot) -ne [IO.Path]::GetFullPath($RepositoryRoot)) {
        throw "Run the release script from its Skjol repository checkout."
    }

    $changes = Get-NativeCommandOutput git @('status', '--porcelain=v1', '--untracked-files=all') 'Checking worktree'
    if ($changes) {
        throw "The worktree must be clean before creating a release.`n$changes"
    }

    $branch = Get-NativeCommandOutput git @('branch', '--show-current') 'Reading current branch'
    if (-not $branch) {
        throw 'Releases cannot be created from a detached HEAD.'
    }
    & git rev-parse --verify --quiet "refs/tags/$Tag" *> $null
    if ($LASTEXITCODE -eq 0) {
        throw "Tag $Tag already exists. Increment pyobfuscator/_version.py first."
    }
    return $branch
}

function Assert-GitHubReleaseTarget {
    param(
        [Parameter(Mandatory)] [string]$Repository,
        [Parameter(Mandatory)] [string]$Branch,
        [Parameter(Mandatory)] [string]$Tag
    )

    $localCommit = Get-NativeCommandOutput git @('rev-parse', 'HEAD') 'Reading local commit'
    $remoteCommit = Get-NativeCommandOutput gh @(
        'api', "repos/$Repository/commits/$Branch", '--jq', '.sha'
    ) 'Reading the GitHub branch commit'
    if ($localCommit -ne $remoteCommit) {
        throw "Local HEAD $localCommit does not match GitHub $Branch at $remoteCommit. Push or synchronize the branch first."
    }

    $tagRef = "refs/tags/$Tag"
    $matchingTagRefsText = Get-NativeCommandOutput gh @(
        'api',
        "repos/$Repository/git/matching-refs/tags/$Tag",
        '--jq',
        '.[].ref'
    ) "Checking GitHub tag $Tag"
    $matchingTagRefs = $matchingTagRefsText -split '\r?\n'
    if ($matchingTagRefs -contains $tagRef) {
        throw "GitHub tag $Tag already exists. Increment pyobfuscator/_version.py first."
    }
}

function New-ReleaseBuild {
    param(
        [Parameter(Mandatory)] [string]$RepositoryRoot,
        [Parameter(Mandatory)] [string]$Version,
        [Parameter(Mandatory)] [string]$PythonCommand,
        [Parameter(Mandatory)] [string]$TemporaryRoot
    )

    Invoke-NativeCommand $PythonCommand @('-m', 'pytest', '-q') 'Running the complete test suite'

    $sourceArchive = Join-Path $TemporaryRoot 'source.zip'
    $sourceRoot = Join-Path $TemporaryRoot 'source'
    $artifactRoot = Join-Path $TemporaryRoot 'artifacts'
    New-Item -ItemType Directory -Path $sourceRoot, $artifactRoot | Out-Null

    Invoke-NativeCommand git @(
        'archive', '--format=zip', "--output=$sourceArchive", 'HEAD'
    ) 'Exporting the committed release source'
    Expand-Archive -LiteralPath $sourceArchive -DestinationPath $sourceRoot

    Push-Location $sourceRoot
    try {
        Invoke-NativeCommand $PythonCommand @(
            '-m', 'build', '--outdir', $artifactRoot
        ) 'Building wheel and source distribution'
    }
    finally {
        Pop-Location
    }

    $artifacts = @(Get-ChildItem -LiteralPath $artifactRoot -File | Sort-Object Name)
    $expectedNames = @("skjol-$Version-py3-none-any.whl", "skjol-$Version.tar.gz")
    $actualNames = @($artifacts.Name)
    foreach ($expectedName in $expectedNames) {
        if ($expectedName -notin $actualNames) {
            throw "Expected release artifact '$expectedName' was not built. Found: $($actualNames -join ', ')"
        }
    }
    if ($artifacts.Count -ne $expectedNames.Count) {
        throw "Expected exactly two release artifacts. Found: $($actualNames -join ', ')"
    }

    $checkArguments = @('-m', 'twine', 'check') + @($artifacts.FullName)
    Invoke-NativeCommand $PythonCommand $checkArguments 'Validating package metadata'
    Write-Host "`nRelease artifacts:"
    $artifacts | ForEach-Object {
        $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        Write-Host "  $($_.Name)  sha256:$hash"
    }
    return $artifacts
}

function Get-LatestReleaseRunId {
    param(
        [Parameter(Mandatory)] [string]$Branch,
        [Parameter(Mandatory)] [string]$Repository
    )

    return Get-NativeCommandOutput gh @(
        'run', 'list',
        '--repo', $Repository,
        '--workflow', 'release.yml',
        '--branch', $Branch,
        '--event', 'workflow_dispatch',
        '--limit', '1',
        '--json', 'databaseId',
        '--jq', '.[0].databaseId'
    ) 'Finding the latest release workflow run'
}

function Publish-GitHubRelease {
    param(
        [Parameter(Mandatory)] [string]$ReleaseMode,
        [Parameter(Mandatory)] [string]$Version,
        [Parameter(Mandatory)] [string]$Tag,
        [Parameter(Mandatory)] [string]$Branch,
        [Parameter(Mandatory)] [string]$Repository,
        [Parameter(Mandatory)] [bool]$Confirmed,
        [Parameter(Mandatory)] [bool]$WaitForCompletion
    )

    $isDraft = $ReleaseMode -eq 'Draft'
    $releaseKind = if ($isDraft) { 'draft GitHub release' } else { 'public GitHub release' }
    Write-Host "`nReady to create $releaseKind $Tag from $Repository@$Branch."
    if (-not $Confirmed) {
        $expected = "release $Tag"
        $response = Read-Host "Type '$expected' to continue"
        if ($response -ne $expected) {
            throw 'Release cancelled; confirmation text did not match.'
        }
    }

    $previousRun = Get-LatestReleaseRunId $Branch $Repository
    Invoke-NativeCommand gh @(
        'workflow', 'run', 'release.yml',
        '--repo', $Repository,
        '--ref', $Branch,
        '--field', "version=$Version",
        '--field', "draft=$($isDraft.ToString().ToLowerInvariant())"
    ) "Dispatching the $releaseKind workflow"

    $runId = $null
    foreach ($attempt in 1..15) {
        Start-Sleep -Seconds 2
        $candidate = Get-LatestReleaseRunId $Branch $Repository
        if ($candidate -and $candidate -ne $previousRun) {
            $runId = $candidate
            break
        }
    }
    if (-not $runId) {
        throw 'The workflow was dispatched, but its run ID could not be discovered.'
    }

    $runUrl = Get-NativeCommandOutput gh @(
        'run', 'view', $runId, '--repo', $Repository, '--json', 'url', '--jq', '.url'
    ) 'Reading release workflow URL'
    Write-Host "Release workflow: $runUrl"
    if ($WaitForCompletion) {
        Invoke-NativeCommand gh @(
            'run', 'watch', $runId, '--repo', $Repository, '--exit-status'
        ) 'Waiting for the release workflow'
        $releaseUrl = Get-NativeCommandOutput gh @(
            'release', 'view', $Tag, '--repo', $Repository, '--json', 'url', '--jq', '.url'
        ) 'Reading GitHub release URL'
        Write-Host "GitHub release: $releaseUrl"
    }
}

function Remove-ReleaseTemporaryDirectory {
    param([Parameter(Mandatory)] [string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }
    $resolved = (Resolve-Path -LiteralPath $Path).Path
    $temporaryBase = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')
    $leaf = Split-Path -Leaf $resolved
    if (-not $resolved.StartsWith($temporaryBase, [StringComparison]::OrdinalIgnoreCase) -or
        -not $leaf.StartsWith('skjol-release-', [StringComparison]::Ordinal)) {
        throw "Refusing to remove unexpected temporary directory: $resolved"
    }
    Remove-Item -LiteralPath $resolved -Recurse -Force
}

$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$versionFile = Join-Path $repositoryRoot 'pyobfuscator\_version.py'
$version = Get-ProjectVersion $versionFile
$tag = "v$version"

Write-Host "Skjol release plan"
Write-Host "  Version: $version"
Write-Host "  Tag:     $tag"
Write-Host "  Mode:    $Mode"

if ($PlanOnly) {
    if ($Mode -ne 'Validate') {
        throw '-PlanOnly can only be used with -Mode Validate.'
    }
    Write-Host 'Plan only; no tests, build, or GitHub operation was performed.'
    return
}

Get-Command git -ErrorAction Stop | Out-Null
Get-Command $Python -ErrorAction Stop | Out-Null
Get-Command gh -ErrorAction Stop | Out-Null

Push-Location $repositoryRoot
$temporaryRoot = Join-Path ([IO.Path]::GetTempPath()) ("skjol-release-" + [guid]::NewGuid().ToString('N'))
try {
    $branch = Assert-ReleaseCheckout -RepositoryRoot $repositoryRoot -Tag $tag
    Invoke-NativeCommand $Python @('-m', 'build', '--version') 'Checking the build frontend'
    Invoke-NativeCommand $Python @('-m', 'twine', '--version') 'Checking Twine'
    New-Item -ItemType Directory -Path $temporaryRoot | Out-Null
    $artifacts = New-ReleaseBuild $repositoryRoot $version $Python $temporaryRoot

    if ($Mode -eq 'Validate') {
        Write-Host "`nValidation succeeded. No GitHub state was changed."
        Write-Host "Use -Mode Draft or -Mode Publish when the committed checkout is ready."
        return
    }

    Invoke-NativeCommand gh @('auth', 'status') 'Checking GitHub CLI authentication'
    $repository = Get-NativeCommandOutput gh @(
        'repo', 'view', '--json', 'nameWithOwner', '--jq', '.nameWithOwner'
    ) 'Resolving GitHub repository'
    Assert-GitHubReleaseTarget -Repository $repository -Branch $branch -Tag $tag
    Publish-GitHubRelease `
        -ReleaseMode $Mode `
        -Version $version `
        -Tag $tag `
        -Branch $branch `
        -Repository $repository `
        -Confirmed $Yes.IsPresent `
        -WaitForCompletion (-not $NoWait.IsPresent)
}
finally {
    Pop-Location
    Remove-ReleaseTemporaryDirectory $temporaryRoot
}
