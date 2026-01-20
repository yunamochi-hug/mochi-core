#!/bin/bash
# YUNA v2 - Smart Activity Loop
# Faster during travel, slower when idle

cd /root/mochi
source venv/bin/activate

echo "=========================================="
echo "🫶 YUNA v2 - SMART ACTIVITY LOOP"
echo "=========================================="
echo "Started at: $(date)"
echo "Dashboard: http://152.42.177.43:5000"
echo "=========================================="

mkdir -p /root/mochi/logs

while true; do
    echo ""
    echo "$(date): ============ YUNA CYCLE ============" >> /root/mochi/logs/yuna.log
    
    # Run Yuna's life cycle
    python mochi_soul_v2.py >> /root/mochi/logs/yuna.log 2>&1
    
    # Check travel status for smart timing
    TRAVEL_STATUS=$(python -c "
import json
try:
    with open('data/travel_full.json', 'r') as f:
        travel = json.load(f)
    with open('data/state.json', 'r') as f:
        state = json.load(f)
    
    status = travel.get('status', 'idle')
    step = state.get('current_step', 'idle')
    
    # Fast mode during active travel
    if status == 'booked':
        print('TRAVELING')
    # Medium mode at destination
    elif status == 'completed' and step in ['exploring', 'mochi_time', 'after_hugs']:
        print('ACTIVE')
    # Slow mode otherwise
    else:
        print('IDLE')
except:
    print('IDLE')
" 2>/dev/null)
    
    # Set sleep time based on mode
    if [ "$TRAVEL_STATUS" = "TRAVELING" ]; then
        # Active travel - check every 5-10 minutes
        MIN_SLEEP=300   # 5 minutes
        MAX_SLEEP=600   # 10 minutes
        MODE="✈️ TRAVEL MODE"
    elif [ "$TRAVEL_STATUS" = "ACTIVE" ]; then
        # At destination doing things - 10-20 minutes
        MIN_SLEEP=600   # 10 minutes
        MAX_SLEEP=1200  # 20 minutes
        MODE="🚶 ACTIVE MODE"
    else
        # Idle/resting - 15-30 minutes
        MIN_SLEEP=900   # 15 minutes
        MAX_SLEEP=1800  # 30 minutes
        MODE="😴 IDLE MODE"
    fi
    
    SLEEP_TIME=$((RANDOM % (MAX_SLEEP - MIN_SLEEP + 1) + MIN_SLEEP))
    SLEEP_MINS=$((SLEEP_TIME / 60))
    
    echo "$(date): $MODE - Next cycle in ${SLEEP_MINS} minutes" >> /root/mochi/logs/yuna.log
    
    sleep $SLEEP_TIME
done
