import React from 'react';
import { View } from 'react-native';
import Svg, { Polygon, Line, Text as SvgText, Circle, G } from 'react-native-svg';
import { appChromeColors } from './theme';

interface RadarChartProps {
  data: {
    power: number;
    control: number;
    durability: number;
    comfort: number;
    sound: number;
  };
  size?: number;
}

export function AppRadarChart({ data, size = 320 }: RadarChartProps) {
  const centerX = size / 2;
  const centerY = size / 2;
  const radius = (size / 2) * 0.48; // Reduced further to ensure long labels like 'DURABILITY 8' have enough margin
  const levels = 5;
  const points = 5;
  const angleStep = (Math.PI * 2) / points;

  // Axis order: Power (top), Control, Durability, Comfort, Sound
  const axes = [
    { key: 'power', label: 'Power' },
    { key: 'control', label: 'Control' },
    { key: 'durability', label: 'Durability' },
    { key: 'comfort', label: 'Comfort' },
    { key: 'sound', label: 'Sound' },
  ];

  // Helper to get coordinates
  const getCoords = (index: number, value: number, maxRadius: number) => {
    const angle = index * angleStep - Math.PI / 2; // Start from top
    const r = (value / 10) * maxRadius;
    return {
      x: centerX + r * Math.cos(angle),
      y: centerY + r * Math.sin(angle),
    };
  };

  // 1. Background Grid (Pentagons)
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

  // 2. Data Polygon
  const dataPointsStr = axes
    .map((axis, i) => {
      const value = data[axis.key as keyof typeof data] || 0;
      const { x, y } = getCoords(i, value, radius);
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <View className="items-center justify-center py-2">
      <Svg width={size} height={size}>
        <G>
          {/* Grid Lines (Pentagons) */}
          {gridPolygons.map((points, i) => (
            <Polygon
              key={`grid-${i}`}
              points={points}
              fill="none"
              stroke="#E2E8F0"
              strokeWidth="1"
            />
          ))}

          {/* Axis Lines */}
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

          {/* Data Polygon */}
          <Polygon
            points={dataPointsStr}
            fill="rgba(37, 99, 235, 0.12)"
            stroke={appChromeColors.primary}
            strokeWidth="2"
          />

          {/* Data Points (Markers) */}
          {axes.map((axis, i) => {
            const value = data[axis.key as keyof typeof data] || 0;
            const { x, y } = getCoords(i, value, radius);
            return (
              <Circle
                key={`point-${i}`}
                cx={x}
                cy={y}
                r="3.5"
                fill={appChromeColors.primary}
                stroke="white"
                strokeWidth="1.5"
              />
            );
          })}

          {/* Labels with Scores */}
          {axes.map((axis, i) => {
            const value = data[axis.key as keyof typeof data] || 0;
            const { x, y } = getCoords(i, 11.5, radius); 
            const textAnchor = x > centerX + 15 ? 'start' : x < centerX - 15 ? 'end' : 'middle';
            
            // Refined dy positioning to prevent vertical overlap/cutoff
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
                letterSpacing="0"
              >
                {`${axis.label.toUpperCase()} ${value}`}
              </SvgText>
            );
          })}
        </G>
      </Svg>
    </View>
  );
}
