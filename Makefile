.PHONY: container-build container-test container-up container-down

container-build:
	docker build -f Dockerfile.minimal -t ai-writing-flow:minimal .

container-up:
	docker compose -f docker-compose.minimal.yml up -d
	@echo "Waiting for container to be ready..."
	@for i in {1..30}; do \
		if curl -s http://localhost:8003/health > /dev/null; then \
			echo "Container is ready!"; \
			break; \
		fi; \
		sleep 2; \
	done

container-test: container-up
	pytest tests/test_container_api.py -v
	
container-down:
	docker compose -f docker-compose.minimal.yml down

container-full-test: container-build container-test container-down
	@echo "✅ All container tests passed!"

# Quick test routing
test-routing:
	@echo "Testing ORIGINAL (should skip research):"
	@curl -s -X POST http://localhost:8003/api/test-routing \
		-H "Content-Type: application/json" \
		-d '{"title": "Test", "content_ownership": "ORIGINAL"}' | jq .
	
	@echo "\nTesting EXTERNAL (should do research):"
	@curl -s -X POST http://localhost:8003/api/test-routing \
		-H "Content-Type: application/json" \
		-d '{"title": "Test", "content_ownership": "EXTERNAL"}' | jq .

logs:
	docker compose -f docker-compose.minimal.yml logs -f

clean:
	docker compose -f docker-compose.minimal.yml down
	docker rmi ai-writing-flow:minimal || true

all: clean container-build container-up test-routing