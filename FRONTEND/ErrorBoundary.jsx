// components/ErrorBoundary.jsx

import React from "react";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Error caught by boundary:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="p-4 text-red-500">
            <h2>Something went wrong.</h2>
            <p>{this.state.error && this.state.error.toString()}</p>
            <button
              onClick={() => this.setState({ hasError: false })}
              className="mt-2 bg-blue-500 text-white px-4 py-2 rounded"
            >
              Try again
            </button>
          </div>
        )
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
