#!/bin/bash

echo "Starting Qdrant vector DB via Docker..."
docker pull qdrant/qdrant:1.16.0

docker stop qdrant-finagent &> /dev/null
docker rm qdrant-finagent &> /dev/null

docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant:1.16.0

# Uncomment the line below if you want to run it in detached mode
# docker run -d --name qdrant-finagent -p 6333:6333 -p 6334:6334 -v "$(pwd)/qdrant_storage:/qdrant/storage" qdrant/qdrant:1.16.0

if [ $? -ne 0 ]; then
    echo "Docker error. Ensure Docker is running. Fallback to local Qdrant (no server)."
    echo "No action needed - code uses local by default."
else
    echo "Monitor Qdrant server at http://localhost:6333/dashboard"
    echo "Add QDRANT_URL=http://localhost:6333 to config/.env"
    echo "Check collection by http://10.192.237.16:6333/collections/finagent_reports"
fi

read -p "Press Enter to continue..."