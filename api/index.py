"""Vercel Serverless 入口 — 万年历 Flask 应用"""

import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入 Flask app — Vercel Python runtime 会自动检测并作为 WSGI 应用运行
from src.webapp import app

# Vercel 需要一个名为 'app' 的 WSGI 应用变量
# Flask(__name__) 返回的实例即是 WSGI 兼容的
