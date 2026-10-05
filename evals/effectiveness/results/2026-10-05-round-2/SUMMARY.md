# Skill effectiveness eval: results

Date 2026-10-05, model `claude-sonnet-5-5`, 2.1.289 (Claude Code), source commit `7ca90d458502`. 30 valid of 30 scheduled runs. Repository CLAUDE.md in both arms' run directory: yes (CLAUDE.md).

| Task | Arm | n | Compiles (attempt 1) | Compiles (within 2) | Convention checks (agent-decided) | Generator checks | Mean turns | Mean failed build cmds | Mean minutes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| classifier | baseline | 3 | 3/3 | 3/3 | 92.3% | 100.0% | 24.67 | 1.33 | 3.41 |
| classifier | skill | 3 | 3/3 | 3/3 | 92.3% | 100.0% | 23.33 | 1.0 | 1.44 |
| mcp-server | baseline | 3 | 3/3 | 3/3 | 89.7% | 100.0% | 24.33 | 1.33 | 3.72 |
| mcp-server | skill | 3 | 3/3 | 3/3 | 92.3% | 100.0% | 29.33 | 1.0 | 1.97 |
| parallel | baseline | 3 | 3/3 | 3/3 | 94.9% | 100.0% | 21.67 | 2.0 | 3.5 |
| parallel | skill | 3 | 3/3 | 3/3 | 97.4% | 100.0% | 28.67 | 1.0 | 1.91 |
| rag | baseline | 3 | 3/3 | 3/3 | 82.1% | 80.0% | 21.0 | 2.0 | 3.34 |
| rag | skill | 3 | 3/3 | 3/3 | 92.3% | 100.0% | 28.0 | 0.33 | 3.49 |
| tools | baseline | 3 | 3/3 | 3/3 | 87.2% | 100.0% | 22.67 | 1.67 | 3.55 |
| tools | skill | 3 | 3/3 | 3/3 | 92.3% | 100.0% | 27.0 | 0.67 | 1.57 |
| **All tasks** | baseline | 15 | 15/15 | 15/15 | 89.2% | 96.0% | 22.87 | 1.67 | 3.5 |
| **All tasks** | skill | 15 | 15/15 | 15/15 | 93.3% | 100.0% | 27.27 | 0.8 | 2.08 |

Delta (skill minus baseline): compile at attempt 1 +0.0 pp, compile within two attempts +0.0 pp, agent-decided convention checks +4.1 pp, generator checks +4.0 pp.

## Per-check pass counts

| Check | Baseline | Skill |
| --- | --- | --- |
| `agent_annotation` | 3/3 | 3/3 |
| `agentic_extension` | 3/3 | 3/3 |
| `ai_service` | 15/15 | 15/15 |
| `delimited_input` | 15/15 | 15/15 |
| `dev_logging` | 15/15 | 15/15 |
| `devservices_off` | 15/15 | 15/15 |
| `dual_bom` | 15/15 | 15/15 |
| `easy_rag_extension` | 3/3 | 3/3 |
| `easy_rag_path` | 3/3 | 3/3 |
| `embedding_dependency` | 3/3 | 3/3 |
| `enum_result` | 3/3 | 3/3 |
| `fault_tolerance` | 6/6 | 6/6 |
| `input_guardrail` | 11/15 | 15/15 |
| `java_release_25` | 15/15 | 15/15 |
| `llm_tool` | 3/3 | 3/3 |
| `llm_tools_wired` | 6/6 | 6/6 |
| `mcp_server_extension` | 3/3 | 3/3 |
| `mcp_tool` | 3/3 | 3/3 |
| `mcp_tool_arg` | 3/3 | 3/3 |
| `memory_id` | 3/3 | 3/3 |
| `named_model` | 6/15 | 5/15 |
| `native_profile` | 15/15 | 15/15 |
| `no_executor_glue` | 3/3 | 3/3 |
| `no_extension_version_pins` | 12/15 | 15/15 |
| `no_manual_wiring` | 15/15 | 15/15 |
| `parallel_agent` | 3/3 | 3/3 |
| `parameters_flag` | 15/15 | 15/15 |
| `record_dto` | 15/15 | 15/15 |
| `sample_document` | 3/3 | 3/3 |
| `smoke_test` | 9/15 | 15/15 |
| `virtual_threads` | 1/3 | 0/3 |
| `zero_temperature` | 3/3 | 3/3 |

The skill arm invoked `scaffold-project` in 15/15 runs.
Excluded runs: 0.
