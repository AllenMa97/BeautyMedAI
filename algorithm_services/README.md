# 启动说明

## Windows系统启动简易说明
python解析器 main.py -m uvicorn services.main:app --reload
比如：
"C:\python.exe" "C:\hc_dao_vibe_algorithm\services\main.py" -m uvicorn services.main:app --reload 
也可以不填脚本启动参数，但是记得把uvicorn的Reload关掉


## Linux系统启动简易说明
- 激活conda环境（若需要）：  conda activate haici
- 进入项目根目录：     cd /home/allen/lansee_chatbot/algorithm_services
- 启动服务（用于生产, 日志重定向到文件）：./fastapi_service.sh start
- 启动服务（用于调试，退出调试直接Ctrl+C）./fastapi_service.sh debug
- 停止服务（停止任意模式的服务）：./fastapi_service.sh stop
- 重启服务（重启生产模式服务）：./fastapi_service.sh restart
- 小技巧：调试时查看历史日志
  ```shell
    # 实时跟踪生产模式标准日志
    tail -f /home/allen/lansee_chatbot/logs/fastapi_service.log
    # 实时跟踪生产模式错误日志
    tail -f /home/allen/lansee_chatbot/logs/fastapi_service_err.log
  ```
- 
---

# 架构层次简易说明

## 对研究者：
- core/models/ 对应 机器学习或业务规则模型（算法实体）
- core/processors/清晰对应模型与数据处理流程，
- data/ 对应 管理实验状态。

## 对 Spring Boot 开发者：
- api/routers/ 对应 Controller，
- core/services/ 对应 Service，
- data/ 对应 Repository，
- config/ 对应 Configuration。
- api/schemas 对应 Web 数据模型（Pydantic DTO）也对应 @RequestBody的 DTO 类（放在 dto/或 request/包） 

---
# 其他
## 服务默认端口：6732
## 设计相关的文档见working_manuscript内