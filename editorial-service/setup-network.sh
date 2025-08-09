#!/bin/bash
# Vector Wave Shared Network Setup
# Creates shared Docker network for Vector Wave ecosystem integration

set -euo pipefail

NETWORK_NAME="vector-wave-shared"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🌊 Vector Wave Network Setup"
echo "=============================="

# Function to check if Docker is running
check_docker() {
    if ! docker info &> /dev/null; then
        echo "❌ Docker is not running. Please start Docker and try again."
        exit 1
    fi
    echo "✅ Docker is running"
}

# Function to check if network exists
network_exists() {
    docker network ls --filter name=^${NETWORK_NAME}$ --format "{{.Name}}" | grep -q "^${NETWORK_NAME}$"
}

# Function to create network
create_network() {
    echo "🔧 Creating shared network: ${NETWORK_NAME}"
    docker network create \
        --driver bridge \
        --subnet 172.22.0.0/16 \
        --gateway 172.22.0.1 \
        --opt com.docker.network.bridge.name=br-vector-wave \
        --opt com.docker.network.bridge.enable_icc=true \
        --opt com.docker.network.bridge.enable_ip_masquerade=true \
        --opt com.docker.network.driver.mtu=1500 \
        --label com.vectorwave.network=shared \
        --label com.vectorwave.version=2.0.0 \
        ${NETWORK_NAME}
    
    echo "✅ Network ${NETWORK_NAME} created successfully"
}

# Function to inspect network
inspect_network() {
    echo "🔍 Network Information:"
    echo "======================"
    docker network inspect ${NETWORK_NAME} --format "{{.Name}}: {{.Driver}} ({{.Scope}})"
    docker network inspect ${NETWORK_NAME} --format "Gateway: {{(index .IPAM.Config 0).Gateway}}"
    docker network inspect ${NETWORK_NAME} --format "Subnet: {{(index .IPAM.Config 0).Subnet}}"
    echo ""
}

# Function to list connected services
list_connected_services() {
    local containers
    containers=$(docker network inspect ${NETWORK_NAME} --format "{{range \$k,\$v := .Containers}}{{printf \"%s\\n\" \$v.Name}}{{end}}" | sort)
    
    if [[ -n "$containers" ]]; then
        echo "🔗 Connected Services:"
        echo "====================="
        echo "$containers" | while read -r container; do
            if [[ -n "$container" ]]; then
                echo "  - $container"
            fi
        done
    else
        echo "📭 No services currently connected to ${NETWORK_NAME}"
    fi
    echo ""
}

# Function to create development environment file
create_dev_env() {
    local env_file="${SCRIPT_DIR}/.env.network"
    
    cat > "$env_file" << EOF
# Vector Wave Network Configuration
NETWORK_NAME=${NETWORK_NAME}
NETWORK_GATEWAY=172.22.0.1
NETWORK_SUBNET=172.22.0.0/16

# Service Discovery
SERVICE_REGISTRY_URL=redis://redis:6379
JAEGER_ENDPOINT=http://jaeger:14268/api/traces
PROMETHEUS_URL=http://prometheus:9090

# Development overrides
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost:3001
LOG_LEVEL=debug
ENVIRONMENT=development
EOF

    echo "📄 Created network environment file: .env.network"
}

# Function to verify network connectivity
verify_connectivity() {
    echo "🧪 Testing Network Connectivity"
    echo "==============================="
    
    # Test with a temporary container
    local test_output
    test_output=$(docker run --rm --network ${NETWORK_NAME} alpine:latest /bin/sh -c "
        echo 'Network: ${NETWORK_NAME}'
        echo 'Container IP:' \$(hostname -i)
        echo 'Gateway:' \$(route -n | grep '^0.0.0.0' | awk '{print \$2}')
        ping -c 1 172.20.0.1 > /dev/null 2>&1 && echo 'Gateway reachable: ✅' || echo 'Gateway unreachable: ❌'
    " 2>/dev/null)
    
    echo "$test_output"
    echo ""
}

# Function to show next steps
show_next_steps() {
    echo "🚀 Next Steps"
    echo "============="
    echo "1. Start Vector Wave services:"
    echo "   docker-compose -f docker-compose.dev.yml up -d"
    echo ""
    echo "2. Check service health:"
    echo "   curl http://localhost:8040/health"
    echo ""
    echo "3. View service discovery:"
    echo "   curl http://localhost:8040/info"
    echo ""
    echo "4. Monitor with Prometheus:"
    echo "   http://localhost:9090"
    echo ""
    echo "5. View traces in Jaeger:"
    echo "   http://localhost:16686"
    echo ""
}

# Main execution
main() {
    echo "Starting Vector Wave network setup..."
    
    check_docker
    
    if network_exists; then
        echo "⚠️  Network ${NETWORK_NAME} already exists"
        inspect_network
        list_connected_services
        
        read -p "Do you want to recreate the network? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "🗑️  Removing existing network..."
            docker network rm ${NETWORK_NAME}
            create_network
        fi
    else
        create_network
    fi
    
    inspect_network
    list_connected_services
    create_dev_env
    verify_connectivity
    show_next_steps
    
    echo "✅ Vector Wave network setup complete!"
}

# Handle script arguments
case "${1:-setup}" in
    "setup"|"create")
        main
        ;;
    "remove"|"cleanup")
        echo "🗑️  Cleaning up Vector Wave network..."
        if network_exists; then
            # Stop any connected containers first
            docker network disconnect -f ${NETWORK_NAME} $(docker network inspect ${NETWORK_NAME} --format "{{range \$k,\$v := .Containers}}{{printf \"%s \" \$k}}{{end}}") 2>/dev/null || true
            docker network rm ${NETWORK_NAME}
            echo "✅ Network ${NETWORK_NAME} removed"
        else
            echo "⚠️  Network ${NETWORK_NAME} does not exist"
        fi
        ;;
    "info"|"status")
        check_docker
        if network_exists; then
            inspect_network
            list_connected_services
        else
            echo "❌ Network ${NETWORK_NAME} does not exist. Run './setup-network.sh setup' to create it."
        fi
        ;;
    "test")
        check_docker
        if network_exists; then
            verify_connectivity
        else
            echo "❌ Network ${NETWORK_NAME} does not exist"
            exit 1
        fi
        ;;
    *)
        echo "Usage: $0 {setup|remove|info|test}"
        echo ""
        echo "Commands:"
        echo "  setup   - Create the Vector Wave shared network (default)"
        echo "  remove  - Remove the Vector Wave shared network"
        echo "  info    - Show network information and connected services"
        echo "  test    - Test network connectivity"
        exit 1
        ;;
esac