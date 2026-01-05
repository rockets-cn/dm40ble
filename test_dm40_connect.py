#!/usr/bin/env python3
"""
直接测试连接 DM40
"""
import asyncio
from bleak import BleakClient

DM40_ADDRESS = "A7:CD:DA:CC:60:05"

async def test_connect():
    """测试连接 DM40"""
    print(f"尝试连接 DM40: {DM40_ADDRESS}")
    print("=" * 60)

    try:
        async with BleakClient(DM40_ADDRESS) as client:
            print("✅ 连接成功!")

            # 获取服务
            print("\n📋 发现的服务:")
            for service in client.services:
                print(f"  服务: {service.uuid}")
                for char in service.characteristics:
                    print(f"    特征: {char.uuid}")

            # 读取设备名称
            try:
                name = await client.read_gatt_char("00002a00-0000-1000-8000-00805f9b34fb")
                device_name = name.decode('utf-8', errors='ignore')
                print(f"\n📌 设备名称: {device_name}")
            except Exception as e:
                print(f"\n⚠️ 无法读取设备名称: {e}")

            return True

    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connect())
