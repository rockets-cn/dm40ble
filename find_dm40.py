#!/usr/bin/env python3
"""
快速查找 DM40 系列蓝牙万用表
"""

import asyncio
from bleak import BleakScanner

async def find_dm40_device():
    """查找 DM40 设备"""
    print("🔍 正在扫描 DM40 系列设备...")
    print("=" * 60)

    devices = await BleakScanner.discover(timeout=10, return_adv=True)

    dm40_devices = []
    all_devices = []

    for device, adv_data in devices.items():
        # macOS 兼容性处理：尝试从不同位置获取设备名称
        try:
            name = device.name
        except AttributeError:
            try:
                name = adv_data.local_name if adv_data else None
            except AttributeError:
                name = None

        if not name:
            name = "未知"

        # 获取设备地址（macOS 兼容）
        try:
            address = device.address
        except AttributeError:
            try:
                address = str(device)
            except AttributeError:
                address = "未知地址"

        # 获取信号强度（macOS 兼容）
        try:
            rssi = adv_data.rssi
        except AttributeError:
            try:
                rssi = adv_data[1].rssi if adv_data and len(adv_data) > 1 else -1
            except (AttributeError, IndexError):
                rssi = -1

        all_devices.append({
            'name': name,
            'address': address,
            'rssi': rssi
        })

        # 检查是否是 DM40 系列
        if "DM40" in name.upper() or "DM4" in name.upper():
            dm40_devices.append({
                'name': name,
                'address': address,
                'rssi': rssi
            })

    print(f"📡 总共发现 {len(all_devices)} 个蓝牙设备\n")

    if dm40_devices:
        print(f"✅ 发现 {len(dm40_devices)} 个 DM40 设备:\n")
        for i, dev in enumerate(dm40_devices, 1):
            print(f"设备 {i}:")
            print(f"  名称: {dev['name']}")
            print(f"  地址: {dev['address']}")
            print(f"  信号强度: {dev['rssi']} dBm")
            print("-" * 40)

        # 显示如何使用第一个设备
        print("\n📌 使用示例:")
        print(f"device = Com_DM40A(device_addr='{dm40_devices[0]['address']}')")
    else:
        print("❌ 未发现 DM40 设备")
        print("\n📋 发现的所有设备:")
        for i, dev in enumerate(all_devices[:10], 1):  # 只显示前10个
            print(f"  {i}. {dev['name']} ({dev['address']}) - {dev['rssi']} dBm")

        print("\n排查建议:")
        print("1. 确保 DM40 万用表已开机")
        print("2. 确保蓝牙功能已开启")
        print("3. 确保设备处于可发现模式")
        print("4. 尝试重新启动万用表的蓝牙")
        print("5. 缩短与电脑的距离")

if __name__ == "__main__":
    try:
        asyncio.run(find_dm40_device())
    except KeyboardInterrupt:
        print("\n扫描被中断")
    except Exception as e:
        print(f"错误: {e}")
        print("\n请确保:")
        print("- 已安装 bleak: pip install bleak")
        print("- 系统蓝牙已开启")
        print("- 有蓝牙适配器")
