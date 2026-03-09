"""
MedTrack – DynamoDB Document Store
Replaces the in-memory document store with AWS DynamoDB Local.
Provides the same collection API (find_one, find, insert_one, update_one, etc.)
so that controllers require no changes to their query logic.
"""

import copy
import os
import re
import uuid
from datetime import datetime
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

# ─── DynamoDB connection ──────────────────────────────────────
DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8000")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url=DYNAMODB_ENDPOINT,
    region_name=AWS_REGION,
    aws_access_key_id="fakeMyKeyId",
    aws_secret_access_key="fakeSecretAccessKey",
)

dynamodb_client = boto3.client(
    "dynamodb",
    endpoint_url=DYNAMODB_ENDPOINT,
    region_name=AWS_REGION,
    aws_access_key_id="fakeMyKeyId",
    aws_secret_access_key="fakeSecretAccessKey",
)


# ─── Helper: convert Python types ↔ DynamoDB types ────────────
def _to_dynamo(value):
    """Convert Python value to DynamoDB-safe type (Decimal for numbers)."""
    if isinstance(value, bool):
        return value  # must check before int, since bool is subclass of int
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, int):
        return Decimal(str(value))
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, dict):
        return {k: _to_dynamo(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_dynamo(i) for i in value]
    if isinstance(value, str) and value == "":
        return "EMPTY__SENTINEL"
    if value is None:
        return "NULL__SENTINEL"
    return value


def _from_dynamo(value):
    """Convert DynamoDB types back to Python types."""
    if isinstance(value, Decimal):
        if value == int(value):
            return int(value)
        return float(value)
    if isinstance(value, dict):
        return {k: _from_dynamo(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_from_dynamo(i) for i in value]
    if value == "NULL__SENTINEL":
        return None
    if value == "EMPTY__SENTINEL":
        return ""
    return value


# ─── InsertResult ──────────────────────────────────────────────
class InsertResult:
    """Mimics pymongo InsertOneResult."""
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


# ─── Cursor ────────────────────────────────────────────────────
class Cursor:
    """Mimics pymongo Cursor with sort / limit / iteration."""

    def __init__(self, docs):
        self._docs = list(docs)
        self._sort_key = None
        self._sort_dir = 1
        self._limit_n = 0

    def sort(self, key, direction=-1):
        self._sort_key = key
        self._sort_dir = direction
        return self

    def limit(self, n):
        self._limit_n = n
        return self

    def _resolve(self):
        docs = self._docs
        if self._sort_key:
            docs = sorted(
                docs,
                key=lambda d: d.get(self._sort_key, ""),
                reverse=(self._sort_dir == -1),
            )
        if self._limit_n:
            docs = docs[: self._limit_n]
        return docs

    def __iter__(self):
        return iter(self._resolve())

    def __next__(self):
        return next(iter(self._resolve()))

    def __len__(self):
        return len(self._resolve())

    def __list__(self):
        return self._resolve()


# ─── Matcher: evaluate MongoDB-style query filters ─────────────
def _match(doc, query):
    """Return True if *doc* satisfies the MongoDB-style *query* dict."""
    for key, condition in query.items():
        if key == "$or":
            if not any(_match(doc, sub) for sub in condition):
                return False
            continue
        if key == "$and":
            if not all(_match(doc, sub) for sub in condition):
                return False
            continue

        value = doc.get(key)

        if isinstance(condition, dict):
            for op, op_val in condition.items():
                if op == "$in":
                    if value not in op_val:
                        return False
                elif op == "$nin":
                    if value in op_val:
                        return False
                elif op == "$regex":
                    flags = 0
                    if condition.get("$options", "") and "i" in condition["$options"]:
                        flags = re.IGNORECASE
                    if not re.search(op_val, str(value or ""), flags):
                        return False
                elif op == "$exists":
                    exists = key in doc
                    if op_val and not exists:
                        return False
                    if not op_val and exists:
                        return False
                elif op == "$gt":
                    if value is None or value <= op_val:
                        return False
                elif op == "$gte":
                    if value is None or value < op_val:
                        return False
                elif op == "$lt":
                    if value is None or value >= op_val:
                        return False
                elif op == "$lte":
                    if value is None or value > op_val:
                        return False
                elif op == "$ne":
                    if value == op_val:
                        return False
                elif op == "$sum":
                    pass
        else:
            if value != condition:
                return False
    return True


# ─── Collection ────────────────────────────────────────────────
class DynamoCollection:
    """
    Drop-in replacement for pymongo.collection.Collection.
    Stores documents in DynamoDB Local with a single-table design.
    Each collection maps to a DynamoDB table with `_id` as the hash key.
    """

    TABLE_NAMES = set()  # track created tables

    def __init__(self, name):
        self.name = name
        self._table = None
        self._ensure_table()

    def _ensure_table(self):
        """Create the DynamoDB table if it doesn't exist."""
        if self.name in DynamoCollection.TABLE_NAMES:
            self._table = dynamodb.Table(self.name)
            return

        existing = dynamodb_client.list_tables().get("TableNames", [])
        if self.name not in existing:
            dynamodb.create_table(
                TableName=self.name,
                KeySchema=[{"AttributeName": "_id", "KeyType": "HASH"}],
                AttributeDefinitions=[
                    {"AttributeName": "_id", "AttributeType": "S"}
                ],
                BillingMode="PAY_PER_REQUEST",
            )
            # Wait for table to become active
            table = dynamodb.Table(self.name)
            table.meta.client.get_waiter("table_exists").wait(TableName=self.name)
            self._table = table
        else:
            self._table = dynamodb.Table(self.name)

        DynamoCollection.TABLE_NAMES.add(self.name)

    def _get_all_items(self):
        """Scan entire table and return all items (converted from Dynamo types)."""
        items = []
        response = self._table.scan()
        items.extend(response.get("Items", []))
        while "LastEvaluatedKey" in response:
            response = self._table.scan(
                ExclusiveStartKey=response["LastEvaluatedKey"]
            )
            items.extend(response.get("Items", []))
        return [_from_dynamo(item) for item in items]

    # write ops -------------------------------------------------
    def insert_one(self, doc):
        doc = copy.deepcopy(doc)
        if "_id" not in doc:
            doc["_id"] = str(uuid.uuid4())
        doc["_id"] = str(doc["_id"])
        doc_id = doc["_id"]

        dynamo_doc = _to_dynamo(doc)
        self._table.put_item(Item=dynamo_doc)
        return InsertResult(doc_id)

    def update_one(self, filter_q, update, upsert=False):
        all_items = self._get_all_items()
        matched = None
        for doc in all_items:
            if _match(doc, filter_q):
                matched = doc
                break

        if matched:
            if "$set" in update:
                for k, v in update["$set"].items():
                    matched[k] = v
            if "$unset" in update:
                for k in update["$unset"]:
                    matched.pop(k, None)
            if "$inc" in update:
                for k, v in update["$inc"].items():
                    matched[k] = matched.get(k, 0) + v
            if "$push" in update:
                for k, v in update["$push"].items():
                    matched.setdefault(k, []).append(v)
            self._table.put_item(Item=_to_dynamo(matched))
            return

        if upsert:
            new_doc = copy.deepcopy(filter_q)
            if "$set" in update:
                new_doc.update(update["$set"])
            new_doc = {k: v for k, v in new_doc.items() if not k.startswith("$")}
            self.insert_one(new_doc)

    def update_many(self, filter_q, update):
        all_items = self._get_all_items()
        for doc in all_items:
            if _match(doc, filter_q):
                if "$set" in update:
                    for k, v in update["$set"].items():
                        doc[k] = v
                self._table.put_item(Item=_to_dynamo(doc))

    def delete_one(self, filter_q):
        all_items = self._get_all_items()
        for doc in all_items:
            if _match(doc, filter_q):
                self._table.delete_item(Key={"_id": doc["_id"]})
                return

    def delete_many(self, filter_q):
        all_items = self._get_all_items()
        for doc in all_items:
            if _match(doc, filter_q):
                self._table.delete_item(Key={"_id": doc["_id"]})

    # read ops --------------------------------------------------
    def find_one(self, filter_q=None, projection=None):
        filter_q = filter_q or {}

        # Optimization: if filtering only by _id, use get_item
        if list(filter_q.keys()) == ["_id"] and isinstance(filter_q["_id"], str):
            response = self._table.get_item(Key={"_id": filter_q["_id"]})
            item = response.get("Item")
            if item:
                result = _from_dynamo(item)
                if projection:
                    result = self._apply_projection(result, projection)
                return result
            return None

        all_items = self._get_all_items()
        for doc in all_items:
            if _match(doc, filter_q):
                result = copy.deepcopy(doc)
                if projection:
                    result = self._apply_projection(result, projection)
                return result
        return None

    def find(self, filter_q=None, projection=None):
        filter_q = filter_q or {}
        all_items = self._get_all_items()
        results = []
        for doc in all_items:
            if _match(doc, filter_q):
                d = copy.deepcopy(doc)
                if projection:
                    d = self._apply_projection(d, projection)
                results.append(d)
        return Cursor(results)

    def count_documents(self, filter_q=None):
        filter_q = filter_q or {}
        all_items = self._get_all_items()
        return sum(1 for doc in all_items if _match(doc, filter_q))

    def aggregate(self, pipeline):
        """Very basic aggregation supporting $group/$sort/$limit."""
        docs = self._get_all_items()
        for stage in pipeline:
            if "$group" in stage:
                g = stage["$group"]
                group_key = g["_id"]
                field = group_key.lstrip("$") if isinstance(group_key, str) else None
                groups = {}
                for doc in docs:
                    key = doc.get(field, "Unknown") if field else "all"
                    if key not in groups:
                        groups[key] = {"_id": key, "count": 0}
                    for agg_field, agg_op in g.items():
                        if agg_field == "_id":
                            continue
                        if isinstance(agg_op, dict) and "$sum" in agg_op:
                            groups[key][agg_field] = groups[key].get(agg_field, 0) + 1
                docs = list(groups.values())
            elif "$sort" in stage:
                sort_spec = stage["$sort"]
                for key, direction in reversed(list(sort_spec.items())):
                    docs.sort(
                        key=lambda d: d.get(key, 0),
                        reverse=(direction == -1),
                    )
            elif "$limit" in stage:
                docs = docs[: stage["$limit"]]
        return docs

    def create_index(self, *args, **kwargs):
        """No-op: DynamoDB manages its own indexes."""
        pass

    @staticmethod
    def _apply_projection(doc, projection):
        """Apply MongoDB-style field projection."""
        if not projection:
            return doc
        has_inclusion = any(v == 1 for v in projection.values() if isinstance(v, int))
        has_exclusion = any(v == 0 for v in projection.values() if isinstance(v, int))
        if has_exclusion:
            for field, val in projection.items():
                if val == 0:
                    doc.pop(field, None)
        elif has_inclusion:
            keys_to_keep = {"_id"}
            for field, val in projection.items():
                if val == 1:
                    keys_to_keep.add(field)
            doc = {k: v for k, v in doc.items() if k in keys_to_keep}
        return doc


# ─── DynamoDB Database ────────────────────────────────────────
class DynamoDatabase:
    """Mimics pymongo database with attribute-based collection access."""

    def __init__(self):
        self._collections = {}

    def __getattr__(self, name):
        if name.startswith("_"):
            return super().__getattribute__(name)
        if name not in self._collections:
            self._collections[name] = DynamoCollection(name)
        return self._collections[name]

    def __getitem__(self, name):
        return self.__getattr__(name)


# ─── Initialise ───────────────────────────────────────────────
db = DynamoDatabase()

# Collections (same names as before so imports keep working)
users_collection = db.users
doctors_collection = db.doctors
patients_collection = db.patients
appointments_collection = db.appointments
medical_records_collection = db.medical_records
notifications_collection = db.notifications
reviews_collection = db.reviews


def init_indexes():
    """No-op for DynamoDB – kept for API compatibility."""
    print("[OK] DynamoDB Local document store initialised")
    print(f"     Endpoint: {DYNAMODB_ENDPOINT}")


def get_db():
    return db
