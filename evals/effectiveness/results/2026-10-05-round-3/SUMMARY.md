# Skill effectiveness eval: results

Date 2026-10-05, model `claude-sonnet-5-5`, 2.1.289 (Claude Code), source commit `30a80a0cf940`. 30 valid of 30 scheduled runs. Repository CLAUDE.md in both arms' run directory: yes (CLAUDE.md).

| Task | Arm | n | Compiles (attempt 1) | Compiles (within 2) | Convention checks (agent-decided) | Generator checks | Mean turns | Mean failed build cmds | Mean minutes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| classifier | baseline | 3 | 3/3 | 3/3 | 100.0% | 100.0% | 22.67 | 2.0 | 3.36 |
| classifier | skill | 3 | 3/3 | 3/3 | 94.9% | 100.0% | 26.67 | 2.0 | 2.11 |
| mcp-server | baseline | 3 | 3/3 | 3/3 | 100.0% | 100.0% | 24.67 | 1.33 | 3.52 |
| mcp-server | skill | 3 | 3/3 | 3/3 | 100.0% | 100.0% | 38.0 | 2.33 | 3.48 |
| parallel | baseline | 3 | 3/3 | 3/3 | 97.4% | 100.0% | 36.67 | 3.0 | 4.27 |
| parallel | skill | 3 | 3/3 | 3/3 | 97.4% | 100.0% | 30.67 | 1.33 | 3.13 |
| rag | baseline | 3 | 3/3 | 3/3 | 94.9% | 100.0% | 18.67 | 0.67 | 3.26 |
| rag | skill | 3 | 3/3 | 3/3 | 100.0% | 100.0% | 27.67 | 1.0 | 3.27 |
| tools | baseline | 3 | 3/3 | 3/3 | 100.0% | 100.0% | 17.0 | 1.0 | 3.3 |
| tools | skill | 3 | 3/3 | 3/3 | 100.0% | 100.0% | 28.67 | 2.33 | 3.07 |
| **All tasks** | baseline | 15 | 15/15 | 15/15 | 98.5% | 100.0% | 23.93 | 1.6 | 3.54 |
| **All tasks** | skill | 15 | 15/15 | 15/15 | 98.5% | 100.0% | 30.33 | 1.8 | 3.01 |

Delta (skill minus baseline): compile at attempt 1 +0.0 pp, compile within two attempts +0.0 pp, agent-decided convention checks +0.0 pp, generator checks +0.0 pp.

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
| `fault_tolerance` | 6/6 | 4/6 |
| `input_guardrail` | 13/15 | 15/15 |
| `java_release_25` | 15/15 | 15/15 |
| `llm_tool` | 3/3 | 3/3 |
| `llm_tools_wired` | 6/6 | 6/6 |
| `mcp_server_extension` | 3/3 | 3/3 |
| `mcp_tool` | 3/3 | 3/3 |
| `mcp_tool_arg` | 3/3 | 3/3 |
| `memory_id` | 3/3 | 3/3 |
| `named_model` | 15/15 | 15/15 |
| `native_profile` | 15/15 | 15/15 |
| `no_executor_glue` | 2/3 | 2/3 |
| `no_extension_version_pins` | 15/15 | 15/15 |
| `no_manual_wiring` | 15/15 | 15/15 |
| `parallel_agent` | 3/3 | 3/3 |
| `parameters_flag` | 15/15 | 15/15 |
| `record_dto` | 15/15 | 15/15 |
| `sample_document` | 3/3 | 3/3 |
| `smoke_test` | 15/15 | 15/15 |
| `virtual_threads` | 3/3 | 3/3 |
| `zero_temperature` | 3/3 | 3/3 |

The skill arm invoked `scaffold-project` in 15/15 runs.
Excluded runs: 0.
