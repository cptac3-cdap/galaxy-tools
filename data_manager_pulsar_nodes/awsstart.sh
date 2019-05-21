#!/bin/sh
export PYTHONPATH=/mnt/galaxy/galaxy-app/lib:
/mnt/galaxy/galaxy-app/.venv/bin/python data_manager_pulsar_nodes.py start "" aws "" /mnt/galaxy/tools/edwardslab/data_manager_pulsar_nodes /mnt/galaxy/galaxy-app/tool-data
