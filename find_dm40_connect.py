#!/usr/bin/env python3
"""
通过连接尝试查找 DM40 设备
"""
import asyncio
from bleak import BleakClient, BleakScanner

# DM40 的服务 UUID
SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"

async def try_connect_to_device(address, timeout=3):
    """尝试连接设备并检查是否是 DM40"""
    try:
        async with BleakClient(address, timeout=timeout) as client:
            # 尝试获取设备名称
            try:
                name = await client.read_gatt_char("00002a00-0000-1000-8000-00805f9b34fb")
                device_name = name.decode('utf-8', errors='ignore')
            except:
                device_name = None

            # 检查设备名称是否包含 DM40
            if device_name and "DM40" in device_name.upper():
                # 检查是否有 DM40 的服务
                services = client.services
                service_uuids = [str(s.uuid) for s in services]

                return {
                    'address': address,
                    'name': device_name,
                    'is_dm40': True,
                    'services': service_uuids
                }
            # 返回名称以便调试
            return {'found': False, 'name': device_name}
    except Exception as e:
        return {'found': False, 'error': str(e)[:50]}

async def find_dm40_by_connecting():
    """通过连接查找 DM40 设备"""
    print("🔍 正在扫描并尝试连接查找 DM40 设备...")
    print("=" * 60)

    # 先扫描所有设备
    devices = await BleakScanner.discover(timeout=5, return_adv=True)

    print(f"📡 发现 {len(devices)} 个设备，开始逐个连接检查...\n")

    # 按信号强度排序（先检查信号强的）
    device_list = []
    for device, adv_data in devices.items():
        try:
            rssi = adv_data.rssi
        except AttributeError:
            rssi = -100

        try:
            address = device.address
        except AttributeError:
            address = str(device)

        device_list.append((address, rssi))

    # 按信号强度排序（从强到弱）
    device_list.sort(key=lambda x: x[1], reverse=True)

    # 只检查前 20 个信号最强的设备
    found_names = []
    for i, (address, rssi) in enumerate(device_list[:20], 1):
        print(f"[{i}/20] 尝试连接 {address}...", end=" ", flush=True)

        result = await try_connect_to_device(address)

        if result and result.get('is_dm40'):
            print(f"✅ 找到 DM40!")
            print(f"\n设备信息:")
            print(f"  名称: {result['name']}")
            print(f"  地址: {result['address']}")
            print(f"\n📌 使用方法:")
            print(f'  device = Com_DM40A(device_addr="{result["address"]}")')
            return result['address']
        else:
            # 显示找到的设备名称
            name = result.get('name')
            if name:
                print(f"名称: {name}")
                found_names.append(name)
            else:
                error = result.get('error', '')
                print(f"❌ {error if error else '无法读取名称'}")

    print(f"\n❌ 未找到 DM40 设备")
    if found_names:
        print(f"\n📋 成功读取的设备名称:")
        for n in found_names:
            print(f"  - {n}")
    print("\n提示:")
    print("1. 确保 DM40 万用表已开机")
    print("2. 确保 DM40 的蓝牙功能已开启")
    print("3. 尝试将万用表靠近电脑")

if __name__ == "__main__":
    try:
        asyncio.run(find_dm40_by_connecting())
    except KeyboardInterrupt:
        print("\n\n扫描被中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
