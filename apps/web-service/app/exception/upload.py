"""文件上传业务异常"""

from app.exception.base import BusinessException


class UploadException(BusinessException):
    """文件上传相关业务异常"""

    def __init__(self, message: str):
        super().__init__(message=message)
