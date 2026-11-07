from collections import deque
from typing import Dict, List, Set, Tuple, Any, Optional


class GraphEdgeView:
    def __init__(
        self,
        id: str,
        source_id: str,
        target_id: str,
        relation_type: str,
        relationship_strength: float,
        propagation_enabled: bool,
        confirmation_status: str,
    ):
        self.id = id
        self.source_id = source_id
        self.target_id = target_id
        self.relation_type = relation_type
        self.relationship_strength = relationship_strength
        self.propagation_enabled = propagation_enabled
        self.confirmation_status = confirmation_status


class GraphTraversalResult:
    def __init__(
        self,
        node_id: str,
        shortest_distance: int,
        explanation_paths: List[List[Dict[str, Any]]],
        path_strength: float,
        has_unconfirmed_edges: bool,
    ):
        self.node_id = node_id
        self.shortest_distance = shortest_distance
        self.explanation_paths = explanation_paths
        self.path_strength = path_strength
        self.has_unconfirmed_edges = has_unconfirmed_edges


class GraphEngine:
    @staticmethod
    def traverse_impact(
        start_node_id: str,
        edges: List[GraphEdgeView],
        node_display_map: Optional[Dict[str, str]] = None,
    ) -> Tuple[Dict[str, GraphTraversalResult], List[str]]:
        """
        Cycle-safe BFS traversal starting from start_node_id.
        Follows only active edges with propagation_enabled=True.
        Calculates shortest distance and reconstructs up to 3 shortest explanation paths.
        Returns: (results_by_node_id, warnings)
        """
        node_display_map = node_display_map or {}
        warnings: List[str] = []

        # 1. Build adjacency list of active, propagation-enabled edges
        adjacency: Dict[str, List[GraphEdgeView]] = {}
        for edge in edges:
            if not edge.propagation_enabled:
                continue
            adjacency.setdefault(edge.source_id, []).append(edge)

        # Check if root has outgoing links
        if start_node_id not in adjacency or not adjacency[start_node_id]:
            warnings.append(
                f"Changed requirement node has no outgoing active propagation links."
            )
            return {}, warnings

        # 2. BFS Traversal
        distance: Dict[str, int] = {start_node_id: 0}
        # predecessors map: target_node -> list of (predecessor_node_id, edge)
        predecessors: Dict[str, List[Tuple[str, GraphEdgeView]]] = {start_node_id: []}
        queue = deque([start_node_id])
        visited: Set[str] = {start_node_id}

        detected_cycle = False

        while queue:
            current = queue.popleft()
            current_dist = distance[current]

            for edge in adjacency.get(current, []):
                next_node = edge.target_id
                candidate_dist = current_dist + 1

                if next_node not in visited:
                    visited.add(next_node)
                    distance[next_node] = candidate_dist
                    predecessors[next_node] = [(current, edge)]
                    queue.append(next_node)
                else:
                    # Next node already visited. Check if this is an alternative shortest path
                    if candidate_dist == distance.get(next_node, -1):
                        predecessors[next_node].append((current, edge))
                    elif candidate_dist < distance.get(next_node, -1):
                        # Shorter path found
                        distance[next_node] = candidate_dist
                        predecessors[next_node] = [(current, edge)]
                    else:
                        # Longer path or back-edge (cycle)
                        detected_cycle = True

        if detected_cycle:
            warnings.append(
                "Traceability graph contains cycles; cycle-safe traversal handled them successfully."
            )

        # 3. Path Reconstruction for all reached nodes (excluding start_node)
        results: Dict[str, GraphTraversalResult] = {}

        def get_all_paths(
            curr: str, max_paths: int = 3
        ) -> List[List[Dict[str, Any]]]:
            if curr == start_node_id:
                return [[]]
            paths: List[List[Dict[str, Any]]] = []
            for pred_id, edge in predecessors.get(curr, []):
                sub_paths = get_all_paths(pred_id, max_paths - len(paths))
                for sp in sub_paths:
                    step = {
                        "edge_id": edge.id,
                        "source_id": edge.source_id,
                        "source_display_id": node_display_map.get(
                            edge.source_id, edge.source_id
                        ),
                        "target_id": edge.target_id,
                        "target_display_id": node_display_map.get(
                            edge.target_id, edge.target_id
                        ),
                        "relation_type": edge.relation_type,
                        "relationship_strength": edge.relationship_strength,
                        "confirmation_status": edge.confirmation_status,
                    }
                    paths.append(sp + [step])
                    if len(paths) >= max_paths:
                        return paths
            return paths

        for reached_node, dist in distance.items():
            if reached_node == start_node_id:
                continue

            explanation_paths = get_all_paths(reached_node, max_paths=3)

            # Calculate path strength for each path: product of edge strengths
            # Choose the maximum strength path as the representative path_strength
            best_strength = 0.0
            has_unconfirmed = False

            for p in explanation_paths:
                p_strength = 1.0
                for step in p:
                    p_strength *= step["relationship_strength"]
                    if step["confirmation_status"] in ("SUGGESTED", "NEEDS_REVIEW"):
                        has_unconfirmed = True
                if p_strength > best_strength:
                    best_strength = p_strength

            results[reached_node] = GraphTraversalResult(
                node_id=reached_node,
                shortest_distance=dist,
                explanation_paths=explanation_paths,
                path_strength=round(best_strength, 4),
                has_unconfirmed_edges=has_unconfirmed,
            )

        return results, warnings
