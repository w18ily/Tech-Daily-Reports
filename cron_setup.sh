#!/bin/bash
# 设置每天上午 10:00 运行

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_CMD="0 10 * * * cd $SCRIPT_DIR && bash run.sh >> $SCRIPT_DIR/output/cron.log 2>&1"

# 检查是否已存在
if crontab -l 2>/dev/null | grep -q "tech-daily"; then
    echo "Cron job already exists."
else
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "Cron job added: 每天 10:00 运行"
fi

echo "Current crontab:"
crontab -l
