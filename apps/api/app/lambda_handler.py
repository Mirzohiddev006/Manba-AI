"""Serverless varianti (ADR-001): Mangum adapteri."""

from mangum import Mangum

from .main import app

handler = Mangum(app)
