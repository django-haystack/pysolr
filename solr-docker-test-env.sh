#!/bin/bash

set -e

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    echo "Usage: $0 [setup|destroy]"
    echo -e "  ${GREEN}setup${NC}    : Start Solr Docker test server and wait for initialization"
    echo -e "  ${RED}destroy${NC}  : Stop Solr Docker test server and remove volumes"
    exit 1
}

# Check if exactly one argument is provided
if [ $# -ne 1 ]; then
    echo -e "${YELLOW}Warning: Exactly one flag is required${NC}"
    usage
fi

# Parse the flag
case "$1" in
help | --help | -h)
    usage
    ;;

setup)
    echo -e "${CYAN}=== Starting Solr Docker Test Environment Setup ===${NC}"

    # Start docker compose in detached mode
    echo -e "${BLUE}→ Running \`docker compose -f docker/docker-compose-solr.yml up -d\`...${NC}"
    docker compose -f docker/docker-compose-solr.yml up -d

    # Wait for the solr-init container to finish (60-second timeout)
    echo -e "${BLUE}→ Waiting for solr-init container to complete (timeout: 60 seconds)...${NC}"
    if timeout 60 docker container wait solr-init; then
        # Capture the exit code of the solr-init container
        EXIT_CODE=$(docker inspect solr-init --format='{{.State.ExitCode}}')
        echo -e "${BLUE}→ solr-init container exited with code: ${EXIT_CODE}${NC}"

        if [ "$EXIT_CODE" -eq 0 ]; then
            echo -e "${GREEN}✓ Setup completed successfully!${NC}"
            echo -e "${GREEN}✓ Solr test server is ready${NC}"
            exit 0
        else
            echo -e "${RED}✗ Error: solr-init container failed with exit code ${EXIT_CODE}${NC}"
            echo -e "${YELLOW}Fetching logs from solr-init:${NC}"
            docker logs solr-init
            exit 1
        fi
    else
        echo -e "${RED}✗ Error: Timeout waiting for solr-init container${NC}"
        echo -e "${YELLOW}Fetching logs from solr-init:${NC}"
        docker logs solr-init
        exit 1
    fi
    ;;

destroy)
    echo -e "${CYAN}=== Starting Solr Docker Test Environment Teardown ===${NC}"

    # Stop docker compose and remove volumes
    echo -e "${BLUE}→ Running \`docker compose -f docker/docker-compose-solr.yml down -v\`...${NC}"
    docker compose -f docker/docker-compose-solr.yml down -v

    echo -e "${GREEN}✓ Teardown completed successfully!${NC}"
    echo -e "${GREEN}✓ All containers and volumes removed${NC}"
    exit 0
    ;;

*)
    echo -e "${RED}Error: Invalid flag '$1'${NC}"
    usage
    ;;
esac
