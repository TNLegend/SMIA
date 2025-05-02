import { useRef, useEffect } from 'react';
import { useTheme } from '@mui/material/styles';
import { Card, CardContent, CardHeader, Box, Divider } from '@mui/material';
import Chart from 'chart.js/auto';

interface LineChartProps {
  title: string;
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    color?: string;
  }[];
  height?: number;
}

const LineChart = ({ 
  title, 
  labels, 
  datasets, 
  height = 300 
}: LineChartProps) => {
  const theme = useTheme();
  const chartRef = useRef<HTMLCanvasElement>(null);
  const chartInstance = useRef<Chart | null>(null);
  
  const defaultColors = [
    theme.palette.primary.main,
    theme.palette.secondary.main,
    theme.palette.tertiary.main,
    theme.palette.success.main,
    theme.palette.warning.main,
  ];

  useEffect(() => {
    if (chartRef.current) {
      // Destroy previous chart instance if it exists
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
      
      const ctx = chartRef.current.getContext('2d');
      
      if (ctx) {
        chartInstance.current = new Chart(ctx, {
          type: 'line',
          data: {
            labels,
            datasets: datasets.map((dataset, index) => ({
              label: dataset.label,
              data: dataset.data,
              borderColor: dataset.color || defaultColors[index % defaultColors.length],
              backgroundColor: theme.palette.mode === 'dark'
                ? `${dataset.color || defaultColors[index % defaultColors.length]}33`
                : `${dataset.color || defaultColors[index % defaultColors.length]}15`,
              fill: true,
              tension: 0.4,
              borderWidth: 2,
              pointRadius: 3,
              pointHoverRadius: 5,
              pointBackgroundColor: dataset.color || defaultColors[index % defaultColors.length],
              pointHoverBackgroundColor: theme.palette.background.paper,
              pointBorderColor: dataset.color || defaultColors[index % defaultColors.length],
              pointHoverBorderColor: dataset.color || defaultColors[index % defaultColors.length],
              pointBorderWidth: 2,
              pointHoverBorderWidth: 2,
            })),
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              x: {
                grid: {
                  display: false,
                  drawBorder: false,
                },
                ticks: {
                  color: theme.palette.text.secondary,
                  font: {
                    size: 10,
                  },
                },
              },
              y: {
                grid: {
                  color: theme.palette.divider,
                  drawBorder: false,
                },
                ticks: {
                  color: theme.palette.text.secondary,
                  font: {
                    size: 10,
                  },
                  callback: function(value) {
                    return value;
                  }
                },
              },
            },
            plugins: {
              legend: {
                position: 'top',
                align: 'end',
                labels: {
                  usePointStyle: true,
                  boxWidth: 6,
                  boxHeight: 6,
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
              },
            },
            animation: {
              duration: 1000,
              easing: 'easeOutQuart',
            },
            interaction: {
              mode: 'index',
              intersect: false,
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
  }, [labels, datasets, theme]);

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
          }}
        >
          <canvas ref={chartRef} />
        </Box>
      </CardContent>
    </Card>
  );
};

export default LineChart;