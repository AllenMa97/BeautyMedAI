"""
后端服务启动脚本
"""

import argparse
import uvicorn
import sys
import os
from app.main import app


def main():
    parser = argparse.ArgumentParser(description='Lansee Backend Services')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=3003, help='Port to bind to')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    parser.add_argument('--workers', type=int, default=1, help='Number of worker processes')
    
    args = parser.parse_args()
    
    print(f"Starting Lansee Backend Services on {args.host}:{args.port}")
    print(f"Auto-reload: {'Enabled' if args.reload else 'Disabled'}")
    print(f"Workers: {args.workers}")
    
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,  # 不支持reload和workers一起使用
        log_level="info"
    )


if __name__ == "__main__":
    main()