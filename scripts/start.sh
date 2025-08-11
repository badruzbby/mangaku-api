#!/bin/bash

# Mangaku API Startup Script
# This script sets up and starts the Mangaku API with all optimizations

set -e

echo "🎌 Starting Mangaku API Setup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_status "Docker and Docker Compose are available"
}

# Check if Redis is running
check_redis() {
    if docker ps | grep -q "mangaku-redis"; then
        print_status "Redis is already running"
        return 0
    fi
    
    print_warning "Redis is not running. Starting Redis..."
    docker-compose up -d redis
    
    # Wait for Redis to be ready
    print_status "Waiting for Redis to be ready..."
    sleep 5
    
    if docker-compose exec redis redis-cli ping | grep -q "PONG"; then
        print_status "Redis is ready"
    else
        print_error "Failed to start Redis"
        exit 1
    fi
}

# Setup environment
setup_environment() {
    print_header "Setting up environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        print_status "Creating .env file..."
        cat > .env << EOF
# Mangaku API Configuration
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
REDIS_URL=redis://localhost:6379

# Performance Settings
CACHE_DEFAULT_TIMEOUT=300
RATELIMIT_DEFAULT=100 per hour, 20 per minute

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/mangaku-api.log
EOF
        print_status "Created .env file with default settings"
    else
        print_status ".env file already exists"
    fi
    
    # Create logs directory
    mkdir -p logs
    print_status "Created logs directory"
}

# Build and start services
start_services() {
    print_header "Building and starting services..."
    
    # Build the application
    print_status "Building Mangaku API..."
    docker-compose build api
    
    # Start all services
    print_status "Starting all services..."
    docker-compose up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check health
    if curl -f http://localhost:5000/health > /dev/null 2>&1; then
        print_status "API is healthy and ready!"
    else
        print_warning "API might still be starting up. Check logs with: docker-compose logs -f api"
    fi
}

# Show service status
show_status() {
    print_header "Service Status:"
    docker-compose ps
    
    echo ""
    print_header "Available Services:"
    echo "🌐 API: http://localhost:5000"
    echo "📚 Swagger Docs: http://localhost:5000/docs/"
    echo "🏥 Health Check: http://localhost:5000/health"
    echo "🔧 Redis Commander: http://localhost:8081 (if enabled)"
    
    echo ""
    print_header "Useful Commands:"
    echo "📊 Monitor performance: python scripts/monitor.py --mode monitor"
    echo "🧪 Run load test: python scripts/monitor.py --mode load --duration 60"
    echo "📋 View logs: docker-compose logs -f api"
    echo "🛑 Stop services: docker-compose down"
    echo "🔄 Restart services: docker-compose restart"
    echo "🧹 Clear cache: curl -X POST http://localhost:5000/health/cache/clear"
}

# Performance test
run_performance_test() {
    print_header "Running Performance Test..."
    
    if command -v python3 &> /dev/null; then
        python3 scripts/monitor.py --mode health
        print_status "Basic health check completed"
        
        read -p "Run full load test? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            python3 scripts/monitor.py --mode load --duration 30
        fi
    else
        print_warning "Python3 not available. Skipping performance test."
    fi
}

# Cleanup function
cleanup() {
    print_header "Cleaning up..."
    docker-compose down
    print_status "Services stopped"
}

# Main menu
show_menu() {
    echo ""
    print_header "🎌 Mangaku API Management"
    echo "1) Full Setup (recommended for first time)"
    echo "2) Start Services"
    echo "3) Stop Services"
    echo "4) Restart Services"
    echo "5) Show Status"
    echo "6) View Logs"
    echo "7) Performance Test"
    echo "8) Clear Cache"
    echo "9) Enable Redis Commander"
    echo "0) Exit"
    echo ""
}

# Handle menu selection
handle_selection() {
    case $1 in
        1)
            check_docker
            setup_environment
            check_redis
            start_services
            show_status
            run_performance_test
            ;;
        2)
            check_docker
            docker-compose up -d
            show_status
            ;;
        3)
            docker-compose down
            print_status "Services stopped"
            ;;
        4)
            docker-compose restart
            print_status "Services restarted"
            ;;
        5)
            show_status
            ;;
        6)
            docker-compose logs -f api
            ;;
        7)
            run_performance_test
            ;;
        8)
            curl -X POST http://localhost:5000/health/cache/clear
            print_status "Cache cleared"
            ;;
        9)
            docker-compose --profile tools up -d redis-commander
            print_status "Redis Commander started at http://localhost:8081"
            ;;
        0)
            cleanup
            exit 0
            ;;
        *)
            print_error "Invalid option"
            ;;
    esac
}

# Main execution
main() {
    # Check if running with arguments
    if [ $# -eq 0 ]; then
        # Interactive mode
        while true; do
            show_menu
            read -p "Select an option: " choice
            handle_selection $choice
            echo ""
            read -p "Press Enter to continue..."
        done
    else
        # Command line mode
        case $1 in
            "setup")
                check_docker
                setup_environment
                check_redis
                start_services
                show_status
                ;;
            "start")
                check_docker
                docker-compose up -d
                ;;
            "stop")
                docker-compose down
                ;;
            "status")
                show_status
                ;;
            "test")
                run_performance_test
                ;;
            *)
                echo "Usage: $0 [setup|start|stop|status|test]"
                exit 1
                ;;
        esac
    fi
}

# Trap Ctrl+C
trap cleanup EXIT

# Run main function
main "$@" 