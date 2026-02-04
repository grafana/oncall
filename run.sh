export COMPOSE_PROFILES=engine,oncall_ui,redis,postgres,grafana 
export DB=postgres 
export BROKER_TYPE=redis 
docker compose -f docker-compose-developer.yml up -d --force-recreate
