import { useRef, useEffect } from 'react';
import { useTheme } from '@mui/material/styles';
import { Card, CardContent, CardHeader, Box, Divider } from '@mui/material';
import Chart from 'chart.js/auto';

interface PieChartProps {
  title: string;
  labels: string[];
  data: number[];
  colors?: string[];
  height?: number;
}

const PieChart = ({ 
  title, 
  labels, 
  data, 
  colors, 
  height = 300 
}: PieChartProps) => {
  const theme = useTheme();
  const chartRef = useRef<HTMLCanvasElement>(null);
  const chartInstance = useRef<Chart | null>(null);
  
  const defaultColors = [
    theme.palette.primary.main,
    theme.palette.secondary.main,
    theme.palette.tertiary.main,
    theme.palette.success.main,
    theme.palette.warning.main,
    theme.palette.error.main,
  ];
  
  const chartColors = colors || defaultColors;

  useEffect(() => {
    if (chartRef.current) {
      // Destroy previous chart instance if it exists
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
      
      const ctx = chartRef.current.getContext('2d');
      
      if (ctx) {
        chartInstance.current = new Chart(ctx, {
          type: 'doughnut',
          data: {
            labels,
            datasets: [
              {
                data,
                backgroundColor: chartColors,
                borderColor: theme.palette.background.paper,
                borderWidth: 2,
                hoverOffset: 10,
              },
            ],
          },
          options: {
            cutout: '60%',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'bottom',
                labels: {
                  usePointStyle: true,
                  padding: 20,
                  font: {
                    family: theme.typography.fontFamily,
                    size: 11,
                  },
                  color: theme.palette.text.primary,
                },
              },
              tooltip: {
                enabled: true,
                backgroundColor: theme.palette.mode === 'dark' 
                  ? 'rgba(0, 0, 0, 0.75)' 
                  : 'rgba(255, 255, 255, 0.9)',
                titleColor: theme.palette.text.primary,
                bodyColor: theme.palette.text.secondary,
                borderColor: theme.palette.divider,
                borderWidth: 1,
                padding: 12,
                boxPadding: 4,
                usePointStyle: true,
                callbacks: {
                  label: function(context) {
                    const value = context.raw as number;
                    const total = context.dataset.data.reduce(
                      (acc: number, data: number) => acc + data, 0
                    );
                    const percentage = Math.round((value / total) * 100);
                    return `${context.label}: ${value} (${percentage}%)`;
                  }
                }
              },
            },
            animation: {
              animateRotate: true,
              animateScale: true,
              duration: 1000,
              easing: 'easeOutQuart',
            },
          },
        });
      }
    }
    
    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [labels, data, chartColors, theme]);

  return (
    <Card sx={{ height: '100%' }}>
      <CardHeader 
        title={title} 
        titleTypographyProps={{ 
          variant: 'h6', 
          fontWeight: 600,
          fontSize: '1rem' 
        }} 
      />
      <Divider />
      <CardContent>
        <Box
          sx={{
            height,
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <canvas ref={chartRef} />
        </Box>
      </CardContent>
    </Card>
  );
};

export default PieChart;