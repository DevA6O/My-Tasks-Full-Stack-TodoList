import React from "react";

export default function LoadingScreen() {
  return (
    <div className="h-screen flex flex-col justify-center items-center bg-gray-100 text-gray-700">
      <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-blue-500 border-solid mb-4"></div>
      <p data-testid="loading-text" className="text-lg font-medium">Loading...</p>
    </div>
  );
}