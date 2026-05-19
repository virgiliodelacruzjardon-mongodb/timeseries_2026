# Setup
# python3 -m venv venv
# source venv/bin/activate
# python3 -m pip install pymongo

import os
import random
import time
from datetime import datetime, timedelta

from pymongo import MongoClient

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError("Please set the MONGODB_URI environment variable.")

client = MongoClient(MONGODB_URI)
db = client["timeseries_poc"]

# Collections
ts_collection = db["sensor_data_timeseries"]
normal_collection = db["sensor_data_normal"]

# Drop existing collections
ts_collection.drop()
normal_collection.drop()

# Create Time Series Collection
db.create_collection(
    "sensor_data_timeseries",
    timeseries={
        "timeField": "timestamp",
        "metaField": "metadata",
        "granularity": "seconds",  # Options: seconds, minutes, hours
    },
)

print("✅ Collections created\n")

# ==========================================
# 1. DATA INSERTION
# ==========================================

def generate_sensor_data(num_records=10000):
    """Generate sample IoT sensor data."""
    data = []
    start_time = datetime.now() - timedelta(days=7)

    sensors = ["sensor_001", "sensor_002", "sensor_003", "sensor_004", "sensor_005"]
    locations = ["Building_A", "Building_B", "Building_C"]

    for i in range(num_records):
        timestamp = start_time + timedelta(seconds=i * 2)  # Data every 2 seconds

        for sensor in sensors:
            doc = {
                "timestamp": timestamp,
                "metadata": {
                    "sensor_id": sensor,
                    "location": random.choice(locations),
                    "type": "temperature",
                },
                "temperature": round(random.uniform(18.0, 28.0), 2),
                "humidity": round(random.uniform(40.0, 70.0), 2),
                "pressure": round(random.uniform(980.0, 1020.0), 2),
            }
            data.append(doc)

    return data


# Generate data
print("📊 Generating 100,000 sensor readings...")
sensor_data = generate_sensor_data(100000)  # 100k intervals x 5 sensors

# Insert into Time Series Collection
print("⏱️ Inserting into Time Series collection...")
start = time.time()
ts_collection.insert_many(sensor_data.copy())
ts_insert_time = time.time() - start
print(f" Time taken: {ts_insert_time:.4f} seconds")

# Insert into Normal Collection
print("⏱️ Inserting into Normal collection...")
start = time.time()
normal_collection.insert_many(sensor_data.copy())
normal_insert_time = time.time() - start
print(f" Time taken: {normal_insert_time:.4f} seconds\n")

# ==========================================
# 2. STORAGE COMPARISON
# ==========================================

print("💾 STORAGE COMPARISON")
print("=" * 60)

ts_stats = db.command("collStats", "sensor_data_timeseries")
normal_stats = db.command("collStats", "sensor_data_normal")

ts_size = ts_stats["storageSize"] / (1024 * 1024)  # MB
normal_size = normal_stats["storageSize"] / (1024 * 1024)  # MB

print(f"Time Series Collection Size: {ts_size:.2f} MB")
print(f"Normal Collection Size: {normal_size:.2f} MB")
print(f"Space Savings: {((normal_size - ts_size) / normal_size * 100):.2f}%\n")

# ==========================================
# 3. QUERY PERFORMANCE COMPARISON
# ==========================================

print("🚀 QUERY PERFORMANCE COMPARISON")
print("=" * 60)

# Query 1: Range query
query_start = datetime.now() - timedelta(days=1)
query_end = datetime.now()

# Time Series Collection Query
start = time.time()
ts_result = list(
    ts_collection.find(
        {
            "timestamp": {"$gte": query_start, "$lte": query_end},
            "metadata.sensor_id": "sensor_001",
        }
    ).limit(1000)
)
ts_query_time = time.time() - start

# Normal Collection Query
start = time.time()
normal_result = list(
    normal_collection.find(
        {
            "timestamp": {"$gte": query_start, "$lte": query_end},
            "metadata.sensor_id": "sensor_001",
        }
    ).limit(1000)
)
normal_query_time = time.time() - start

print("Query 1: Range query (last 24 hours, specific sensor)")
print(f" Time Series: {ts_query_time:.4f}s | Found: {len(ts_result)} docs")
print(f" Normal: {normal_query_time:.4f}s | Found: {len(normal_result)} docs")
if ts_query_time > 0:
    print(f" Speedup: {normal_query_time / ts_query_time:.2f}x faster\n")
else:
    print(" Speedup: N/A\n")

# Query 2: Aggregation with time bucketing
pipeline = [
    {
        "$match": {
            "timestamp": {"$gte": query_start, "$lte": query_end},
        }
    },
    {
        "$group": {
            "_id": {
                "sensor": "$metadata.sensor_id",
                "hour": {"$dateTrunc": {"date": "$timestamp", "unit": "hour"}},
            },
            "avg_temp": {"$avg": "$temperature"},
            "max_temp": {"$max": "$temperature"},
            "min_temp": {"$min": "$temperature"},
            "count": {"$sum": 1},
        }
    },
    {"$sort": {"_id.hour": 1}},
]

# Time Series Collection Aggregation
start = time.time()
ts_agg_result = list(ts_collection.aggregate(pipeline))
ts_agg_time = time.time() - start

# Normal Collection Aggregation
start = time.time()
normal_agg_result = list(normal_collection.aggregate(pipeline))
normal_agg_time = time.time() - start

print("Query 2: Hourly aggregation (avg, max, min temperature)")
print(f" Time Series: {ts_agg_time:.4f}s | Buckets: {len(ts_agg_result)}")
print(f" Normal: {normal_agg_time:.4f}s | Buckets: {len(normal_agg_result)}")
if ts_agg_time > 0:
    print(f" Speedup: {normal_agg_time / ts_agg_time:.2f}x faster\n")
else:
    print(" Speedup: N/A\n")

# ==========================================
# 4. ADVANCED TIME SERIES FEATURES
# ==========================================

print("⚡ ADVANCED TIME SERIES FEATURES")
print("=" * 60)

window_pipeline = [
    {
        "$match": {
            "metadata.sensor_id": "sensor_001",
            "timestamp": {"$gte": query_start},
        }
    },
    {
        "$setWindowFields": {
            "partitionBy": "$metadata.sensor_id",
            "sortBy": {"timestamp": 1},
            "output": {
                "moving_avg_temp": {
                    "$avg": "$temperature",
                    "window": {
                        "documents": [-5, 5],  # 5 documents before and after
                    },
                }
            },
        }
    },
    {"$limit": 10},
]

start = time.time()
window_result = list(ts_collection.aggregate(window_pipeline))
window_time = time.time() - start

print("Window Function (Moving Average):")
print(f" Time taken: {window_time:.4f}s")
print(" Sample result:")
for doc in window_result[:3]:
    print(
        f" {doc['timestamp']} | Temp: {doc['temperature']:.2f}°C | "
        f"Moving Avg: {doc['moving_avg_temp']:.2f}°C"
    )

# ==========================================
# 5. SUMMARY
# ==========================================

print("\n" + "=" * 60)
print("📊 SUMMARY")
print("=" * 60)
print(f"Total Documents: {len(sensor_data):,}")
print("\n🏆 Winner Comparison:")
print(f" Storage Efficiency: Time Series is {((normal_size - ts_size) / normal_size * 100):.1f}% smaller")
if ts_query_time > 0:
    print(f" Range Query Speed: Time Series is {normal_query_time / ts_query_time:.1f}x faster")
else:
    print(" Range Query Speed: N/A")
if ts_agg_time > 0:
    print(f" Aggregation Speed: Time Series is {normal_agg_time / ts_agg_time:.1f}x faster")
else:
    print(" Aggregation Speed: N/A")
print("\n✨ Unique Time Series Features:")
print(" ✓ Automatic data bucketing")
print(" ✓ Optimized compression")
print(" ✓ Window functions for time-based analysis")
print(" ✓ Better indexing for time-based queries")
print("=" * 60)

# Cleanup
client.close()
