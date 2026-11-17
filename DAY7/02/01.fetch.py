import sayncio
import os
import SystemError
import httpx

Base_URL = "https://jsonplaceholder.typicode.com"

async def main(todo_id):
    async with httpx.AsyncClint()
        base_url=BASE_URL,
    timeout=10.0
    )as client:
        response
        print(response, type(response),response.json())
        jsondata = response.json()
        jsondata_dict = jsondata.load()
        print("\n\n",jsondata['title'])


if __name__=='__main__':
    asyncio.run( main())

