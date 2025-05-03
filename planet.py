import asyncio
import aiohttp
import requests

async def get_planet_async(api_key, name):
    async with aiohttp.ClientSession() as session:
        url = f"https://api.api-ninjas.com/v1/planets?name={name}"
        async with session.get(url, headers={'X-Api-Key': api_key}) as response:
            if response.status == 200:
                data = await response.json()
                return data[0] if data else None
            return None

def get_planet_sync(api_key, name):
    response = requests.get(
        f"https://api.api-ninjas.com/v1/planets?name={name}",
        headers={'X-Api-Key': api_key}
    )
    if response.status_code == 200:
        data = response.json()
        return data[0] if data else None
    return None

def display_planet(planet):
    if not planet:
        print("Данные о планете не получены")
        return
    
    print("\n=== Информация о планете ===")
    print(f"Название: {planet.get('name', 'N/A')}")
    print(f"Масса (отн. Юпитера): {planet.get('mass', 'N/A')}")
    print(f"Радиус (отн. Юпитера): {planet.get('radius', 'N/A')}")
    print(f"Период обращения (дни): {planet.get('period', 'N/A')}")
    print(f"Большая полуось (а.е.): {planet.get('semi_major_axis', 'N/A')}")
    print(f"Температура (K): {planet.get('temperature', 'N/A')}")
    print(f"Расстояние (св. годы): {planet.get('distance_light_year', 'N/A')}")

async def main():
    api_key = input("Введите API ключ: ")
    name = input("Введите название планеты (например Neptune): ")

    print("\nСинхронный запрос:")
    sync_data = get_planet_sync(api_key, name)
    display_planet(sync_data)

    print("\nАсинхронный запрос:")
    async_data = await get_planet_async(api_key, name)
    display_planet(async_data)

if __name__ == "__main__":
    asyncio.run(main())