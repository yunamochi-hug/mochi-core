#!/bin/bash
# YUNA - 48 Hour Live Test Runner
# Posts randomly every 25 minutes to 3 hours

cd /root/mochi
source venv/bin/activate

echo "=========================================="
echo "🫶 YUNA 48-HOUR LIVE TEST"
echo "=========================================="
echo "Started at: $(date)"
echo "Dashboard: http://152.42.177.43:5000"
echo "=========================================="

mkdir -p /root/mochi/logs

while true; do
    echo ""
    echo "$(date): ============ YUNA CYCLE ============" >> /root/mochi/logs/yuna.log
    
    python mochi_soul.py >> /root/mochi/logs/yuna.log 2>&1
    
    # Random sleep between 25 minutes (1500s) and 3 hours (10800s)
    MIN_SLEEP=1500
    MAX_SLEEP=10800
    
    SLEEP_TIME=$((RANDOM % (MAX_SLEEP - MIN_SLEEP + 1) + MIN_SLEEP))
    SLEEP_MINS=$((SLEEP_TIME / 60))
    
    echo "$(date): Next cycle in ${SLEEP_MINS} minutes" >> /root/mochi/logs/yuna.log
    
    sleep $SLEEP_TIME
done
