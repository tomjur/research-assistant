# Hyperparameters (this task)

| Parameter | Value | Notes |
|-----------|-------|-------|
| `$InitialPromptVariants$` | | |
| `$MaxCountToFindUniquePrompts$` | | |
| `$WorkersPerTask$` | | total cap per (prompt variant, worker model) pair |
| `$EarlyStoppingWorkers$` | | per-vendor batch size per round + consecutive-no-new-info threshold; default 2 |
| `$MaxOrchestratorIterations$` | | |
| `$ControlPlaneModel$` | | see protocol table; mirror in `TOOLS_AND_MCP.md` |
| `$ModelsForThisTask$` | | see protocol table; mirror in `TOOLS_AND_MCP.md` |

Meanings: [RESEARCH_PROTOCOL.md — Hyperparameters](../RESEARCH_PROTOCOL.md#hyperparameters).
