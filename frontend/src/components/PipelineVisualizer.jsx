import React, { useCallback, useEffect, useMemo } from "react";
import ReactFlow, { 
  Background, 
  Controls, 
  useNodesState, 
  useEdgesState,
  MarkerType,
  addEdge,
  MiniMap
} from "reactflow";
import "reactflow/dist/style.css";
import { Paper, Box, Typography, IconButton, Tooltip } from '@mui/material';
import { ZoomIn, ZoomOut, FitScreen } from '@mui/icons-material';

const nodeStyle = {
  padding: '10px 20px',
  borderRadius: '10px',
  fontSize: '14px',
  color: '#fff',
  width: 180,
  textAlign: 'center',
  fontWeight: 'bold',
  boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
  transition: 'all 0.3s ease',
  cursor: 'pointer',
  '&:hover': {
    transform: 'scale(1.05)',
    boxShadow: '0 6px 12px rgba(0,0,0,0.15)'
  }
};

const PipelineVisualizer = ({ pipelineNodes, onNodeClick, onConnect }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const reactFlowWrapper = React.useRef(null);

  // Sync internal React Flow state with the parent's pipeline array
  useEffect(() => {
    const formattedNodes = pipelineNodes.map((node, index) => ({
      id: node.id,
      data: { 
        label: node.name,
        description: node.description,
        config: node.config
      },
      position: { x: 50 + index * 250, y: 100 },
      style: { 
        ...nodeStyle, 
        background: node.color || '#1976d2',
        border: 'none'
      },
      onClick: (event, nodeData) => {
        if (onNodeClick) onNodeClick(nodeData);
      }
    }));

    const formattedEdges = [];
    for (let i = 0; i < pipelineNodes.length - 1; i++) {
      formattedEdges.push({
        id: `e${pipelineNodes[i].id}-${pipelineNodes[i+1].id}`,
        source: pipelineNodes[i].id,
        target: pipelineNodes[i+1].id,
        animated: true,
        style: { stroke: '#94a3b8', strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#94a3b8' },
      });
    }

    setNodes(formattedNodes);
    setEdges(formattedEdges);
  }, [pipelineNodes, setNodes, setEdges]);

  const onConnectHandler = useCallback((params) => {
    setEdges((eds) => addEdge({ ...params, animated: true }, eds));
    if (onConnect) onConnect(params);
  }, [setEdges, onConnect]);

  const fitView = useCallback(() => {
    if (reactFlowWrapper.current) {
      reactFlowWrapper.current.fitView();
    }
  }, []);

  const zoomIn = useCallback(() => {
    if (reactFlowWrapper.current) {
      reactFlowWrapper.current.zoomIn();
    }
  }, []);

  const zoomOut = useCallback(() => {
    if (reactFlowWrapper.current) {
      reactFlowWrapper.current.zoomOut();
    }
  }, []);

  if (!pipelineNodes || pipelineNodes.length === 0) {
    return (
      <Paper elevation={0} sx={{ 
        width: '100%', 
        height: '400px', 
        borderRadius: 3, 
        border: '1px solid #e2e8f0', 
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: '#f8fafc'
      }}>
        <Box textAlign="center">
          <Typography variant="body1" color="text.secondary">
            No pipeline stages added yet
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Add stages from the left panel to build your pipeline
          </Typography>
        </Box>
      </Paper>
    );
  }

  return (
    <Paper elevation={0} sx={{ 
      width: '100%', 
      height: '450px', 
      borderRadius: 3, 
      border: '1px solid #e2e8f0', 
      overflow: 'hidden', 
      position: 'relative',
      bgcolor: '#f8fafc'
    }}>
      <Box sx={{ position: 'absolute', top: 10, right: 10, zIndex: 10, display: 'flex', gap: 1 }}>
        <Tooltip title="Zoom In">
          <IconButton size="small" onClick={zoomIn} sx={{ bgcolor: 'white', boxShadow: 1 }}>
            <ZoomIn />
          </IconButton>
        </Tooltip>
        <Tooltip title="Zoom Out">
          <IconButton size="small" onClick={zoomOut} sx={{ bgcolor: 'white', boxShadow: 1 }}>
            <ZoomOut />
          </IconButton>
        </Tooltip>
        <Tooltip title="Fit View">
          <IconButton size="small" onClick={fitView} sx={{ bgcolor: 'white', boxShadow: 1 }}>
            <FitScreen />
          </IconButton>
        </Tooltip>
      </Box>
      
      <ReactFlow
        ref={reactFlowWrapper}
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnectHandler}
        fitView
        attributionPosition="bottom-right"
        minZoom={0.5}
        maxZoom={2}
      >
        <Background variant="dots" gap={20} size={1} />
        <Controls showInteractive={false} />
        <MiniMap 
          nodeColor={(node) => node.style?.background || '#1976d2'}
          maskColor="rgba(0,0,0,0.1)"
        />
      </ReactFlow>
    </Paper>
  );
};

export default PipelineVisualizer;