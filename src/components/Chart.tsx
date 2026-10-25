import React from 'react';

interface ChartProps {
  values: number[];
  color?: string;
  label?: string;
  startLabel?: string;
  endLabel?: string;
}

export const Chart: React.FC<ChartProps> = ({
  values,
  color = '#48815a',
  label = 'Observed values',
  startLabel = '',
  endLabel = '',
}) => {
  if (!values.length) {
    return (
      <div className="empty-state">
        <span className="empty-icon">⌁</span>
        <strong>No records available</strong>
        <p>No observations are available to plot.</p>
      </div>
    );
  }

  const width = 700;
  const height = 205;
  const left = 34;
  const right = 12;
  const top = 12;
  const bottom = 30;

  const numbers = values.map((val) => Number(val) || 0);
  const min = Math.min(...numbers);
  const max = Math.max(...numbers);
  const span = Math.max(max - min, 1);

  const points: [number, number][] = numbers.map((value, index) => {
    const x = left + (index * (width - left - right)) / Math.max(numbers.length - 1, 1);
    const y = top + ((max - value) * (height - top - bottom)) / span;
    return [x, y];
  });

  const line = points
    .map(([x, y], index) => `${index ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`)
    .join(' ');

  const lastPoint = points[points.length - 1];
  const firstPoint = points[0];
  const area = `${line} L${lastPoint[0]},${height - bottom} L${firstPoint[0]},${height - bottom} Z`;

  const guide = [0, 1, 2, 3].map((i) => {
    const y = top + (i * (height - top - bottom)) / 3;
    return (
      <line
        key={i}
        className="chart-grid"
        x1={left}
        y1={y}
        x2={width - right}
        y2={y}
      />
    );
  });

  return (
    <div className="chart-wrap">
      <svg
        className="chart"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={label}
      >
        <defs>
          <linearGradient id="chartGradient" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0" stopColor={color} stopOpacity="0.20" />
            <stop offset="1" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        {guide}
        <path className="chart-fill" d={area} />
        <path className="chart-line" stroke={color} d={line} />
        {startLabel && (
          <text className="chart-label" x={left} y={height - 8}>
            {startLabel}
          </text>
        )}
        {endLabel && (
          <text className="chart-label" textAnchor="end" x={width - right} y={height - 8}>
            {endLabel}
          </text>
        )}
      </svg>
    </div>
  );
};
