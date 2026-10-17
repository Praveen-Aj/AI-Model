"""
Async Ollama REST API Client
Handles direct API calls to Ollama server
"""

import aiohttp
import asyncio
import logging
import sys
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# Setup logging with UTF-8 encoding
import codecs

# Ensure UTF-8 encoding for stdout
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/ollama_client.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
    force=True,
)
logger = logging.getLogger(__name__)


@dataclass
class Model:
    name: str
    size: int
    digest: str
    modified_at: datetime
    details: Dict[str, Any]


@dataclass
class RunningModel:
    name: str
    model: str
    size: int
    digest: str
    parent_digest: str
    created_at: datetime


@dataclass
class ModelInfo:
    name: str
    architecture: str
    parameters: str
    context_length: int
    embedding_length: int
    quantization: str
    capabilities: List[str]


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=300)  # 5 minute timeout

    async def is_service_running(self) -> bool:
        try:
            await self._make_request(
                "GET", "/api/tags", suppress_error_logging=True
            )
            return True
        except Exception:
            return False

    async def _make_request(
        self, method: str, endpoint: str, suppress_error_logging: bool = False, **kwargs
    ) -> Dict[str, Any]:
        """Make async request to Ollama API"""
        url = f"{self.base_url}{endpoint}"

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            try:
                async with session.request(method, url, **kwargs) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"Ollama response from {endpoint}: {data}")
                        # Validate response structure
                        return self._validate_response(data, endpoint)
                    else:
                        error_text = await response.text()
                        if not suppress_error_logging:
                            logger.error(
                                f"Ollama API error: {response.status} - {error_text}"
                            )
                        raise Exception(
                            f"Ollama API error: {response.status} - {error_text}"
                        )
            except asyncio.TimeoutError:
                if not suppress_error_logging:
                    logger.error(f"Request to {url} timed out")
                raise Exception(f"Request to {url} timed out")
            except Exception as e:
                if not suppress_error_logging:
                    logger.error(f"Failed to connect to Ollama: {str(e)}")
                raise Exception(f"Failed to connect to Ollama: {str(e)}")

    def _validate_response(self, data: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
        """Validate and normalize API response"""
        if not isinstance(data, dict):
            logger.warning(f"Invalid response type from {endpoint}: {type(data)}")
            return {}

        # Handle missing fields gracefully
        if endpoint == "/api/ps":
            # Ensure models field exists
            if "models" not in data:
                logger.warning(
                    f"Missing 'models' field in /api/ps response: {list(data.keys())}"
                )
                data["models"] = []

        elif endpoint == "/api/tags":
            # Ensure models field exists
            if "models" not in data:
                logger.warning(
                    f"Missing 'models' field in /api/tags response: {list(data.keys())}"
                )
                data["models"] = []

        elif endpoint == "/api/show":
            # Ensure required fields exist
            required_fields = ["model", "details", "capabilities"]
            for field in required_fields:
                if field not in data:
                    logger.warning(
                        f"Missing '{field}' field in /api/show response: {list(data.keys())}"
                    )
                    data[field] = "" if field == "model" else {}

        return data

    async def list_models(self) -> List[Model]:
        """List all installed models"""
        try:
            response = await self._make_request("GET", "/api/tags")
            models = []

            for model_data in response.get("models", []):
                model = Model(
                    name=model_data["name"],
                    size=model_data["size"],
                    digest=model_data["digest"],
                    modified_at=datetime.fromisoformat(
                        model_data["modified_at"].replace("Z", "+00:00")
                    ),
                    details=model_data.get("details", {}),
                )
                models.append(model)

            return models
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return []

    async def running_models(self) -> List[RunningModel]:
        """Get currently running models"""
        try:
            response = await self._make_request("GET", "/api/ps")
            logger.debug(f"Ollama /api/ps raw response: {response}")
            running_models = []

            for model_data in response.get("models", []):
                # Handle missing created_at field gracefully
                created_at_str = model_data.get("created_at", "")
                if created_at_str:
                    try:
                        created_at = datetime.fromisoformat(
                            created_at_str.replace("Z", "+00:00")
                        )
                    except ValueError:
                        created_at = datetime.now()
                        logger.warning(
                            f"Invalid timestamp format for {model_data.get('name', 'unknown')}: {created_at_str}"
                        )
                else:
                    created_at = datetime.now()

                name_value = model_data.get("name") or model_data.get("model") or ""
                model_value = model_data.get("model") or model_data.get("name") or ""

                running_models.append(
                    RunningModel(
                        name=name_value,
                        model=model_value,
                        size=model_data.get("size", 0),
                        digest=model_data.get("digest", ""),
                        parent_digest=model_data.get("parent_digest", ""),
                        created_at=created_at,
                    )
                )

            return running_models
        except Exception as e:
            logger.error(f"Error getting running models: {str(e)}")
            return []

    async def warmup_model(self, model_name: str) -> bool:
        """Warmup model by making minimal generate request"""
        try:
            payload = {
                "model": model_name,
                "prompt": "",
                "stream": False,
                "options": {"num_predict": 0, "temperature": 0},
            }

            await self._make_request("POST", "/api/generate", json=payload)
            return True
        except Exception as e:
            logger.error(f"Error warming up model {model_name}: {str(e)}")
            return False

    async def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific model"""
        try:
            response = await self._make_request("GET", f"/api/show?model={model_name}")
            logger.debug(f"Model info response for {model_name}: {response}")
            return response
        except Exception as e:
            error_text = str(e)
            logger.warning(f"Error getting model info for {model_name}: {error_text}")
            if "405" in error_text or "method not allowed" in error_text.lower():
                try:
                    response = await self._make_request(
                        "POST", "/api/show", json={"model": model_name}
                    )
                    logger.debug(
                        f"Model info response for {model_name} via POST /api/show: {response}"
                    )
                    return response
                except Exception as post_error:
                    logger.error(
                        f"POST fallback failed for model info {model_name}: {post_error}"
                    )
            return None

    async def start_model(self, model_name: str, keep_alive: str = "600s") -> bool:
        """Start/load a model and keep it available in Ollama"""
        payload = {
            "model": model_name,
            "prompt": " ",
            "stream": False,
            "keep_alive": keep_alive,
            "options": {"max_tokens": 1, "temperature": 0},
        }
        logger.debug(f"Starting model {model_name} with payload: {payload}")
        try:
            response = await self._make_request("POST", "/api/generate", json=payload)
            logger.debug(f"Start model response for {model_name}: {response}")
            return True
        except Exception as e:
            error_message = f"Failed to start model {model_name}: {str(e)}"
            logger.error(error_message)
            raise Exception(error_message)

    async def stop_model(self, model_name: str) -> bool:
        """Stop a running model (by canceling any active generation)"""
        try:
            # Ollama doesn't have a direct stop endpoint
            # We'll cancel any ongoing generation by sending a cancel request
            payload = {
                "model": model_name,
                "prompt": "",
                "stream": False,
                "keep_alive": "0s",  # This tells Ollama to unload the model immediately
            }

            await self._make_request("POST", "/api/generate", json=payload)
            return True
        except Exception as e:
            logger.error(f"Error stopping model {model_name}: {str(e)}")
            return False

    async def delete_model(self, model_name: str) -> bool:
        """Delete a model from disk"""
        try:
            await self._make_request(
                "DELETE", f"/api/delete", json={"name": model_name}
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting model {model_name}: {str(e)}")
            return False

    async def pull_model(self, model_name: str) -> bool:
        """Pull a new model"""
        try:
            await self._make_request("POST", "/api/pull", json={"name": model_name})
            return True
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {str(e)}")
            return False


# Test function
async def test_client():
    """Test the Ollama client"""
    client = OllamaClient()

    logger.info("Testing Ollama client...")

    # Test list models
    models = await client.list_models()
    logger.info(f"Found {len(models)} models:")
    for model in models[:3]:  # Show first 3
        logger.info(f"  - {model.name} ({model.size / (1024**3):.1f}GB)")

    # Test running models
    running = await client.running_models()
    logger.info(f"Running models: {len(running)}")
    for model in running:
        logger.info(f"  - {model.name}")

    # Test model info
    if models:
        info = await client.get_model_info(models[0].name)
        if info:
            logger.info(f"Model info for {info.name}:")
            logger.info(f"  - Architecture: {info.architecture}")
            logger.info(f"  - Parameters: {info.parameters}")
            logger.info(f"  - Context: {info.context_length}")
            logger.info(f"  - Capabilities: {info.capabilities}")


if __name__ == "__main__":
    asyncio.run(test_client())
