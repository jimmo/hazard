#!/bin/bash
source venv/bin/activate
bluetoothctl power on
python3 -m hazard.main
