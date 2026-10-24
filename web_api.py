

import asyncio
import copy
from pathlib import Path

import networkx as nx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from aerodrift.collectors.aws_collector import AWSCollector
from aerodrift.collectors.mock_aws_client import MockAWSClient
from aerodrift.topology.graph import CloudTopology
from aerodrift.drift.detector import detect_database_drift
from aerodrift.storage.snapshot_store import (
    save_snapshot,
    list_snapshots,
    load_snapshot,
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "aerodrift.db"
MOCK_FILE = BASE_DIR / "mock_data" / "aws_state.json"

app = FastAPI(
    title="AeroDrift API",
    description="Cloud topology, drift detection and snapshot history",
    version="1.0.0",
)


async def build_demo_state():
    """Collect mock resources and reproduce the synthetic drift example."""
    client = MockAWSClient(str(MOCK_FILE))
    collector = AWSCollector(client)
    state = await collector.collect_all()

    topology = CloudTopology()
    baseline_graph = topology.build(state)

    previous_graph = copy.deepcopy(baseline_graph)
    current_graph = copy.deepcopy(baseline_graph)

    database_id = "db-prod-001"
    private_subnet_id = "subnet-private-001"

    for graph in (previous_graph, current_graph):
        graph.add_node(
            database_id,
            resource_type="database",
            name="production-database",
            private_ip="10.0.2.20",
        )

        if private_subnet_id in graph:
            graph.add_edge(
                private_subnet_id,
                database_id,
                relationship="network_path",
            )

    if private_subnet_id in current_graph:
        current_graph.add_edge(
            "internet",
            private_subnet_id,
            relationship="simulated_drift",
        )

    findings = detect_database_drift(
        previous_graph,
        current_graph,
    )

    return state, current_graph, findings


def serialize_graph(graph: nx.DiGraph) -> dict:
    return {
        "nodes": [
            {"id": str(node_id), **attributes}
            for node_id, attributes in graph.nodes(data=True)
        ],
        "edges": [
            {
                "source": str(source),
                "target": str(target),
                **attributes,
            }
            for source, target, attributes in graph.edges(data=True)
        ],
    }


@app.get("/")
def root():
    return {
        "application": "AeroDrift",
        "status": "running",
        "environment": "mock",
        "docs": "/docs",
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "environment": "mock",
    }


@app.get("/api/overview")
async def overview():
    state, graph, findings = await build_demo_state()

    return {
        "environment": "mock",
        "resources": {
            "vpcs": len(state["vpcs"]),
            "subnets": len(state["subnets"]),
            "ec2_instances": len(state["ec2_instances"]),
            "security_groups": len(state["security_groups"]),
            "databases": sum(
                1
                for _, attrs in graph.nodes(data=True)
                if attrs.get("resource_type") == "database"
            ),
        },
        "graph_nodes": graph.number_of_nodes(),
        "graph_edges": graph.number_of_edges(),
        "finding_count": len(findings),
        "findings": [
            {
                "resource_id": finding.resource_id,
                "message": finding.message,
                "path": finding.path,
                "severity": "high",
                "source": "synthetic graph scenario",
            }
            for finding in findings
        ],
    }


@app.get("/api/topology")
async def topology():
    _, graph, _ = await build_demo_state()
    return serialize_graph(graph)


class SnapshotRequest(BaseModel):
    label: str = Field(min_length=1, max_length=100)


@app.get("/api/snapshots")
def snapshots():
    return {"snapshots": list_snapshots(DB_PATH)}


@app.post("/api/snapshots")
async def create_snapshot(request: SnapshotRequest):
    _, graph, _ = await build_demo_state()

    try:
        snapshot_id = save_snapshot(
            graph,
            request.label,
            DB_PATH,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "id": snapshot_id,
        "label": request.label.strip(),
        "message": "Snapshot saved to SQLite",
    }


@app.get("/api/snapshots/{snapshot_id}")
def get_snapshot(snapshot_id: int):
    try:
        graph = load_snapshot(snapshot_id, DB_PATH)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return {
        "id": snapshot_id,
        **serialize_graph(graph),
    }
    
class SnapshotComparisonRequest(BaseModel):
    previous_snapshot_id: int = Field(gt=0)
    current_snapshot_id: int = Field(gt=0)


def graph_diff(previous_graph: nx.DiGraph, current_graph: nx.DiGraph) -> dict:
    """Compare resource IDs and directed relationships between two snapshots."""
    previous_nodes = set(previous_graph.nodes)
    current_nodes = set(current_graph.nodes)

    previous_edges = set(previous_graph.edges)
    current_edges = set(current_graph.edges)

    added_nodes = sorted(current_nodes - previous_nodes)
    removed_nodes = sorted(previous_nodes - current_nodes)
    added_edges = sorted(current_edges - previous_edges)
    removed_edges = sorted(previous_edges - current_edges)

    return {
        "added_resources": [
            {
                "id": str(node_id),
                **current_graph.nodes[node_id],
            }
            for node_id in added_nodes
        ],
        "removed_resources": [
            {
                "id": str(node_id),
                **previous_graph.nodes[node_id],
            }
            for node_id in removed_nodes
        ],
        "added_relationships": [
            {"source": str(source), "target": str(target)}
            for source, target in added_edges
        ],
        "removed_relationships": [
            {"source": str(source), "target": str(target)}
            for source, target in removed_edges
        ],
        "summary": {
            "added_resources": len(added_nodes),
            "removed_resources": len(removed_nodes),
            "added_relationships": len(added_edges),
            "removed_relationships": len(removed_edges),
        },
    }


@app.post("/api/snapshots/compare")
def compare_snapshots(request: SnapshotComparisonRequest):
    """Compare two persisted topology snapshots."""
    try:
        previous_graph = load_snapshot(
            request.previous_snapshot_id, DB_PATH
        )
        current_graph = load_snapshot(
            request.current_snapshot_id, DB_PATH
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return {
        "previous_snapshot_id": request.previous_snapshot_id,
        "current_snapshot_id": request.current_snapshot_id,
        "comparison": graph_diff(previous_graph, current_graph),
    }
