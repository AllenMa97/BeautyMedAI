from pydantic import BaseModel, validator

class SafeSchema(BaseModel):
    @validator('components', each_item=True)
    def check_xss(cls, v):
        if 'script' in v.get('props', {}):
            raise ValueError("XSS攻击特征检测")
        return v