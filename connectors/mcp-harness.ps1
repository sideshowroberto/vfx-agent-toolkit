# connectors/mcp-harness.ps1
# Shared helper for the connector scripts. Every connector accepts
# -Harness claude|opencode|qwen|none (and -NoRegister as shorthand for
# -Harness none). "claude" is the default and runs "claude mcp add" as
# before. Any other value skips Claude Code entirely and prints the
# resolved MCP server definition (command + absolute args, env, or URL)
# so it can be pasted into the other harness's config file:
#
#   opencode : opencode.json  (project root, or ~\.config\opencode\opencode.json)
#   qwen     : ~\.qwen\settings.json  ("mcpServers" block)
#   none     : plain command line + args, for any other MCP client
#
# Dot-source from a connector script, then call Write-McpServerConfig:
#
#   . (Join-Path $PSScriptRoot "..\mcp-harness.ps1")
#   Write-McpServerConfig -Harness $Harness -Name nuke -Command node -Arguments @($serverScript)
#   Write-McpServerConfig -Harness $Harness -Name magnific -Url "https://mcp.magnific.com"
#
# Works under Windows PowerShell 5.1 and PowerShell 7. ASCII only.

function ConvertTo-McpJsonString {
    # Minimal JSON string encoder. Used instead of ConvertTo-Json so the
    # output is identical on PowerShell 5.1 and 7 (5.1 escapes some
    # characters as \uXXXX and formats arrays one item per line).
    param([string]$Value)
    $s = $Value.Replace('\', '\\').Replace('"', '\"')
    $s = $s.Replace("`r", '\r').Replace("`n", '\n').Replace("`t", '\t')
    $sb = New-Object System.Text.StringBuilder
    foreach ($ch in $s.ToCharArray()) {
        if ([int]$ch -lt 32) {
            [void]$sb.Append(('\u{0:x4}' -f [int]$ch))
        } else {
            [void]$sb.Append($ch)
        }
    }
    return '"' + $sb.ToString() + '"'
}

function ConvertTo-McpJsonArray {
    param([string[]]$Values)
    $parts = @()
    foreach ($v in $Values) { $parts += (ConvertTo-McpJsonString $v) }
    return "[" + ($parts -join ", ") + "]"
}

function ConvertTo-McpJsonObject {
    # Renders a flat string->string hashtable as a JSON object body with
    # the given indent applied to each member line.
    param([hashtable]$Table, [string]$Indent)
    $lines = @()
    foreach ($key in ($Table.Keys | Sort-Object)) {
        $lines += ($Indent + (ConvertTo-McpJsonString $key) + ": " + (ConvertTo-McpJsonString ([string]$Table[$key])))
    }
    return ($lines -join ",`n")
}

function Format-McpCommandLine {
    # Human-readable command line; quotes any arg containing whitespace.
    param([string]$Command, [string[]]$Arguments)
    $parts = @($Command) + $Arguments
    $quoted = foreach ($p in $parts) {
        if ($p -match '\s') { '"' + $p + '"' } else { $p }
    }
    return ($quoted -join " ")
}

function Write-McpServerConfig {
    param(
        [Parameter(Mandatory = $true)][string]$Harness,
        [Parameter(Mandatory = $true)][string]$Name,
        [string]$Command = "",
        [string[]]$Arguments = @(),
        [hashtable]$Environment = @{},
        [string]$Url = ""
    )

    $isHttp = -not [string]::IsNullOrEmpty($Url)

    Write-Host ""
    Write-Host "=== MCP server '$Name' - NOT registered (Harness: $Harness) ===" -ForegroundColor Yellow

    if ($isHttp) {
        Write-Host "Resolved server:" -ForegroundColor White
        Write-Host "  transport : http"
        Write-Host "  url       : $Url"
    } else {
        Write-Host "Resolved command:" -ForegroundColor White
        Write-Host ("  " + (Format-McpCommandLine $Command $Arguments))
        if ($Environment.Count -gt 0) {
            Write-Host "Environment:" -ForegroundColor White
            foreach ($key in ($Environment.Keys | Sort-Object)) {
                Write-Host "  $key=$($Environment[$key])"
            }
        }
    }
    Write-Host ""

    switch ($Harness) {
        "opencode" {
            Write-Host "Add to opencode.json (project root, or ~\.config\opencode\opencode.json)," -ForegroundColor White
            Write-Host "merging into any existing `"mcp`" block, then restart OpenCode:" -ForegroundColor White
            Write-Host ""
            $json = @()
            $json += "{"
            $json += "  `"mcp`": {"
            $json += "    " + (ConvertTo-McpJsonString $Name) + ": {"
            if ($isHttp) {
                $json += "      `"type`": `"remote`","
                $json += "      `"url`": " + (ConvertTo-McpJsonString $Url) + ","
            } else {
                $json += "      `"type`": `"local`","
                $cmdLine = "      `"command`": " + (ConvertTo-McpJsonArray (@($Command) + $Arguments)) + ","
                $json += $cmdLine
                if ($Environment.Count -gt 0) {
                    $json += "      `"environment`": {"
                    $json += (ConvertTo-McpJsonObject $Environment "        ")
                    $json += "      },"
                }
            }
            $json += "      `"enabled`": true"
            $json += "    }"
            $json += "  }"
            $json += "}"
            foreach ($line in $json) { Write-Host $line -ForegroundColor Cyan }
        }
        "qwen" {
            Write-Host "Add to ~\.qwen\settings.json, merging into any existing `"mcpServers`"" -ForegroundColor White
            Write-Host "block, then restart Qwen Code:" -ForegroundColor White
            Write-Host ""
            $json = @()
            $json += "{"
            $json += "  `"mcpServers`": {"
            $json += "    " + (ConvertTo-McpJsonString $Name) + ": {"
            if ($isHttp) {
                $json += "      `"httpUrl`": " + (ConvertTo-McpJsonString $Url)
            } else {
                $json += "      `"command`": " + (ConvertTo-McpJsonString $Command) + ","
                $argsLine = "      `"args`": " + (ConvertTo-McpJsonArray $Arguments)
                if ($Environment.Count -gt 0) {
                    $json += ($argsLine + ",")
                    $json += "      `"env`": {"
                    $json += (ConvertTo-McpJsonObject $Environment "        ")
                    $json += "      }"
                } else {
                    $json += $argsLine
                }
            }
            $json += "    }"
            $json += "  }"
            $json += "}"
            foreach ($line in $json) { Write-Host $line -ForegroundColor Cyan }
        }
        default {
            Write-Host "Paste the values above into your MCP client's config. For a ready-made" -ForegroundColor Gray
            Write-Host "snippet re-run this script with -Harness opencode or -Harness qwen." -ForegroundColor Gray
        }
    }
    Write-Host ""
}
