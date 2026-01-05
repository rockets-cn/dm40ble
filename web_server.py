"""
DM40A 蓝牙万用表实时数据 Web 服务器
支持多种测量模式：直流/交流电压、直流/交流电流、电阻、电容、频率、温度等
"""
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import threading
import time
from dm40ble import Com_DM40A

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dm40a-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局变量
dm40_device = None
current_data = {"value": None, "unit": "", "mode": "", "status": "disconnected"}


def data_update_callback(data, unit, mode):
    """数据更新回调函数"""
    global current_data
    current_data["value"] = data
    current_data["unit"] = unit
    current_data["mode"] = mode
    # 通过 WebSocket 推送数据到前端
    socketio.emit('data_update', {
        'value': data,
        'unit': unit,
        'mode': mode,
        'timestamp': time.time()
    })


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """获取当前状态 API"""
    return jsonify(current_data)


@app.route('/api/connect', methods=['POST'])
def connect_device():
    """连接设备"""
    global dm40_device, current_data
    try:
        if dm40_device is None:
            dm40_device = Com_DM40A()
            dm40_device.set_data_update_callback(data_update_callback)
            dm40_device.run(200)
            current_data["status"] = "connecting"
        return jsonify({'status': 'ok', 'message': '正在连接设备...'})
    except Exception as e:
        current_data["status"] = "error"
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/disconnect', methods=['POST'])
def disconnect_device():
    """断开设备"""
    global dm40_device, current_data
    try:
        if dm40_device:
            dm40_device.stop()
            dm40_device = None
        current_data = {"value": None, "unit": "", "mode": "", "status": "disconnected"}
        return jsonify({'status': 'ok', 'message': '已断开连接'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== 电压模式 ====================

@app.route('/api/mode/dc_voltage', methods=['POST'])
def set_dc_voltage_mode():
    """设置直流电压模式"""
    global dm40_device
    try:
        if dm40_device:
            dm40_device.set_mode(Com_DM40A.MODE_DC_VOLTAGE)
            return jsonify({'status': 'ok', 'message': '已切换到直流电压模式'})
        return jsonify({'status': 'error', 'message': '设备未连接'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/mode/ac_voltage', methods=['POST'])
def set_ac_voltage_mode():
    """设置交流电压模式"""
    global dm40_device
    try:
        if dm40_device:
            dm40_device.set_mode(Com_DM40A.MODE_AC_VOLTAGE)
            return jsonify({'status': 'ok', 'message': '已切换到交流电压模式'})
        return jsonify({'status': 'error', 'message': '设备未连接'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== 电流模式 ====================

@app.route('/api/mode/dc_current', methods=['POST'])
def set_dc_current_mode():
    """设置直流电流模式"""
    global dm40_device
    try:
        if dm40_device:
            dm40_device.set_mode(Com_DM40A.MODE_DC_CURRENT)
            return jsonify({'status': 'ok', 'message': '已切换到直流电流模式'})
        return jsonify({'status': 'error', 'message': '设备未连接'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/mode/ac_current', methods=['POST'])
def set_ac_current_mode():
    """设置交流电流模式"""
    global dm40_device
    try:
        if dm40_device:
            dm40_device.set_mode(Com_DM40A.MODE_AC_CURRENT)
            return jsonify({'status': 'ok', 'message': '已切换到交流电流模式'})
        return jsonify({'status': 'error', 'message': '设备未连接'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== 其他测量模式 ====================

@app.route('/api/mode/resistance', methods=['POST'])
def set_resistance_mode():
    """设置电阻模式"""
    global dm40_device
    try:
        if dm40_device:
            dm40_device.set_mode(Com_DM40A.MODE_RESISTANCE)
            return jsonify({'status': 'ok', 'message': '已切换到电阻模式'})
        return jsonify({'status': 'error', 'message': '设备未连接'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/mode/capacitance', methods=['POST'])
def set_capacitance_mode():
    """设置电容模式"""
    global dm40_device
    try:
        if dm40_device:
            dm40_device.set_mode(Com_DM40A.MODE_CAPACITANCE)
            return jsonify({'status': 'ok', 'message': '已切换到电容模式'})
        return jsonify({'status': 'error', 'message': '设备未连接'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/mode/frequency', methods=['POST'])
def set_frequency_mode():
    """设置频率模式"""
    global dm40_device
    try:
        if dm40_device:
            dm40_device.set_mode(Com_DM40A.MODE_FREQUENCY)
            return jsonify({'status': 'ok', 'message': '已切换到频率模式'})
        return jsonify({'status': 'error', 'message': '设备未连接'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/mode/temperature', methods=['POST'])
def set_temperature_mode():
    """设置温度模式"""
    global dm40_device
    try:
        if dm40_device:
            dm40_device.set_mode(Com_DM40A.MODE_TEMPERATURE)
            return jsonify({'status': 'ok', 'message': '已切换到温度模式'})
        return jsonify({'status': 'error', 'message': '设备未连接'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/mode/diode', methods=['POST'])
def set_diode_mode():
    """设置二极管模式"""
    global dm40_device
    try:
        if dm40_device:
            dm40_device.set_mode(Com_DM40A.MODE_DIODE)
            return jsonify({'status': 'ok', 'message': '已切换到二极管模式'})
        return jsonify({'status': 'error', 'message': '设备未连接'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/mode/continuity', methods=['POST'])
def set_continuity_mode():
    """设置通断模式"""
    global dm40_device
    try:
        if dm40_device:
            dm40_device.set_mode(Com_DM40A.MODE_CONTINUITY)
            return jsonify({'status': 'ok', 'message': '已切换到通断模式'})
        return jsonify({'status': 'error', 'message': '设备未连接'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== 兼容旧 API ====================

@app.route('/api/mode/voltage', methods=['POST'])
def set_voltage_mode():
    """设置电压模式（兼容旧代码，默认直流）"""
    return set_dc_voltage_mode()


@app.route('/api/mode/current', methods=['POST'])
def set_current_mode():
    """设置电流模式（兼容旧代码，默认直流）"""
    return set_dc_current_mode()


# ==================== WebSocket 事件 ====================

@socketio.on('connect')
def handle_connect():
    """WebSocket 连接处理"""
    emit('connected', {'data': 'WebSocket connected'})
    # 发送当前数据
    emit('data_update', current_data)


@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket 断开处理"""
    print('Client disconnected')


if __name__ == '__main__':
    port = 5001
    print("DM40A Web 服务器启动中...")
    print("支持模式: 直流/交流电压、直流/交流电流、电阻、电容、频率、温度、二极管、通断")
    print(f"请打开浏览器访问: http://localhost:{port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)
