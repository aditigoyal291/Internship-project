import React, { useState, useEffect } from "react";
import { Search } from "lucide-react";
import GraphVisualization from "./GraphVisualization"; // Import the component

const PinSearchForm = () => {
  const [pinCode, setPinCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);

  // Function to handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!pinCode.trim()) {
      setError("Please enter a valid PIN code");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Connect to your PIN search API endpoint
      const response = await fetch(
        `http://localhost:5000/api/graph/pin/${pinCode}`
      );

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("No people found in this PIN code");
        }
        throw new Error("Failed to fetch data");
      }

      const data = await response.json();

      // Ensure we have nodes
      if (!data.nodes || data.nodes.length === 0) {
        throw new Error("No people found in this PIN code");
      }

      console.log("Graph data received:", data);

      // Initialize positions for nodes with good spacing
      const width = 600;
      const height = 500;
      const centerX = width / 2;
      const centerY = height / 2;
      const radius = Math.min(width, height) * 0.4;

      // Arrange nodes in a circle for initial layout
      data.nodes = data.nodes.map((node, index) => {
        const angle = (index / data.nodes.length) * 2 * Math.PI;
        return {
          ...node,
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle),
          vx: 0,
          vy: 0,
        };
      });

      setGraphData(data);
      setSelectedNode(null);
    } catch (err) {
      console.error("Error fetching data:", err);
      setError(err.message || "An error occurred while fetching data");
      setGraphData(null);
    } finally {
      setLoading(false);
    }
  };

  // Function to handle node selection
  const handleNodeSelect = (node) => {
    setSelectedNode(node);
  };

  return (
    <div className="flex h-screen w-full overflow-hidden">
      {/* Main graph area */}
      <div className="flex-1 relative">
        <div className="absolute top-0 left-0 right-0 p-4 z-10">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <div className="relative flex-grow">
              <input
                type="text"
                value={pinCode}
                onChange={(e) => setPinCode(e.target.value)}
                placeholder="Enter PIN Code"
                className="w-full p-2 pl-10 border rounded-md"
                maxLength="6"
              />
              <Search
                className="absolute left-3 top-2.5 text-gray-400"
                size={18}
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-blue-300"
            >
              {loading ? "Loading..." : "Search"}
            </button>
          </form>
        </div>

        {error && (
          <div className="absolute top-16 left-0 right-0 p-4 z-10">
            <div
              className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative"
              role="alert"
            >
              {error}
            </div>
          </div>
        )}

        <div className="w-full h-full">
          {graphData && (
            <GraphVisualization
              nodes={graphData.nodes}
              relationships={[]} // No relationships for PIN search
              onNodeSelect={handleNodeSelect}
              selectedNode={selectedNode}
            />
          )}
        </div>
      </div>

      {/* Sidebar for node details */}
      {selectedNode && (
        <div className="w-80 h-full bg-gray-800 overflow-y-auto">
          <NodeDetails
            node={selectedNode}
            onClose={() => setSelectedNode(null)}
            graphData={graphData}
          />
        </div>
      )}
    </div>
  );
};

export default PinSearchForm;
