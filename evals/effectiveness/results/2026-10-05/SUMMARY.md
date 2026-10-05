# Skill effectiveness eval: results

Date 2026-10-05, model `claude-sonnet-5-5`, 2.1.289 (Claude Code), source commit `9f421f023ada`. 30 valid of 30 scheduled runs.

| Task | Arm | n | Compiles (attempt 1) | Compiles (within 2) | Convention checks (agent-decided) | Generator checks | Mean turns | Mean failed build cmds | Mean minutes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| classifier | baseline | 3 | 3/3 | 3/3 | 43.6% | 100.0% | 18.33 | 2.33 | 0.94 |
| classifier | skill | 3 | 3/3 | 3/3 | 76.9% | 100.0% | 27.33 | 1.0 | 1.55 |
| mcp-server | baseline | 3 | 3/3 | 3/3 | 53.8% | 100.0% | 24.67 | 6.33 | 1.31 |
| mcp-server | skill | 3 | 3/3 | 3/3 | 92.3% | 100.0% | 29.0 | 0.33 | 1.73 |
| parallel | baseline | 3 | 3/3 | 3/3 | 23.1% | 86.7% | 20.0 | 5.0 | 1.43 |
| parallel | skill | 3 | 3/3 | 3/3 | 92.3% | 100.0% | 26.67 | 1.33 | 1.73 |
| rag | baseline | 3 | 3/3 | 3/3 | 46.2% | 60.0% | 18.0 | 5.67 | 1.13 |
| rag | skill | 3 | 3/3 | 3/3 | 92.3% | 100.0% | 27.0 | 0.67 | 3.39 |
| tools | baseline | 3 | 3/3 | 3/3 | 46.2% | 100.0% | 18.33 | 3.33 | 0.86 |
| tools | skill | 3 | 3/3 | 3/3 | 76.9% | 100.0% | 29.33 | 2.0 | 1.87 |
| **All tasks** | baseline | 15 | 15/15 | 15/15 | 42.6% | 89.3% | 19.87 | 4.53 | 1.14 |
| **All tasks** | skill | 15 | 15/15 | 15/15 | 86.2% | 100.0% | 27.87 | 1.07 | 2.05 |

Delta (skill minus baseline): compile at attempt 1 +0.0 pp, compile within two attempts +0.0 pp, agent-decided convention checks +43.6 pp, generator checks +10.7 pp.

## Per-check pass counts

| Check | Baseline | Skill |
| --- | --- | --- |
| `agent_annotation` | 0/3 | 3/3 |
| `agentic_extension` | 0/3 | 3/3 |
| `ai_service` | 15/15 | 15/15 |
| `delimited_input` | 0/15 | 13/15 |
| `dev_logging` | 0/15 | 15/15 |
| `devservices_off` | 0/15 | 14/15 |
| `dual_bom` | 15/15 | 15/15 |
| `easy_rag_extension` | 3/3 | 3/3 |
| `easy_rag_path` | 3/3 | 3/3 |
| `embedding_dependency` | 0/3 | 3/3 |
| `enum_result` | 3/3 | 3/3 |
| `fault_tolerance` | 0/6 | 0/6 |
| `input_guardrail` | 0/15 | 15/15 |
| `java_release_25` | 11/15 | 15/15 |
| `llm_tool` | 3/3 | 3/3 |
| `llm_tools_wired` | 6/6 | 6/6 |
| `mcp_server_extension` | 3/3 | 3/3 |
| `mcp_tool` | 3/3 | 3/3 |
| `mcp_tool_arg` | 3/3 | 3/3 |
| `memory_id` | 3/3 | 3/3 |
| `named_model` | 0/15 | 0/15 |
| `native_profile` | 11/15 | 15/15 |
| `no_executor_glue` | 0/3 | 3/3 |
| `no_extension_version_pins` | 15/15 | 15/15 |
| `no_manual_wiring` | 15/15 | 15/15 |
| `parallel_agent` | 0/3 | 3/3 |
| `parameters_flag` | 15/15 | 15/15 |
| `record_dto` | 15/15 | 15/15 |
| `sample_document` | 3/3 | 3/3 |
| `smoke_test` | 2/15 | 15/15 |
| `virtual_threads` | 0/3 | 0/3 |
| `zero_temperature` | 3/3 | 3/3 |

The skill arm invoked `scaffold-project` in 15/15 runs.
Excluded runs: 0.
