# RambaZamba
collection of networking tools.

# Usage Instructions
Make scripts executable and run setup:

bash
chmod +x *.sh
./quick_setup.sh


After setup, you can monitor activities with:

bash
# View honeypot logs
tail -f honeypot.log

# View network traffic
tail -f network_traffic.log

# View connection attempts  
tail -f connection_attempts.log

# Live dashboard
python monitoring_dashboard.py
