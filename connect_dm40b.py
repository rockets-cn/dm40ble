#!/usr/bin/env python3
"""
专门测试连接 DM40B 设备
"""
import asyncio
from bleak import BleakClient, BleakScanner

# DM40B 的地址（macOS UUID 格式）
DM40B_ADDRESS = "EB31784A-359B-AAF1-E798-76064EA680CD"

# DM40 的服务 UUID
DM40_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
DM40_WRITE_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
DM40_READ_UUID = "0000fff2-0000-1000-8000-00805f9b34fb"

async def connect_dm40b():
    """连接 DM40B 并获取服务信息"""
    print(f"🔍 查找 DM40B: {DM40B_ADDRESS}")

    # 首先确认设备存在
    device = await BleakScanner.find_device_by_address(DM40B_ADDRESS, timeout=10)

    if not device:
        print(f"❌ 未找到设备")
        return None

    print(f"✅ 找到设备: {device.name}")
    print(f"📡 地址: {device.address}")

    # 尝试连接
    print("\n🔗 尝试连接...")
    try:
        client = BleakClient(device, timeout=10)
        await client.connect()
        print("✅ 连接成功!")

        # 列出所有服务
        print("\n📋 发现的服务:")
        for service in client.services:
            print(f"\n  服务: {service.uuid}")
            for char in service.characteristics:
                props = ", ".join(char.properties)
                print(f"    特征: {char.uuid}")
                print(f"      属性: {props}")

                # 检查是否是我们要的特征
                if str(char.uuid) == DM40_WRITE_UUID:
                    print(f"      ⭐ 这是写特征!")
                if str(char.uuid) == DM40_READ_UUID:
                    print(f"      ⭐ 这是读特征!")

        # 设置通知
        print(f"\n📢 设置通知...")
        await client.start_notify(DM40_READ_UUID, lambda s, d: print(f"收到数据: {d.hex()}"))
        print("✅ 通知设置成功")

        # 发送读取命令
        print(f"\n📤 发送读取命令...")
        cmd = bytes([0xaf, 0x05, 0x03, 0x09, 0x00, 0x40])
        await client.write_gatt_char(DM40_WRITE_UUID, cmd)
        print("✅ 命令发送成功")

        # 等待响应
        print("\n⏳ 等待响应 (5秒)...")
        await asyncio.sleep(5)

        # 断开连接
        await client.stop_notify(DM40_READ_UUID)
        await client.disconnect()
        print("\n✅ 测试完成")

        return DM40B_ADDRESS

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(connect_dm40b())

    if result:
        print(f"\n📌 更新 dm40ble.py:")
        print(f'  device = Com_DM40A(device_addr="{result}")')
