import json
from typing import Optional
import uuid
from fastapi import APIRouter
from litellm import completion
from pydantic import BaseModel
from app.client.pinecone_client import PineconeClient, MemoryItem
from config import settings
from prompts import FACT_RETRIEVAL_PROMPT, get_update_memory_messages
from app.models import Message
from app.logger import logger
from app.client.opensearch_client import OpensearchClient
from config import settings

client = PineconeClient(api_key=settings.PINECONE_API_KEY, index_name=settings.PINECONE_INDEX_NAME)

class MemoryRequest(BaseModel):
    messages: list[Message]
    user_id: str
    lang: Optional[str] = "en"

router = APIRouter()

@router.post("/api/v1/memory/")
async def add_memory(memory_request: MemoryRequest):
    try:
        logger.info(f"Processing memory for user: {memory_request.user_id}")
        
        # 准备消息列表，包含系统提示词
        messages = [
            {"role": "system", "content": FACT_RETRIEVAL_PROMPT},
            *[{"role": msg.role, "content": msg.content} for msg in memory_request.messages]
        ]
        
        # 调用模型提取事实
        response = completion(
            model="openrouter/google/gemini-pro-1.5",
            messages=messages,
            temperature=0.3,
            max_tokens=512,
            response_format={"type": "json_object"},
            metadata={
                "trace_user_id": memory_request.user_id,
            }
        )
        # 从响应中提取事实列表
        try:
            response = response.choices[0].message.content
            try:
                facts_data = [json.loads(response)["fact"]]
            except Exception as e:
                logger.error(f"Error in new_retrieved_facts: {e}")
                facts_data = []
            logger.info(f"Model response: {response}")
            
            # Check if facts array is empty
            if not facts_data:
                return {
                    "status": "success",
                    "message": "No facts to process",
                    "results": []
                }
                
            retrieved_old_memory = []
            for fact in facts_data:
                existing_memories = client.search(query=fact, user_id=memory_request.user_id)
                for existing_memory in existing_memories:
                    retrieved_old_memory.append({"id": existing_memory.id, "text": existing_memory.memory})
            temp_uuid_mapping = {}
            for idx, item in enumerate(retrieved_old_memory):
                temp_uuid_mapping[str(idx)] = item["id"]
                retrieved_old_memory[idx]["id"] = str(idx)
            function_calling_prompt = get_update_memory_messages(retrieved_old_memory, facts_data)
            response = completion(
                model="openrouter/google/gemini-pro-1.5",
                messages=[{"role": "user", "content": function_calling_prompt}],
                temperature=0.3,
                max_tokens=512,
                response_format={"type": "json_object"},
                metadata={
                    "trace_user_id": memory_request.user_id,
                }
            )
            logger.info(f"Model response: {response}")
            new_memories_with_actions = json.loads(response.choices[0].message.content)
            for new_memory_with_action in new_memories_with_actions["memory"]:
                if new_memory_with_action["event"] == "ADD":
                    client.add(memory_item=MemoryItem(
                            id=str(uuid.uuid4()),
                            memory=new_memory_with_action["text"],
                        ), user_id=memory_request.user_id
                    )
                elif new_memory_with_action["event"] == "UPDATE":
                    client.update(
                        id=temp_uuid_mapping[new_memory_with_action["id"]],
                        memory=new_memory_with_action["text"],
                        user_id=memory_request.user_id
                    )
                elif new_memory_with_action["event"] == "DELETE":
                    client.delete(
                        id=temp_uuid_mapping[new_memory_with_action["id"]],
                        user_id=memory_request.user_id
                    )
            return {
                "status": "success", 
                "message": "Memory processed and stored successfully",
                "results": facts_data
            }
            
        except Exception as e:
            logger.error(f"Error parsing model response: {str(e)}")
            return {"status": "error", "message": f"Error parsing model response: {str(e)}"}
            
    except Exception as e:
        logger.error(f"Error processing memory: {str(e)}")
        return {"status": "error", "message": str(e)}


@router.get("/api/v1/memory/{user_id}")
async def search_memory(user_id: str, query: str):
    try:
        logger.info(f"Searching memory for user: {user_id}, query: {query}")
        results = client.search(query, user_id=user_id)
        logger.info("Memory search completed successfully")
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Error searching memory: {str(e)}")
        return {"status": "error", "message": str(e)}

@router.delete("/api/v1/memory/{user_id}")
async def delete_memory_by_user_id(user_id: str):
    try:
        logger.info(f"Deleting all memories for user: {user_id}")
        client.delete_by_user_id(user_id)
        logger.info(f"Successfully deleted all memories for user: {user_id}")
        return {
            "status": "success", 
            "message": f"Successfully deleted all memories",
            "results": ""
        }
    except Exception as e:
        logger.error(f"Error deleting memories for user {user_id}: {str(e)}")
        return {"status": "error", "message": str(e)}

@router.delete("/api/v1/memory/id/{id}")
async def delete_memory_by_id(id: str):
    try:
        logger.info(f"Deleting memory by id: {id}")
        client.delete_by_id(id)
        logger.info(f"Successfully deleted memory by id: {id}")
        return {"status": "success", "message": f"Successfully deleted memory by id: {id}"}
    except Exception as e:
        logger.error(f"Error deleting memory by id: {id}: {str(e)}")
        return {"status": "error", "message": str(e)}