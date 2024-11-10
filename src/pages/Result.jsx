import React from 'react';

const ResultBox = ({ tripPlan }) => {
  // Simple check for whether the tripPlan is available
  if (!tripPlan) {
    return <div>Loading trip plan...</div>;  // or handle the absence of tripPlan in a different way
  }

  return (
    <div className="result-box">
      <h2>Your Trip Plan</h2>
      {/* Use dangerouslySetInnerHTML to inject HTML content */}
      <div dangerouslySetInnerHTML={{ __html: tripPlan }} />
    </div>
  );
};

export default ResultBox;
