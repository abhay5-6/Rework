"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import dynamic from "next/dynamic";
import type { ForceGraphMethods, NodeObject } from "react-force-graph-2d";
import { Loader2 } from "lucide-react";
import api from "@/lib/api/client";

// Dynamically import react-force-graph-2d to avoid SSR issues
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
  loading: () => (
    <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
      <Loader2 className="animate-spin mb-4" size={32} />
      <p>Loading physics engine...</p>
    </div>
  ),
});

type GraphApiNode = {
  id: string;
  type: string;
  data: {
    label: string;
    domain?: string;
    importance?: number;
  };
};

type GraphApiEdge = {
  source: string;
  target: string;
  label?: string;
};

type GraphNode = {
  id: string;
  name: string;
  domain?: string;
  val: number;
  type: string;
  x?: number;
  y?: number;
};

type GraphLink = {
  source: string;
  target: string;
  label?: string;
};

export default function CognitiveGraph({ roomId }: { roomId: number }) {
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; links: GraphLink[] }>({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fgRef = useRef<ForceGraphMethods | undefined>(undefined);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  useEffect(() => {
    async function loadGraph() {
      try {
        setError(null);
        const res = await api.get(`/ai/graph/${roomId}`);
        
        const data = res.data as { nodes: GraphApiNode[]; edges: GraphApiEdge[] };

        // Format data for react-force-graph
        const nodes = data.nodes.map((node) => ({
          id: node.id,
          name: node.data.label,
          domain: node.data.domain,
          val: (node.data.importance ?? 1) * 2, // Scale up for visual weight
          type: node.type
        }));

        const links = data.edges.map((edge) => ({
          source: edge.source,
          target: edge.target,
          label: edge.label,
        }));

        setGraphData({ nodes, links });
      } catch (err: unknown) {
        console.error("GRAPH LOAD ERROR", err);
        setError("AI Knowledge Graph is currently offline or disabled.");

      } finally {
        setLoading(false);
      }
    }

    loadGraph();
  }, [roomId]);


  // Handle responsive resizing
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight
        });
      }
    };
    
    // Initial size
    handleResize();
    
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Custom node painting
  const paintNode = useCallback((node: NodeObject, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const graphNode = node as NodeObject & Partial<GraphNode>;
    const label = graphNode.name ?? String(graphNode.id ?? "");
    const fontSize = 12 / globalScale;
    ctx.font = `${fontSize}px Inter, sans-serif`;
    
    // Determine color based on domain
    let color = "#525252"; // default neutral
    const domain = graphNode.domain?.toLowerCase() || "";
    if (domain.includes("architecture")) color = "#06b6d4"; // cyan
    else if (domain.includes("backend")) color = "#a855f7"; // purple
    else if (domain.includes("frontend")) color = "#f97316"; // orange
    else if (domain.includes("database")) color = "#10b981"; // emerald

    // Draw node circle
    const r = Math.sqrt(Math.max(0, graphNode.val || 1)) * 4;
    ctx.beginPath();
    ctx.arc(graphNode.x ?? 0, graphNode.y ?? 0, r, 0, 2 * Math.PI, false);
    ctx.fillStyle = color;
    ctx.fill();
    
    // Draw subtle glow
    ctx.shadowColor = color;
    ctx.shadowBlur = 10;
    ctx.fill();
    ctx.shadowBlur = 0; // reset

    // Draw text label
    const textWidth = ctx.measureText(label).width;
    const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2); 
    
    ctx.fillStyle = "rgba(0, 0, 0, 0.8)";
    ctx.fillRect((graphNode.x ?? 0) - bckgDimensions[0] / 2, (graphNode.y ?? 0) + r + 2, bckgDimensions[0], bckgDimensions[1]);
    
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillStyle = "#ffffff";
    ctx.fillText(label, graphNode.x ?? 0, (graphNode.y ?? 0) + r + 2 + bckgDimensions[1] / 2);
  }, []);

  if (loading) {
    return (
      <div className="h-[800px] rounded-3xl border border-border bg-background flex flex-col items-center justify-center text-muted-foreground shadow-2xl">
        <Loader2 className="animate-spin mb-4" size={32} />
        <p>Analyzing AI memory vault...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-[300px] rounded-3xl overflow-hidden border border-border bg-background/50 backdrop-blur flex flex-col items-center justify-center p-6 text-center">
        <div className="w-12 h-12 rounded-full bg-amber-500/10 text-amber-500 flex items-center justify-center mb-3">
          <Loader2 size={24} className="opacity-50" />
        </div>
        <h3 className="font-semibold text-foreground mb-1">AI Assistant Offline</h3>
        <p className="text-sm text-muted-foreground max-w-md">{error}</p>
      </div>
    );
  }


  return (

    <div 
      ref={containerRef}
      className="w-full h-[800px] rounded-3xl overflow-hidden border border-border bg-background shadow-2xl relative"
    >
      <div className="absolute top-4 left-4 z-10 pointer-events-none">
        <h2 className="text-foreground font-bold text-lg mb-1 flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          Neural Context Graph
        </h2>
        <p className="text-muted-foreground text-xs uppercase tracking-widest font-mono">
          {graphData.nodes.length} Nodes • {graphData.links.length} Synapses
        </p>
      </div>
      
      <div className="absolute bottom-4 left-4 z-10 flex gap-4 text-[10px] uppercase font-mono tracking-wider pointer-events-none">
        <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-[#06b6d4]" /> Architecture</div>
        <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-[#a855f7]" /> Backend</div>
        <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-[#f97316]" /> Frontend</div>
        <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-[#10b981]" /> Database</div>
      </div>

      <ForceGraph2D
        ref={fgRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={graphData}
        nodeLabel={() => ""} // Custom label drawing in paintNode
        nodeCanvasObject={paintNode}
        nodeCanvasObjectMode={() => "replace"}
        linkColor={() => "rgba(255, 255, 255, 0.1)"}
        linkWidth={1.5}
        linkDirectionalParticles={2}
        linkDirectionalParticleWidth={1.5}
        linkDirectionalParticleSpeed={0.005}
        backgroundColor="#000000"
        onEngineStop={() => {
          if (fgRef.current) {
            fgRef.current.zoomToFit(400, 50);
          }
        }}
      />
    </div>
  );
}
