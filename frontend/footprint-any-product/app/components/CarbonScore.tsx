import React, { useEffect, useState } from 'react';
import { CarbonScoreProps } from '../types';

const CarbonScore: React.FC<CarbonScoreProps> = ({ 
  score, 
  size = 'md', 
  showText = true,
  animated = true
}) => {
  const [displayScore, setDisplayScore] = useState(0);
  
  useEffect(() => {
    if (animated) {
      const timer = setTimeout(() => {
        setDisplayScore(score);
      }, 300);
      return () => clearTimeout(timer);
    } else {
      setDisplayScore(score);
    }
  }, [score, animated]);
  
  // Get color based on score
  const getColor = () => {
    if (score <= 0) return 'var(--score-neutral)';
    if (score < 40) return 'var(--score-good)';
    if (score < 60) return 'var(--score-fair)';
    return 'var(--score-poor)';
  };
  
  // Get text based on score
  const getText = () => {
    if (score <= 0) return 'Not evaluated';
    if (score < 40) return 'Low impact';
    if (score < 60) return 'Medium impact';
    return 'High impact';
  };
  
  // Get size class
  const getSizeClass = () => {
    switch (size) {
      case 'sm': return 'h-1.5 text-xs';
      case 'lg': return 'h-4 text-base';
      default: return 'h-2 text-sm';
    }
  };
  
  return (
    <div className="w-full">
      <div className="carbon-meter" style={{ height: size === 'sm' ? '6px' : size === 'lg' ? '12px' : '8px' }}>
        <div 
          className="carbon-meter-fill"
          style={{ 
            backgroundColor: getColor(),
            width: `${displayScore}%`
          }}
        />
      </div>
      
      {showText && (
        <div className="flex justify-between mt-1">
          <div className={`font-medium ${getSizeClass()}`} style={{ color: getColor() }}>
            {score > 0 ? score : '-'}/100
          </div>
          <div className={`${getSizeClass()} opacity-70`}>
            {getText()}
          </div>
        </div>
      )}
    </div>
  );
};

export default CarbonScore;