"""
start.py - 前后端一键启动脚本
用法: python start.py
"""
import os
import sys
import time
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / 'backend'
FRONTEND_DIR = ROOT / 'frontend'

# ---- 讯飞星火凭证（已从 start.bat 同步）----
os.environ.setdefault('SPARK_APP_ID',     '9a9b6842')
os.environ.setdefault('SPARK_API_KEY',    '407868b0a52da90db7235bac75423232')
os.environ.setdefault('SPARK_API_SECRET', 'ZWEyYjM3ZDU5MWJiNTM2MDE0MWY1YTI3')

# ====================================================
# 工具函数
# ====================================================

def check(cmd: str, name: str) -> bool:
    try:
        subprocess.run(cmd, shell=True, capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f'[错误] 未找到 {name}，请先安装后再运行。')
        return False


def start_process(title: str, cmd: str, cwd: Path) -> subprocess.Popen:
    """在新窗口中启动进程（Windows 使用 start /新窗口）"""
    full_cmd = f'start "{title}" cmd /k "{cmd}"'
    proc = subprocess.Popen(full_cmd, shell=True, cwd=str(cwd), env=os.environ.copy())
    return proc


# ====================================================
# 主流程
# ====================================================

def main():
    print('=' * 44)
    print('  销售数据分析预测系统')
    print('=' * 44)
    print()

    # 环境检查
    print('[1/3] 检查 Python 环境...')
    if not check('python --version', 'Python 3.9+'):
        sys.exit(1)

    print('[2/3] 检查 Node 环境...')
    if not check('node --version', 'Node.js 16+'):
        sys.exit(1)

    print('[3/3] 启动服务...')
    print()

    # 启动后端
    print('[后端] 启动 Django 开发服务器 -> http://127.0.0.1:8000')
    start_process(
        title='后端 - Django',
        cmd=f'python manage.py runserver',
        cwd=BACKEND_DIR,
    )

    # 等待后端初始化
    time.sleep(3)

    # 启动前端
    print('[前端] 启动 Vue 开发服务器  -> http://localhost:8080')
    start_process(
        title='前端 - Vue',
        cmd='npm run serve',
        cwd=FRONTEND_DIR,
    )

    print()
    print('=' * 44)
    print('  服务已在后台窗口启动：')
    print('    后端: http://127.0.0.1:8000')
    print('    前端: http://localhost:8080')
    print('=' * 44)
    print('  关闭对应窗口即可停止相应服务。')
    input('\n按 Enter 退出此窗口...')


if __name__ == '__main__':
    main()
