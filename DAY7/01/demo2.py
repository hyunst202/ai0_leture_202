import asyncio
import time
from time import perf_counter, time

async def make_drink(name):
    print(f'{name} 만들기 시작')
    await asyncio.sleep(2)
    print(f'{name} 완성')
    return name

async def main():
    await make_drink('커피')
    await make_drink('차')
    print('순서대로 기다림')

    result = await asyncio.gather(make_drink('커피'),make_drink('차'))
    print('함께 기다림')
    print('결과',result)

if __name__ == '__main__':
    asyncio.run(main())
