import React, { useEffect, useState, useCallback } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  applyNodeChanges,
  applyEdgeChanges,
  Node,
  Edge,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api';
import { GitFork, Plus, X, Trash2, ShieldCheck, Info } from 'lucide-react';

const RELATION_TYPES = [
  'IMPLEMENTED_BY',
  'SPECIFIED_BY',
  'REALISED_AS',
  'DEPENDS_ON',
  'EXPOSES',
  'CONSUMED_BY',
  'USES',
  'VERIFIED_BY',
  'DOCUMENTED_BY',
  'DEPLOYED_IN',
  'CONSTRAINED_BY',
];

export const TraceabilityGraph: React.FC = () => {
  const { activeProject } = useAuth();
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [rawGraph, setRawGraph] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [selectedEdge, setSelectedEdge] = useState<any>(null);
  const [showAddEdgeModal, setShowAddEdgeModal] = useState(false);

  // Form for new edge
  const [edgeForm, setEdgeForm] = useState({
    source_node_id: '',
    target_node_id: '',
    relation_type: 'IMPLEMENTED_BY',
    relationship_strength: 1.0,
    confirmation_status: 'CONFIRMED',
    notes: '',
  });

  const loadGraph = () => {
    if (!activeProject) return;
    setLoading(true);
    api.getGraph(activeProject.id)
      .then((res) => {
        setRawGraph(res);
        // Build ReactFlow Nodes
        const flowNodes: Node[] = res.nodes.map((n: any, idx: number) => {
          const isReq = n.node_type === 'REQUIREMENT';
          // Compute simple layout in grid / ranks
          const row = Math.floor(idx / 5);
          const col = idx % 5;
          return {
            id: n.id,
            data: { label: `${n.display_id}\n${n.title || ''}`, raw: n },
            position: { x: col * 240 + 50, y: row * 140 + 50 },
            style: {
              background: isReq ? '#1e1b4b' : '#0f172a',
              color: '#f8fafc',
              border: isReq ? '2px solid #6366f1' : '1px solid #334155',
              borderRadius: '12px',
              padding: '10px 14px',
              fontSize: '11px',
              fontWeight: 600,
              width: 180,
              textAlign: 'center',
              boxShadow: isReq ? '0 4px 14px rgba(99, 102, 241, 0.25)' : '0 2px 8px rgba(0,0,0,0.4)',
            },
          };
        });

        // Build ReactFlow Edges
        const flowEdges: Edge[] = res.edges.map((e: any) => ({
          id: e.id,
          source: e.source_node_id,
          target: e.target_node_id,
          label: e.relation_type,
          labelStyle: { fill: '#94a3b8', fontSize: 9, fontFamily: 'monospace' },
          labelBgStyle: { fill: '#0f172a', fillOpacity: 0.8 },
          markerEnd: { type: MarkerType.ArrowClosed, color: '#38bdf8' },
          style: { stroke: '#38bdf8', strokeWidth: 1.5 },
          data: { raw: e },
        }));

        setNodes(flowNodes);
        setEdges(flowEdges);
      })
      .catch((err) => console.error('Failed to load graph', err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadGraph();
  }, [activeProject?.id]);

  const onNodesChange = useCallback(
    (changes: any) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );

  const onEdgesChange = useCallback(
    (changes: any) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );

  const onNodeClick = (_: any, node: Node) => {
    setSelectedNode(node.data.raw);
    setSelectedEdge(null);
  };

  const onEdgeClick = (_: any, edge: Edge) => {
    setSelectedEdge(edge.data.raw);
    setSelectedNode(null);
  };

  const handleCreateEdge = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeProject) return;
    try {
      await api.createEdge(activeProject.id, edgeForm);
      setShowAddEdgeModal(false);
      setEdgeForm({
        source_node_id: '',
        target_node_id: '',
        relation_type: 'IMPLEMENTED_BY',
        relationship_strength: 1.0,
        confirmation_status: 'CONFIRMED',
        notes: '',
      });
      loadGraph();
    } catch (err: any) {
      alert(`Error creating relationship: ${err.message}`);
    }
  };

  const handleDeleteEdge = async (edgeId: string) => {
    if (!confirm('Are you sure you want to deactivate this traceability link?')) return;
    try {
      await api.deactivateEdge(edgeId);
      setSelectedEdge(null);
      loadGraph();
    } catch (err: any) {
      alert(`Error deactivating edge: ${err.message}`);
    }
  };

  return (
    <div className="space-y-4 max-w-7xl mx-auto h-[calc(100vh-140px)] flex flex-col">
      {/* Controls Bar */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-800 shrink-0">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <GitFork className="w-5 h-5 text-emerald-400" />
            <span>Traceability Graph Explorer</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Directed dependency paths: Source change triggers downstream impact propagation.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAddEdgeModal(true)}
            className="px-3.5 py-1.5 bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold rounded-xl shadow-md transition flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Relationship</span>
          </button>
        </div>
      </div>

      {/* Main Canvas + Detail Drawer */}
      <div className="flex-1 flex gap-4 overflow-hidden relative">
        <div className="flex-1 h-full bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden shadow-inner">
          {loading ? (
            <div className="h-full flex items-center justify-center text-slate-400 text-xs">
              Loading traceability network...
            </div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={onNodeClick}
              onEdgeClick={onEdgeClick}
              fitView
            >
              <Background color="#334155" gap={20} size={1} />
              <Controls className="bg-slate-900 border-slate-800 fill-slate-200" />
            </ReactFlow>
          )}
        </div>

        {/* Selected Node or Edge Inspector */}
        {(selectedNode || selectedEdge) && (
          <div className="w-80 bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shrink-0 shadow-2xl overflow-y-auto">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white">
                {selectedNode ? 'Node Detail' : 'Relationship Detail'}
              </h3>
              <button
                onClick={() => {
                  setSelectedNode(null);
                  setSelectedEdge(null);
                }}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {selectedNode && (
              <div className="space-y-3 text-xs">
                <div>
                  <div className="text-[10px] text-slate-400 font-mono uppercase">Display Identifier</div>
                  <div className="font-mono font-bold text-brand-400 text-sm mt-0.5">{selectedNode.display_id}</div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400 font-mono uppercase">Node Type</div>
                  <div className="text-slate-200 font-medium">{selectedNode.node_type} ({selectedNode.sub_type})</div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400 font-mono uppercase">Title</div>
                  <div className="text-slate-200 font-medium">{selectedNode.title || 'Untitled'}</div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400 font-mono uppercase">Criticality Rating</div>
                  <div className="text-slate-200 font-bold">{selectedNode.criticality} of 5</div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400 font-mono uppercase">Lifecycle Status</div>
                  <div className="text-emerald-400 font-semibold">{selectedNode.status}</div>
                </div>
              </div>
            )}

            {selectedEdge && (
              <div className="space-y-3 text-xs">
                <div>
                  <div className="text-[10px] text-slate-400 font-mono uppercase">Relation Type</div>
                  <div className="font-mono font-bold text-sky-400 text-sm mt-0.5">{selectedEdge.relation_type}</div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400 font-mono uppercase">Connected Nodes</div>
                  <div className="text-slate-200 font-mono mt-0.5">
                    {selectedEdge.source_display_id} ➔ {selectedEdge.target_display_id}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400 font-mono uppercase">Propagation Strength</div>
                  <div className="text-slate-200 font-mono">{selectedEdge.relationship_strength * 100}%</div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400 font-mono uppercase">Confirmation Status</div>
                  <div className="text-slate-300 flex items-center gap-1.5 mt-0.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                    <span>{selectedEdge.confirmation_status}</span>
                  </div>
                </div>
                {selectedEdge.notes && (
                  <div>
                    <div className="text-[10px] text-slate-400 font-mono uppercase">Notes</div>
                    <div className="text-slate-300 italic mt-0.5">{selectedEdge.notes}</div>
                  </div>
                )}
                <div className="pt-3 border-t border-slate-800">
                  <button
                    onClick={() => handleDeleteEdge(selectedEdge.id)}
                    className="w-full py-2 bg-rose-950/60 hover:bg-rose-900 border border-rose-800 text-rose-300 text-xs font-semibold rounded-xl transition flex items-center justify-center gap-1.5"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Deactivate Link</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Add Edge Modal */}
      {showAddEdgeModal && rawGraph && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <h3 className="text-base font-bold text-white">Create Traceability Relationship</h3>
              <button onClick={() => setShowAddEdgeModal(false)} className="text-slate-400 hover:text-slate-200">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateEdge} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 mb-1 font-mono">Source Node (Trigger)</label>
                <select
                  required
                  value={edgeForm.source_node_id}
                  onChange={(e) => setEdgeForm({ ...edgeForm, source_node_id: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="">Select source node...</option>
                  {rawGraph.nodes.map((n: any) => (
                    <option key={n.id} value={n.id}>
                      {n.display_id} - {n.title} ({n.node_type})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-mono">Target Node (Downstream Consequence)</label>
                <select
                  required
                  value={edgeForm.target_node_id}
                  onChange={(e) => setEdgeForm({ ...edgeForm, target_node_id: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="">Select target node...</option>
                  {rawGraph.nodes
                    .filter((n: any) => n.id !== edgeForm.source_node_id)
                    .map((n: any) => (
                      <option key={n.id} value={n.id}>
                        {n.display_id} - {n.title} ({n.node_type})
                      </option>
                    ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1 font-mono">Relation Type</label>
                  <select
                    value={edgeForm.relation_type}
                    onChange={(e) => setEdgeForm({ ...edgeForm, relation_type: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    {RELATION_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1 font-mono">Confirmation Status</label>
                  <select
                    value={edgeForm.confirmation_status}
                    onChange={(e) => setEdgeForm({ ...edgeForm, confirmation_status: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    <option value="CONFIRMED">CONFIRMED</option>
                    <option value="SUGGESTED">SUGGESTED</option>
                    <option value="NEEDS_REVIEW">NEEDS_REVIEW</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-mono">Notes / Rationale</label>
                <input
                  type="text"
                  placeholder="e.g. Service implements registration business logic."
                  value={edgeForm.notes}
                  onChange={(e) => setEdgeForm({ ...edgeForm, notes: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddEdgeModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-semibold rounded-xl text-slate-300 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold rounded-xl transition shadow-lg shadow-brand-600/25"
                >
                  Establish Link
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
