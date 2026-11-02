#!/bin/bash
# Runs the unmodified SWT-Bench harness in its container. Everything after the script name
# goes to src.main. Logs live on E:, Docker's data disk, and images stay in Docker.
export MSYS_NO_PATHCONV=1
exec docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v swt-hf:/hf -e HF_HOME=/hf -e HF_HUB_DISABLE_TELEMETRY=1 \
  -v E:/swt-scoring/run_instance_swt_logs:/app/run_instance_swt_logs \
  -v E:/swt-scoring/image_build_logs:/app/image_build_logs \
  -v E:/swt-scoring/evaluation_results:/app/evaluation_results \
  -v G:/PhD-Prototype/local/02-rephrase-check/scoring/preds:/preds:ro \
  swt-harness:eee3862 \
  python -m src.main --dataset_name princeton-nlp/SWE-bench_Verified --filter_swt "$@"
