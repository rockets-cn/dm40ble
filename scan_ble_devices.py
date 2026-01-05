#!/usr/bin/env python3
"""
蓝牙设备扫描脚本
用于扫描周围的BLE设备并显示它们的地址和名称
"""

import asyncio
from bleak import BleakScanner
import sys

async def scan_ble_devices(timeout=10):
    """
    扫描蓝牙设备

    Args:
        timeout: 扫描时间（秒）

    Returns:
        list: 发现的设备列表，每个设备包含地址和名称
    """
    print(f"开始扫描蓝牙设备... (扫描时间: {timeout}秒)")
    print("-" * 60)

    # 开始扫描
    devices = await BleakScanner.discover(timeout=timeout, return_adv=True)

    device_list = []

    for device, adv_data in devices.items():
        if device.name:  # 只显示有名称的设备
            device_info = {
                'address': device.address,
                'name': device.name,
                'rssi': adv_data.rssi if adv_data else -1
            }
            device_list.append(device_info)

            print(f"设备名称: {device_info['name']}")
            print(f"MAC地址: {device_info['address']}")
            print(f"信号强度: {device_info['rssi']} dBm")
            print("-" * 60)

    if not device_list:
        print("未发现任何蓝牙设备")
        print("可能的原因:")
        print("1. 蓝牙未开启")
        print("2. 没有BLE设备在广播")
        print("3. 权限不足（Linux需要sudo，macOS需要系统权限）")

    return device_list

async def scan_for_specific_device(device_name_keyword, timeout=15):
    """
    扫描特定名称的设备

    Args:
        device_name_keyword: 设备名称关键字
        timeout: 扫描时间
    """
    print(f"正在搜索包含 '{device_name_keyword}' 的设备...")
    print("-" * 60)

    devices = await BleakScanner.discover(timeout=timeout, return_adv=True)

    for device, adv_data in devices.items():
        if device.name and device_name_keyword.lower() in device.name.lower():
            print(f"✓ 找到目标设备!")
            print(f"  名称: {device.name}")
            print(f"  地址: {device.address}")
            print(f"  信号强度: {adv_data.rssi if adv_data else 'N/A'} dBm")
            return device.address

    print(f"✗ 未找到包含 '{device_name_keyword}' 的设备")
    return None

def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 模式1: 搜索特定设备
        if sys.argv[1] == "--search":
            if len(sys.argv) < 3:
                print("用法: python scan_ble_devices.py --search <设备名称关键词>")
                sys.exit(1)
            keyword = sys.argv[2]
            timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 15
            asyncio.run(scan_for_specific_device(keyword, timeout))
        else:
            print("未知参数")
            print("用法:")
            print("  python scan_ble_devices.py                    # 扫描所有设备")
            print("  python scan_ble_devices.py --search DM40      # 搜索DM40设备")
            print("  python scan_ble_devices.py --search DM40 20   # 搜索20秒")
    else:
        # 模式2: 扫描所有设备
        try:
            asyncio.run(scan_ble_devices(timeout=10))
        except KeyboardInterrupt:
            print("\n扫描被用户中断")
        except Exception as e:
            print(f"扫描出错: {e}")
            print("\n可能的解决方案:")
            print("- 确保蓝牙已开启")
            print("- Linux: 尝试使用 sudo 运行")
            print("- macOS: 确保终端有蓝牙权限")
            print("- Windows: 确保蓝牙服务已启动")

if __name__ == "__main__":
    main()
