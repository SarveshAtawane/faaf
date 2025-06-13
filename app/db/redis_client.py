import redis.asyncio as redis
import ssl

redis_client = redis.Redis(
    host='redis-18623.crce182.ap-south-1-1.ec2.redns.redis-cloud.com',
    port=18623,
    decode_responses=True,
    username="default",
    password="WPxoZWafvFo0sT2sQrcrcX3so6lUGMS8",
    ssl_cert_reqs=None,  # This handles SSL for Redis Cloud
)