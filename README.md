# DM40 蓝牙万用表驱动

用于与 DM40A 数字万用表进行蓝牙通信的 Python 驱动程序。

## 📋 目录
- [功能特性](#功能特性)
- [安装依赖](#安装依赖)
- [获取设备地址](#获取设备地址)
- [使用方法](#使用方法)
- [API 文档](#api-文档)
- [故障排除](#故障排除)

## ✨ 功能特性

- ✅ 蓝牙设备扫描与发现
- ✅ 实时数据读取（电压/电流）
- ✅ 模式切换（电压/电流模式）
- ✅ 后台任务管理
- ✅ 数据更新回调
- ✅ 连接重试机制
- ✅ 异步操作支持

## 📦 安装依赖

```bash
pip install bleak
```

## 🔍 获取设备地址

### 方法 1: 快速扫描 DM40 设备

```bash
python find_dm40.py
```

输出示例：
```
🔍 正在扫描 DM40 系列设备...
============================================================
✅ 发现 1 个 DM40 设备:

设备 1:
  名称: DM40A
  地址: D7:ED:DF:91:FC:4D
  信号强度: -45 dBm
----------------------------------------
📌 使用示例:
device = Com_DM40A(device_addr='D7:ED:DF:91:FC:4D')
```

### 方法 2: 扫描所有蓝牙设备

```bash
python scan_ble_devices.py
```

### 方法 3: 按关键词搜索

```bash
python scan_ble_devices.py --search DM40
python scan_ble_devices.py --search DM40 20  # 扫描20秒
```

## 💻 使用方法

### 基本使用

```python
from dm40ble import Com_DM40A

# 创建设备实例
device = Com_DM40A(device_addr="D7:ED:DF:91:FC:4D")

# 设置数据更新回调
def on_data_update(data, unit):
    print(f"当前读数: {data} {unit}")

device.set_data_update_callback(on_data_update)

# 启动后台任务（每200ms采样一次）
device.run(loop_ms=200)

# 等待连接成功
import time
while device.get_state() != 1:
    time.sleep(0.1)
    if device.get_state() == -1:
        print("连接失败")
        break

# 切换到电压模式
device.set_mode(1)  # 1 = 电压模式

# 切换到电流模式
device.set_mode(2)  # 2 = 电流模式

# 获取当前数据
current_data = device.get_current_data()
print(f"当前值: {current_data}")

# 停止后台任务
device.stop()
```

### 异步使用

```python
import asyncio
from dm40ble import Com_DM40A

async def main():
    async with Com_DM40A("D7:ED:DF:91:FC:4D") as device:
        # 设置电压模式
        await device.set_voltage_mode()

        # 获取数据
        data, unit = await device.get_data()
        print(f"电压: {data} {unit}")

        # 设置电流模式
        await device.set_current_mode()

        data, unit = await device.get_data()
        print(f"电流: {data} {unit}")

asyncio.run(main())
```

### 完整示例

```python
from dm40ble import Com_DM40A
import time

def data_callback(data, unit):
    print(f"📊 实时数据: {data:.2f} {unit}")

# 初始化设备
device = Com_DM40A(
    device_addr="D7:ED:DF:91:FC:4D",
    max_retry=3
)

# 设置回调
device.set_data_update_callback(data_callback)

# 启动后台任务
print("正在连接设备...")
device.run(loop_ms=500)  # 每500ms采样

# 等待连接
while True:
    state = device.get_state()
    if state == 1:
        print("✓ 连接成功!")
        break
    elif state == -1:
        print("✗ 连接失败")
        device.stop()
        exit(1)
    time.sleep(0.1)

# 切换模式并读取数据
try:
    print("\n切换到电压模式...")
    device.set_mode(1)
    time.sleep(2)

    print("\n切换到电流模式...")
    device.set_mode(2)
    time.sleep(2)

    # 保持运行
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n正在停止...")
    device.stop()
    print("完成")
```

## 📖 API 文档

### `Com_DM40A` 类

#### 初始化参数
- `device_addr` (str): 蓝牙设备MAC地址
- `max_retry` (int): 连接重试次数，默认3次

#### 主要方法

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `run(loop_ms)` | 启动后台任务 | 采样间隔(ms) | None |
| `stop()` | 停止后台任务 | - | None |
| `set_data_update_callback(callback)` | 设置数据回调 | 回调函数 | None |
| `get_current_data()` | 获取最新数据 | - | float/None |
| `get_state()` | 获取状态 | - | int (0=空闲, 1=运行中, -1=错误) |
| `set_mode(mode)` | 设置模式 | 1=电压, 2=电流 | None |
| `connect()` | 手动连接 | - | bool |
| `disconnect()` | 断开连接 | - | None |
| `get_data()` | 获取单次数据 | - | (data, unit) |
| `set_voltage_mode()` | 设置电压模式 | - | bool |
| `set_current_mode()` | 设置电流模式 | - | bool |

#### 状态码
- `0`: 空闲/未启动
- `1`: 运行中/已连接
- `-1`: 错误/连接失败

## 🔧 协议说明

### 通信命令
- **获取数据**: `AF 05 03 09 00 40`
- **电压模式**: `AF 05 03 06 01 30 12`
- **电流模式**: `AF 05 03 06 01 39 09`

### 响应格式解析
```
响应数据: [字节0...字节N]
- 字节5: 单位标识
  - 0x30 = mV (毫伏)
  - 0x39 = mA (毫安)

- 字节-8: 缩放系数
  - 0x18 = 0.1
  - 0x19 = -0.1
  - 0x16 = 1
  - 0x17 = -1
  - 0x15 = -0.01
  - 0x14 = 0.01

- 字节-3 和 字节-2: 数据值 (小端序)
  data = byte[-3] | (byte[-2] << 8)

最终值 = data × 缩放系数
```

## 🐛 故障排除

### 问题 1: 蓝牙未开启
**错误**: `Bluetooth device is turned off`

**解决**:
- **macOS**: 系统设置 → 蓝牙 → 开启
- **Linux**: `sudo systemctl start bluetooth`
- **Windows**: 设置 → 蓝牙 → 开启

### 问题 2: 权限不足
**错误**: `Permission denied` 或 `Access denied`

**解决**:
- **Linux**: 使用 `sudo` 运行或添加用户到 `bluetooth` 组
  ```bash
  sudo usermod -a -G bluetooth $USER
  ```
- **macOS**: 系统设置 → 隐私与安全性 → 蓝牙 → 允许终端访问

### 问题 3: 找不到设备
**解决**:
1. 确保 DM40 万用表已开机
2. 确保蓝牙功能已启用
3. 尝试重启万用表
4. 缩短与电脑的距离（< 5米）
5. 确保设备未连接其他设备

### 问题 4: 连接不稳定
**解决**:
- 增加重试次数: `Com_DM40A(max_retry=5)`
- 增加采样间隔: `device.run(loop_ms=1000)`
- 检查电池电量

### 问题 5: 数据解析错误
**解决**:
- 检查设备型号是否为 DM40A
- 打印原始响应: `print(response.hex())`
- 确认 UUID 是否正确

## 📝 注意事项

1. **蓝牙适配器**: 确保电脑有蓝牙适配器
2. **距离**: 设备应在蓝牙范围内（通常<10米）
3. **干扰**: 避免强电磁干扰环境
4. **电量**: 确保万用表电量充足
5. **独占访问**: 确保设备未被其他程序占用

## 📄 许可证

MIT License

## 🔗 相关资源

- [Bleak 文档](https://bleak.readthedocs.io/)
- [DM40 系列说明书](https://www.der ee.com/)
