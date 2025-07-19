import hashlib

def hash_password(password: str) -> str:
    """
    Băm mật khẩu bằng thuật toán SHA-256.
    
    Args:
        password: Mật khẩu dạng chuỗi.
        
    Returns:
        Chuỗi hex đã được băm.
    """
    if not isinstance(password, str):
        return ""
    sha256 = hashlib.sha256()
    sha256.update(password.encode('utf-8'))
    return sha256.hexdigest()