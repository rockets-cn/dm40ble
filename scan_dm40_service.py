#!/usr/bin/env python3
"""
通过 DM40 的服务 UUID 查找设备
"""
import asyncio
from bleak import BleakClient, BleakScanner

# DM40 的服务 UUID
DM40_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"

async def scan_for_dm40_service():
    """扫描并查找具有 DM40 服务的设备"""
    print("🔍 正在扫描具有 DM40 服务的蓝牙设备...")
    print("=" * 60)

    # 扫描所有设备
    devices = await BleakScanner.discover(timeout=10)

    print(f"📡 发现 {len(devices)} 个设备\n")

    found_candidates = []

    for i, device in enumerate(devices, 1):
        name = device.name if hasattr(device, 'name') and device.name else "未知"
        addr = device.address if hasattr(device, 'address') else str(device)

        print(f"[{i}/{len(devices)}] 检查 {name} ({addr[:38]}...)...", end=" ", flush=True)

        # 尝试连接并检查服务
        try:
            async with BleakClient(device, timeout=3) as client:
                # 获取所有服务
                service_uuids = [str(s.uuid) for s in client.services]

                # 检查是否有 DM40 的服务
                if DM40_SERVICE_UUID in service_uuids:
                    print("✅ 找到 DM40 设备!")
                    found_candidates.append({
                        'name': name,
                        'address': addr,
                        'services': service_uuids
                    })
                else:
                    # 显示找到的服务以便调试
                    if service_uuids:
                        print(f"无 (服务: {len(service_uuids)} 个)")
                    else:
                        print("无服务")

        except Exception as e:
            error_msg = str(e)[:40]
            print(f"❌ {error_msg}")

    # 输出结果
    print("\n" + "=" * 60)
    if found_candidates:
        print(f"✅ 找到 {len(found_candidates)} 个 DM40 设备:\n")
        for i, dev in enumerate(found_candidates, 1):
            print(f"设备 {i}:")
            print(f"  名称: {dev['name']}")
            print(f"  地址: {dev['address']}")
            print(f"  服务数量: {len(dev['services'])}")
            print(f"\n📌 更新 dm40ble.py:")
            print(f"  device = Com_DM40A(device_addr=\"{dev['address']}\")")
            print("-" * 50)
    else:
        print("❌ 未找到 DM40 设备")
        print("\n提示:")
        print("1. 确保 DM40 万用表已开机")
        print("2. 确保 DM40 的蓝牙功能已开启")
        print("3. 尝试将万用表靠近电脑")
        print("4. 尝试重启万用表的蓝牙功能")

if __name__ == "__main__":
    try:
        asyncio.run(scan_for_dm40_service())
    except KeyboardInterrupt:
        print("\n扫描被中断")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
