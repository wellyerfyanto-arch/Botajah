#!/bin/bash

# Function to connect to VPN
connect_vpn() {
    local vpn_config=$1
    echo "Connecting to VPN: $vpn_config"
    
    # Kill any existing OpenVPN processes
    pkill openvpn || true
    sleep 2
    
    # Start OpenVPN in background
    openvpn --config "/app/vpn-configs/$vpn_config" --auth-nocache --daemon
    sleep 10
    
    # Verify VPN connection
    if curl -s --max-time 5 ifconfig.io > /dev/null 2>&1; then
        CURRENT_IP=$(curl -s ifconfig.io)
        echo "VPN Connected! Current IP: $CURRENT_IP"
        return 0
    else
        echo "VPN Connection failed"
        return 1
    fi
}

# Function to disconnect VPN
disconnect_vpn() {
    echo "Disconnecting VPN..."
    pkill openvpn || true
    sleep 5
}

# Function to get random VPN config
get_random_vpn_config() {
    local configs=($(ls /app/vpn-configs/*.ovpn 2>/dev/null || echo ""))
    if [ ${#configs[@]} -eq 0 ]; then
        echo ""
    else
        basename "${configs[RANDOM % ${#configs[@]}]}"
    fi
}

# Main execution
echo "Starting Automated Browser System with VPN Support"

# Check if VPN configs exist
VPN_CONFIGS=$(ls /app/vpn-configs/*.ovpn 2>/dev/null | wc -l)
if [ $VPN_CONFIGS -eq 0 ]; then
    echo "Warning: No VPN configurations found. Running without VPN."
    echo "To use VPN, add .ovpn files to the vpn-configs/ directory"
    
    # Start application without VPN
    gunicorn app:app --bind 0.0.0.0:5000 --workers 2 --threads 4
else
    echo "Found $VPN_CONFIGS VPN configuration(s)"
    
    # Connect to initial VPN
    INITIAL_VPN=$(get_random_vpn_config)
    connect_vpn "$INITIAL_VPN"
    
    # Start the application with VPN monitoring in background
    gunicorn app:app --bind 0.0.0.0:5000 --workers 2 --threads 4 &
    APP_PID=$!
    
    # VPN rotation every 10-30 minutes
    while kill -0 $APP_PID 2>/dev/null; do
        sleep $((600 + RANDOM % 1200))  # 10-30 minutes
        
        if [ $((RANDOM % 3)) -eq 0 ]; then  # 33% chance to rotate VPN
            NEW_VPN=$(get_random_vpn_config)
            disconnect_vpn
            connect_vpn "$NEW_VPN"
        fi
    done
    
    # Cleanup
    disconnect_vpn
    wait $APP_PID
fi
