#!/usr/bin/env python3
"""
直接测试连接到 DM40 设备
"""
import asyncio
from bleak import BleakClient, BleakScanner

async def test_direct_connect():
    """测试直接连接"""
    # 原来的 MAC 地址
    target_address = "A7:CD:DA:CC:60:05"

    print(f"🔍 尝试查找设备: {target_address}")
    print("-" * 50)

    # 首先尝试通过地址查找
    device = await BleakScanner.find_device_by_address(target_address, timeout=10)

    if device:
        print(f"✅ 找到设备: {device}")
        print(f"   设备名称: {device.name if hasattr(device, 'name') else '未知'}")
        print(f"   设备地址: {device.address if hasattr(device, 'address') else target_address}")

        # 尝试连接
        print("\n🔗 尝试连接...")
        try:
            async with BleakClient(device) as client:
                print("✅ 连接成功!")

                # 列出所有服务
                print("\n📋 发现的服务:")
                for service in client.services:
                    print(f"  服务: {service.uuid}")
                    for char in service.characteristics:
                        print(f"    特征: {char.uuid} (属性: {char.properties})")
        except Exception as e:
            print(f"❌ 连接失败: {e}")
    else:
        print(f"❌ 未找到设备: {target_address}")
        print("\n💡 可能的原因:")
        print("1. DM40 万用表未开机")
        print("2. DM40 蓝牙功能未开启")
        print("3. 设备不在范围内")
        print("4. 设备地址已变更 (macOS 设备地址是 UUID 格式)")
        print("\n🔍 让我尝试扫描所有设备...")

        # 扫描所有设备
        devices = await BleakScanner.discover(timeout=5)
        print(f"\n📡 发现 {len(devices)} 个设备:")
        for i, d in enumerate(devices[:20], 1):
            name = d.name if hasattr(d, 'name') else "未知"
            addr = d.address if hasattr(d, 'address') else str(d)
            print(f"  {i}. {name} - {addr}")

if __name__ == "__main__":
    asyncio.run(test_direct_connect())
