#!/usr/bin/env python3
"""
获取 macOS 上已配对的蓝牙设备 UUID
"""
import asyncio
from bleak import BleakScanner
from Foundation import NSBundle
import CoreBluetooth

async def find_paired_dm40():
    """查找已配对的 DM40 设备"""
    print("🔍 扫描已配对的 DM40 设备...")
    print("=" * 60)

    # 扫描设备
    devices = await BleakScanner.discover(timeout=10, return_adv=True)

    dm40_candidates = []

    for device, adv_data in devices.items():
        try:
            address = device.address
        except AttributeError:
            address = str(device)

        # 尝试连接每个设备并读取名称
        try:
            async with BleakClient(address, timeout=2) as client:
                try:
                    name_bytes = await client.read_gatt_char("00002a00-0000-1000-8000-00805f9b34fb")
                    name = name_bytes.decode('utf-8', errors='ignore').strip('\x00')

                    if "DM40" in name.upper() or "C-1-ATK" in name.upper():
                        dm40_candidates.append({
                            'name': name,
                            'address': address
                        })
                        print(f"✅ 找到: {name}")
                        print(f"   地址: {address}")
                except:
                    pass
        except:
            pass

    if dm40_candidates:
        print(f"\n📌 使用第一个设备的地址:")
        print(f"  device = Com_DM40A(device_addr='{dm40_candidates[0]['address']}')")
    else:
        print("\n❌ 未找到 DM40 设备")

if __name__ == "__main__":
    asyncio.run(find_paired_dm40())
