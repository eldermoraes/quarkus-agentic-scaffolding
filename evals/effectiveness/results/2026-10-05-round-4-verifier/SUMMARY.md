# Skill effectiveness eval: results

Date 2026-10-05, model `claude-sonnet-5-5`, 2.1.289 (Claude Code), source commit `b5840dbaa454`. 15 valid of 15 scheduled runs. Repository CLAUDE.md in both arms' run directory: yes (CLAUDE.md).

| Task | Arm | n | Compiles (attempt 1) | Compiles (within 2) | Convention checks (agent-decided) | Generator checks | Mean turns | Mean failed build cmds | Mean minutes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| classifier | skill | 3 | 3/3 | 3/3 | 97.4% | 100.0% | 24.67 | 1.0 | 1.93 |
| mcp-server | skill | 3 | 3/3 | 3/3 | 100.0% | 100.0% | 36.33 | 0.67 | 2.94 |
| parallel | skill | 3 | 3/3 | 3/3 | 100.0% | 100.0% | 31.67 | 1.67 | 2.95 |
| rag | skill | 3 | 3/3 | 3/3 | 100.0% | 100.0% | 28.33 | 1.0 | 3.34 |
| tools | skill | 3 | 3/3 | 3/3 | 100.0% | 100.0% | 35.33 | 2.33 | 2.88 |
| **All tasks** | skill | 15 | 15/15 | 15/15 | 99.5% | 100.0% | 31.27 | 1.33 | 2.81 |

## Per-check pass counts

| Check | Baseline | Skill |
| --- | --- | --- |
| `agent_annotation` | 0/0 | 3/3 |
| `agentic_extension` | 0/0 | 3/3 |
| `ai_service` | 0/0 | 15/15 |
| `delimited_input` | 0/0 | 15/15 |
| `dev_logging` | 0/0 | 15/15 |
| `devservices_off` | 0/0 | 15/15 |
| `dual_bom` | 0/0 | 15/15 |
| `easy_rag_extension` | 0/0 | 3/3 |
| `easy_rag_path` | 0/0 | 3/3 |
| `embedding_dependency` | 0/0 | 3/3 |
| `enum_result` | 0/0 | 3/3 |
| `fault_tolerance` | 0/0 | 5/6 |
| `input_guardrail` | 0/0 | 15/15 |
| `java_release_25` | 0/0 | 15/15 |
| `llm_tool` | 0/0 | 3/3 |
| `llm_tools_wired` | 0/0 | 6/6 |
| `mcp_server_extension` | 0/0 | 3/3 |
| `mcp_tool` | 0/0 | 3/3 |
| `mcp_tool_arg` | 0/0 | 3/3 |
| `memory_id` | 0/0 | 3/3 |
| `named_model` | 0/0 | 15/15 |
| `native_profile` | 0/0 | 15/15 |
| `no_executor_glue` | 0/0 | 3/3 |
| `no_extension_version_pins` | 0/0 | 15/15 |
| `no_manual_wiring` | 0/0 | 15/15 |
| `parallel_agent` | 0/0 | 3/3 |
| `parameters_flag` | 0/0 | 15/15 |
| `record_dto` | 0/0 | 15/15 |
| `sample_document` | 0/0 | 3/3 |
| `smoke_test` | 0/0 | 15/15 |
| `virtual_threads` | 0/0 | 3/3 |
| `zero_temperature` | 0/0 | 3/3 |

The skill arm invoked `scaffold-project` in 15/15 runs.
Excluded runs: 0.
