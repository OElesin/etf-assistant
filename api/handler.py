"""
AWS Lambda handler for FastAPI application
"""

from mangum import Mangum
from api.main import app

# Create Lambda handler
handler = Mangum(app, lifespan="off")