from loguru import logger
import sys

# 1. 移除默认的输出配置
logger.remove()

# 2. 配置控制台输出（彩色、格式化）
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{extra[request_id]}</level> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",
    colorize=True,
)

# 3. 输出日志
logger.bind(request_id="abc-123", user="admin").info("开始处理请求")
