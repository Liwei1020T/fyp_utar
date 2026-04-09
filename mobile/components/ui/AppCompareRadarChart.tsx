import React from 'react';
import { View } from 'react-native';
import Svg, { Polygon, Line, Text as SvgText, Circle, G } from 'react-native-svg';

interface RadarData {
  power: number;
  control: number;
  durability: number;
  comfort: number;
  sound: number;
}

interface AppCompareRadarChartProps {
  dataA: RadarData;
  dataB: RadarData;
  labelA: string;
  labelB: string;
  size?: number;
}

export function AppCompareRadarChart({ dataA, dataB, size = 320 }: AppCompareRadarChartProps) {
  const centerX = size / 2;
  const centerY = size / 2;
  const radius = (size / 2) * 0.48;
  const levels = 5;
  const points = 5;
  const angleStep = (Math.PI * 2) / points;

  const axes = [
    { key: 'power', label: 'Power' },
    { key: 'control', label: 'Control' },
    { key: 'durability', label: 'Durability' },
    { key: 'comfort', label: 'Comfort' },
    { key: 'sound', label: 'Sound' },
  ];

  const getCoords = (index: number, value: number, maxRadius: number) => {
    const angle = index * angleStep - Math.PI / 2;
    const r = (value / 10) * maxRadius;
    return {
      x: centerX + r * Math.cos(angle),
      y: centerY + r * Math.sin(angle),
    };
  };

  const gridPolygons = [];
  for (let i = 1; i <= levels; i++) {
    const levelRadius = (radius / levels) * i;
    const pointsStr = Array.from({ length: points })
      .map((_, j) => {
        const { x, y } = getCoords(j, 10, levelRadius);
        return `${x},${y}`;
      })
      .join(' ');
    gridPolygons.push(pointsStr);
  }

  const dataPointsA = axes
    .map((axis, i) => {
      const value = dataA[axis.key as keyof RadarData] || 0;
      const { x, y } = getCoords(i, value, radius);
      return `${x},${y}`;
    })
    .join(' ');

  const dataPointsB = axes
    .map((axis, i) => {
      const value = dataB[axis.key as keyof RadarData] || 0;
      const { x, y } = getCoords(i, value, radius);
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <View className="items-center justify-center py-2">
      <Svg width={size} height={size}>
        <G>
          {gridPolygons.map((points, i) => (
            <Polygon
              key={`grid-${i}`}
              points={points}
              fill="none"
              stroke="#E2E8F0"
              strokeWidth="1"
            />
          ))}

          {axes.map((_, i) => {
            const { x, y } = getCoords(i, 10, radius);
            return (
              <Line
                key={`axis-${i}`}
                x1={centerX}
                y1={centerY}
                x2={x}
                y2={y}
                stroke="#E2E8F0"
                strokeWidth="1"
              />
            );
          })}

          {/* String B - Secondary */}
          <Polygon
            points={dataPointsB}
            fill="rgba(100, 116, 139, 0.1)"
            stroke="#64748B"
            strokeWidth="2"
            strokeDasharray="4,4"
          />

          {/* String A - Primary */}
          <Polygon
            points={dataPointsA}
            fill="rgba(59, 130, 246, 0.12)"
            stroke="#3B82F6"
            strokeWidth="2"
          />

          {axes.map((axis, i) => {
            const { x, y } = getCoords(i, 11.5, radius);
            const textAnchor = x > centerX + 15 ? 'start' : x < centerX - 15 ? 'end' : 'middle';
            const dy = y < centerY - 20 ? -12 : y > centerY + 20 ? 22 : 5;

            return (
              <SvgText
                key={`label-${i}`}
                x={x}
                y={y}
                dy={dy}
                fill="#64748B"
                fontSize="10"
                fontWeight="bold"
                textAnchor={textAnchor}
                letterSpacing="0.05em"
              >
                {axis.label.toUpperCase()}
              </SvgText>
            );
          })}
        </G>
      </Svg>
    </View>
  );
}
