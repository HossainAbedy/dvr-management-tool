import os

class Config:
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    DEFAULT_NTP = os.getenv('DEFAULT_NTP', '172.19.11.170')