import json
import os

import httpx
from fastapi import FastAPI, HTTPException, Request
import redis.asyncio as redis
from starlette.responses import JSONResponse

app = FastAPI()

pool = redis.ConnectionPool(host='redis', port=6379, password='8QQnjhHdnAj9ZgVpB5AZSDpZCHpLne')


REMOTE_URL = os.environ.get('REMOTE_URL')


async def get_cache_key(partner_id: int, auth_key: str) -> str:
    if partner_id is None or auth_key is None:
        raise HTTPException(status_code=401, detail="Not auth key or id provided")
    return f"{partner_id}_{auth_key}"


@app.get("/api/v1/bet_insights/partner-sports")
async def proxy(request: Request):
    partner_id = request.headers.get("Partner-id")
    authorization = request.headers.get("Authorization")
    cache_key = await get_cache_key(partner_id=partner_id, auth_key=authorization)
    redis_client = redis.Redis.from_pool(pool)

    cached_response = await redis_client.get(cache_key)

    if cached_response:
        return JSONResponse(status_code=200, content=json.loads(cached_response))

    headers = {"Partner-Id": partner_id, "Authorization": authorization}
    async with httpx.AsyncClient() as client:
        response = await client.get(REMOTE_URL, headers=headers)
        if response.status_code == 200:
            await redis_client.set(name=cache_key, value=json.dumps(response.json()))

        return JSONResponse(status_code=response.status_code, content=response.content, headers=response.headers)
