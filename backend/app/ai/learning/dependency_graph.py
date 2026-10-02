"""Skill Dependency Graph and Topological Sorter.

Constructs a Directed Acyclic Graph (DAG) for skill dependencies.
Implements DFS-based cycle detection and topological sorting to organize skill acquisition
into structured, prerequisite-aware stages while honoring already acquired candidate skills.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from sqlalchemy.orm import Session

from app.models.skill import Skill, SkillRelationship

logger = logging.getLogger(__name__)


class SkillDependencyGraph:
    """Manages skill prerequisite relationships, detects cycles, and generates topological stages."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        # Adjacency list: prereq -> list of dependent skills (u -> v: u is prereq of v)
        self.adj: Dict[str, List[str]] = {}
        # Inverted adjacency: dependent -> list of prerequisites (v -> list of u)
        self.in_edges: Dict[str, List[str]] = {}
        # Known skills
        self.skills: Set[str] = set()

        self._build_graph()

    def _build_graph(self) -> None:
        """Loads prerequisite relationships from database or fallback JSON."""
        relationships = []
        if self.db:
            try:
                db_rels = (
                    self.db.query(SkillRelationship)
                    .filter(SkillRelationship.relationship_type == "PREREQUISITE_OF")
                    .all()
                )
                for r in db_rels:
                    src_name = r.source_skill.name if r.source_skill else None
                    tgt_name = r.target_skill.name if r.target_skill else None
                    if src_name and tgt_name:
                        relationships.append((src_name, tgt_name))
            except Exception as e:
                logger.warning(f"Error querying SkillRelationship from DB: {e}. Falling back to JSON.")

        if not relationships:
            # Fallback to curated skill_relationships.json
            data_file = (
                Path(__file__).resolve().parent.parent.parent
                / "data"
                / "taxonomies"
                / "skill_relationships.json"
            )
            if data_file.exists():
                try:
                    with open(data_file, "r", encoding="utf-8") as f:
                        items = json.load(f)
                        for item in items:
                            if item.get("relationship_type") == "PREREQUISITE_OF":
                                relationships.append(
                                    (item["source_skill"], item["target_skill"])
                                )
                except Exception as e:
                    logger.error(f"Error reading skill_relationships.json: {e}")

        # Populate graph
        for src, tgt in relationships:
            src_norm = src.strip()
            tgt_norm = tgt.strip()
            self.skills.add(src_norm)
            self.skills.add(tgt_norm)

            if src_norm not in self.adj:
                self.adj[src_norm] = []
            if tgt_norm not in self.adj[src_norm]:
                self.adj[src_norm].append(tgt_norm)

            if tgt_norm not in self.in_edges:
                self.in_edges[tgt_norm] = []
            if src_norm not in self.in_edges[tgt_norm]:
                self.in_edges[tgt_norm].append(src_norm)

    def detect_cycles(self) -> List[List[str]]:
        """
        Detects cycles in the graph using DFS 3-coloring.
        Returns list of cycles found (e.g. [['A', 'B', 'C', 'A']]).
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {u: WHITE for u in self.skills}
        parent = {}
        cycles = []

        def dfs(u: str, path: List[str]):
            color[u] = GRAY
            path.append(u)

            for v in self.adj.get(u, []):
                if color.get(v, WHITE) == GRAY:
                    # Cycle detected: find where cycle begins
                    try:
                        cycle_start_idx = path.index(v)
                        cycle = path[cycle_start_idx:] + [v]
                        cycles.append(cycle)
                    except ValueError:
                        cycles.append([u, v])
                elif color.get(v, WHITE) == WHITE:
                    parent[v] = u
                    dfs(v, path)

            path.pop()
            color[u] = BLACK

        for node in list(self.skills):
            if color[node] == WHITE:
                dfs(node, [])

        return cycles

    def get_prerequisites_for_skill(self, skill_name: str) -> List[str]:
        """Returns immediate prerequisites for a given skill."""
        return self.in_edges.get(skill_name, [])

    def organize_learning_stages(
        self,
        target_skills: List[str],
        acquired_skills: Set[str],
    ) -> Dict[str, Any]:
        """
        Organizes missing target skills into topological stages.
        Candidate's already acquired skills are treated as satisfied dependencies.
        Returns:
            - stages: Dict[int, List[str]] (1-indexed stage numbers)
            - graph_nodes: List[Dict]
            - graph_edges: List[Dict]
        """
        norm_acquired = {s.lower().strip() for s in acquired_skills}
        
        # Only keep target skills that have NOT yet been acquired
        missing_skills = [
            s for s in target_skills if s.lower().strip() not in norm_acquired
        ]

        # Case: No missing skills
        if not missing_skills:
            return {
                "stages": {},
                "graph_nodes": [],
                "graph_edges": [],
            }

        # Build local subgraph for missing skills and their dependencies
        all_skills_in_scope = set(missing_skills)
        for s in missing_skills:
            for prereq in self.get_prerequisites_for_skill(s):
                all_skills_in_scope.add(prereq)

        # Calculate in-degree relative to missing skills
        # (prerequisites that candidate already possesses do NOT count towards in-degree)
        in_degree: Dict[str, int] = {s: 0 for s in missing_skills}
        for s in missing_skills:
            prereqs = self.get_prerequisites_for_skill(s)
            for p in prereqs:
                # If prerequisite is also missing and in target list, it must precede s
                if p in missing_skills and p.lower().strip() not in norm_acquired:
                    in_degree[s] += 1

        # Multi-stage topological grouping (Kahn's algorithm variant)
        stages: Dict[int, List[str]] = {}
        current_stage = 1
        remaining = set(missing_skills)

        while remaining:
            # Find all skills with in-degree 0 in current remaining set
            ready = [s for s in remaining if in_degree[s] == 0]

            if not ready:
                # Fallback for remaining cyclic or mutually dependent skills: take remaining
                ready = list(remaining)

            stages[current_stage] = sorted(ready)

            # Remove ready skills and decrement in-degrees of dependents
            for s in ready:
                remaining.remove(s)
                for dep in self.adj.get(s, []):
                    if dep in in_degree and in_degree[dep] > 0:
                        in_degree[dep] -= 1

            current_stage += 1

        # Construct Graph Nodes & Edges for Visualizer
        graph_nodes = []
        graph_edges = []
        seen_nodes = set()

        # Add target/missing nodes
        for stg_num, skills_in_stg in stages.items():
            for sk in skills_in_stg:
                graph_nodes.append({
                    "id": sk,
                    "label": sk,
                    "status": "NOT_STARTED",
                    "stage": stg_num,
                })
                seen_nodes.add(sk)

        # Add acquired prerequisite nodes that directly unlock target skills
        for sk in missing_skills:
            for p in self.get_prerequisites_for_skill(sk):
                if p.lower().strip() in norm_acquired and p not in seen_nodes:
                    graph_nodes.append({
                        "id": p,
                        "label": p,
                        "status": "ACQUIRED",
                        "stage": 0,
                    })
                    seen_nodes.add(p)

                # Add edge
                if p in seen_nodes and sk in seen_nodes:
                    graph_edges.append({
                        "source": p,
                        "target": sk,
                        "relationship_type": "PREREQUISITE_OF",
                    })

        return {
            "stages": stages,
            "graph_nodes": graph_nodes,
            "graph_edges": graph_edges,
        }
