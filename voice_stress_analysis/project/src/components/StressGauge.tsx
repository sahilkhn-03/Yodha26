interface StressGaugeProps {
  score: number;
  level: 'Low' | 'Moderate' | 'High';
  size?: 'small' | 'large';
}

export function StressGauge({ score, level, size = 'large' }: StressGaugeProps) {
  const radius = size === 'large' ? 80 : 50;
  const strokeWidth = size === 'large' ? 12 : 8;
  const normalizedRadius = radius - strokeWidth / 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  const getColor = () => {
    if (level === 'Low') return '#6b7280';
    if (level === 'Moderate') return '#4b5563';
    return '#374151';
  };

  const getBackgroundColor = () => {
    if (level === 'Low') return '#f3f4f6';
    if (level === 'Moderate') return '#e5e7eb';
    return '#d1d5db';
  };

  const dimensions = size === 'large' ? 200 : 120;

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: dimensions, height: dimensions }}>
        <svg height={dimensions} width={dimensions} className="transform -rotate-90">
          <circle
            stroke={getBackgroundColor()}
            fill="transparent"
            strokeWidth={strokeWidth}
            r={normalizedRadius}
            cx={dimensions / 2}
            cy={dimensions / 2}
          />
          <circle
            stroke={getColor()}
            fill="transparent"
            strokeWidth={strokeWidth}
            strokeDasharray={circumference + ' ' + circumference}
            style={{
              strokeDashoffset,
              transition: 'stroke-dashoffset 0.5s ease'
            }}
            strokeLinecap="round"
            r={normalizedRadius}
            cx={dimensions / 2}
            cy={dimensions / 2}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className={`${size === 'large' ? 'text-4xl' : 'text-2xl'} font-bold`} style={{ color: getColor() }}>
            {score}
          </div>
          <div className={`${size === 'large' ? 'text-sm' : 'text-xs'} text-gray-500 font-medium`}>
            / 100
          </div>
        </div>
      </div>
      <div
        className={`mt-3 px-4 py-1.5 rounded-full text-sm font-semibold`}
        style={{
          backgroundColor: getBackgroundColor(),
          color: getColor()
        }}
      >
        {level} Stress
      </div>
    </div>
  );
}
